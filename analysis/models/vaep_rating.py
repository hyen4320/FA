"""VAEP 선수 레이팅 — 교차검증(OOF) + 상대 수준별 분해.

xT보다 정교한 행동가치 모델. 모든 온볼 행동에 대해 "다음 N행동 안 득점확률↑(공격)
+ 실점확률↓(수비)"를 추정해 합산. 수비·빌드업 기여까지 가치화.

이전 버전의 낙관 편향(학습=예측)을 **GroupKFold 교차검증**으로 제거한다:
경기 단위로 폴드를 나눠, 각 행동의 VAEP를 '그 경기를 안 본 모델'로 예측(OOF).
→ 선수 랭킹이 과적합 없이 정직해진다.

추가로 **상대 수준별 VAEP/90**(강/중/약)을 분해한다. 분데스리가 23/24 최종
순위표(외부 사실)로 상대를 티어링 — 우리 데이터로 식별 불가한 동료·리그 효과와
달리, 외부 순위표를 쓰면 '상대 맥락'은 정직하게 계산 가능.

산출물:
  data/vaep_rating.csv          선수별 OOF VAEP/90
  data/vaep_by_tier.csv         선수×상대티어 VAEP/90
  data/vaep_metrics.json        교차검증 성능(train vs test)

실행:
    PYTHONUTF8=1 .venv/Scripts/python.exe analysis/models/vaep_rating.py
"""

import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import xgboost
from sklearn.model_selection import GroupKFold
from sklearn.metrics import log_loss, brier_score_loss
import socceraction.spadl as spadl
import socceraction.vaep.features as fs
import socceraction.vaep.labels as lab
import socceraction.vaep.formula as vaepformula
from socceraction.data.statsbomb import StatsBombLoader

warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import xt_core  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
COMPETITION_ID, SEASON_ID = 9, 281
NB_PREV = 3
N_SPLITS = 5
THE_TEAM = "Bayer Leverkusen"

# 분데스리가 2023/24 최종 순위 기반 상대 티어 (외부 사실)
TIER = {
    "Bayer Leverkusen": "강", "VfB Stuttgart": "강", "Bayern Munich": "강",
    "RB Leipzig": "강", "Borussia Dortmund": "강",
    "Eintracht Frankfurt": "중", "Hoffenheim": "중", "FC Heidenheim": "중",
    "Werder Bremen": "중", "Freiburg": "중", "Augsburg": "중", "Wolfsburg": "중",
    "FSV Mainz 05": "약", "Borussia Mönchengladbach": "약", "Union Berlin": "약",
    "Bochum": "약", "FC Köln": "약", "Darmstadt 98": "약",
}

XFNS = [fs.actiontype_onehot, fs.bodypart_onehot, fs.result_onehot, fs.goalscore,
        fs.startlocation, fs.endlocation, fs.movement, fs.space_delta,
        fs.startpolar, fs.endpolar, fs.team, fs.time_delta]
YFNS = [lab.scores, lab.concedes]


def opponent_of(match_row) -> str:
    h, a = match_row["home_team"], match_row["away_team"]
    return a if h == THE_TEAM else h


def main() -> None:
    import duckdb
    con = duckdb.connect(str(xt_core.DB_PATH), read_only=True)
    matches = con.execute("SELECT match_id, home_team, away_team FROM matches").df()
    con.close()
    opp_by_game = {int(r.match_id): opponent_of(r._asdict()) for r in matches.itertuples(index=False)}

    loader = StatsBombLoader(getter="remote", creds={"user": "", "passwd": ""})
    games = loader.games(COMPETITION_ID, SEASON_ID)
    print(f"경기 {len(games)}개 — SPADL 변환 + 피처/라벨 생성...")

    X_list, Y_list, A_list, groups = [], [], [], []
    players_map = {}           # player_id -> name
    mins_total, mins_tier = {}, {}  # 출전시간 합 / 티어별

    for i, g in enumerate(games.itertuples(index=False)):
        gid, home = int(g.game_id), g.home_team_id
        try:
            events = loader.events(gid)
            actions = spadl.add_names(spadl.statsbomb.convert_to_actions(events, home))
            gs = fs.play_left_to_right(fs.gamestates(actions, NB_PREV), home)
            X = pd.concat([fn(gs) for fn in XFNS], axis=1).reset_index(drop=True)
            Y = pd.concat([fn(actions) for fn in YFNS], axis=1).reset_index(drop=True)
            actions = actions.reset_index(drop=True)
            actions["game_id"] = gid
            X_list.append(X); Y_list.append(Y); A_list.append(actions)
            groups.extend([gid] * len(actions))

            tier = TIER.get(opp_by_game.get(gid, ""), "중")
            for p in loader.players(gid).itertuples(index=False):
                players_map[p.player_id] = p.player_name
                mins_total[p.player_id] = mins_total.get(p.player_id, 0) + p.minutes_played
                key = (p.player_id, tier)
                mins_tier[key] = mins_tier.get(key, 0) + p.minutes_played
        except Exception as e:
            print(f"  [{i+1}/{len(games)}] game {gid} 실패: {e}")
            continue
    print(f"  완료. 행동 {sum(len(a) for a in A_list):,}개")

    X = pd.concat(X_list, ignore_index=True)
    Y = pd.concat(Y_list, ignore_index=True)
    A = pd.concat(A_list, ignore_index=True)
    groups = np.array(groups)

    # ---- GroupKFold 교차검증: OOF 예측 + 성능 측정 ----
    print(f"\nGroupKFold({N_SPLITS}) 교차검증 (경기 단위 분리)...")
    oof = {"scores": np.zeros(len(A)), "concedes": np.zeros(len(A))}
    metrics = {}
    gkf = GroupKFold(n_splits=N_SPLITS)
    for col in ["scores", "concedes"]:
        tr_ll, te_ll, te_br = [], [], []
        for tr, te in gkf.split(X, Y[col], groups):
            m = xgboost.XGBClassifier(n_estimators=100, max_depth=5, learning_rate=0.1,
                                      n_jobs=-1, eval_metric="logloss", verbosity=0)
            m.fit(X.iloc[tr], Y[col].iloc[tr])
            oof[col][te] = m.predict_proba(X.iloc[te])[:, 1]
            tr_ll.append(log_loss(Y[col].iloc[tr], m.predict_proba(X.iloc[tr])[:, 1], labels=[0, 1]))
            te_ll.append(log_loss(Y[col].iloc[te], oof[col][te], labels=[0, 1]))
            te_br.append(brier_score_loss(Y[col].iloc[te], oof[col][te]))
        metrics[col] = {"train_logloss": round(float(np.mean(tr_ll)), 5),
                        "test_logloss": round(float(np.mean(te_ll)), 5),
                        "test_brier": round(float(np.mean(te_br)), 5)}
        print(f"  {col}: train logloss {metrics[col]['train_logloss']} | "
              f"test {metrics[col]['test_logloss']} | brier {metrics[col]['test_brier']}")

    # ---- OOF 예측으로 VAEP 계산 (정직한 값) ----
    values = vaepformula.value(A, pd.Series(oof["scores"]), pd.Series(oof["concedes"]))
    A = A.join(values)
    A["tier"] = A["game_id"].map(lambda gid: TIER.get(opp_by_game.get(int(gid), ""), "중"))

    # 선수별 합산
    agg = A.groupby("player_id")["vaep_value"].agg(vaep_total="sum", actions="count").reset_index()
    agg["player"] = agg["player_id"].map(players_map)
    agg["minutes"] = agg["player_id"].map(lambda p: mins_total.get(p, 0))
    agg = agg[agg["minutes"] >= 450].copy()
    agg["vaep_p90"] = agg["vaep_total"] / agg["minutes"] * 90
    agg = agg.sort_values("vaep_p90", ascending=False)

    # 선수×티어 합산
    tier_rows = []
    for (pid, tier), g in A.groupby(["player_id", "tier"]):
        mins = mins_tier.get((pid, tier), 0)
        if mins < 90:
            continue
        tier_rows.append({"player_id": pid, "player": players_map.get(pid),
                          "tier": tier, "minutes": int(mins),
                          "vaep_p90": round(g["vaep_value"].sum() / mins * 90, 4)})
    tier_df = pd.DataFrame(tier_rows)

    DATA_DIR.mkdir(exist_ok=True)
    agg.to_csv(DATA_DIR / "vaep_rating.csv", index=False, encoding="utf-8-sig")
    tier_df.to_csv(DATA_DIR / "vaep_by_tier.csv", index=False, encoding="utf-8-sig")
    (DATA_DIR / "vaep_metrics.json").write_text(
        json.dumps({"cv": metrics, "n_splits": N_SPLITS, "n_actions": int(len(A)),
                    "method": "GroupKFold by match, out-of-fold VAEP"},
                   ensure_ascii=False, indent=2), encoding="utf-8")

    print("\nVAEP 레이팅 (OOF) — 90분당 상위 12:")
    print(f"  {'선수':<26}{'VAEP/90':>9}{'분':>7}")
    for r in agg.head(12).itertuples(index=False):
        print(f"  {r.player:<26}{r.vaep_p90:>9.3f}{int(r.minutes):>7}")
    print(f"\n저장 → vaep_rating.csv · vaep_by_tier.csv · vaep_metrics.json")


if __name__ == "__main__":
    main()
