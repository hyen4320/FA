"""VAEP (Valuing Actions by Estimating Probabilities) 선수 레이팅.

xT보다 정교한 행동가치 모델. 모든 온볼 행동(패스·드리블·슛·태클·인터셉트 등)에
대해 "이 행동이 다음 N행동 안에 우리 팀 득점 확률을 얼마나 올렸나(공격가치) +
실점 확률을 얼마나 줄였나(수비가치)"를 머신러닝으로 추정해 합산한다.
xT가 못 잡던 '수비 기여'까지 가치화하는 게 핵심.

파이프라인 (socceraction 표준):
  StatsBomb 이벤트 → SPADL 행동 변환 → 피처/라벨 생성
  → XGBoost 2개(득점확률·실점확률) 학습 → 행동별 VAEP → 선수 합산

주의: 첫 버전이라 학습/예측을 같은 데이터로 한다(낙관 편향 존재). 선수 랭킹
데모 목적엔 충분하지만, 본격 모델은 train/test 분리 필요.

실행:
    PYTHONUTF8=1 .venv/Scripts/python.exe analysis/models/vaep_rating.py
"""

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import xgboost
import socceraction.spadl as spadl
import socceraction.vaep.features as fs
import socceraction.vaep.labels as lab
import socceraction.vaep.formula as vaepformula
from socceraction.data.statsbomb import StatsBombLoader

warnings.filterwarnings("ignore")
sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
OUT_CSV = DATA_DIR / "vaep_rating.csv"

COMPETITION_ID = 9
SEASON_ID = 281
NB_PREV = 3  # gamestate에 포함할 이전 행동 수

XFNS = [
    fs.actiontype_onehot, fs.bodypart_onehot, fs.result_onehot,
    fs.goalscore, fs.startlocation, fs.endlocation, fs.movement,
    fs.space_delta, fs.startpolar, fs.endpolar, fs.team, fs.time_delta,
]
YFNS = [lab.scores, lab.concedes]


def main() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    loader = StatsBombLoader(getter="remote", creds={"user": "", "passwd": ""})
    games = loader.games(COMPETITION_ID, SEASON_ID)
    print(f"경기 {len(games)}개 처리 시작 (SPADL 변환 + 피처 생성)...")

    X_list, Y_list, A_list = [], [], []
    players_map = {}  # player_id -> (name, minutes 합)

    for i, g in enumerate(games.itertuples(index=False)):
        gid, home = g.game_id, g.home_team_id
        try:
            events = loader.events(gid)
            actions = spadl.statsbomb.convert_to_actions(events, home)
            actions = spadl.add_names(actions)

            gs = fs.gamestates(actions, NB_PREV)
            gs = fs.play_left_to_right(gs, home)
            X = pd.concat([fn(gs) for fn in XFNS], axis=1)
            Y = pd.concat([fn(actions) for fn in YFNS], axis=1)

            X_list.append(X.reset_index(drop=True))
            Y_list.append(Y.reset_index(drop=True))
            A_list.append(actions.reset_index(drop=True))

            # 출전 시간 누적 (per-90 계산용)
            pl = loader.players(gid)
            for p in pl.itertuples(index=False):
                name, mins = players_map.get(p.player_id, (p.player_name, 0))
                players_map[p.player_id] = (p.player_name, mins + p.minutes_played)
        except Exception as e:
            print(f"  [{i+1}/{len(games)}] game {gid} 실패: {e}")
            continue
        print(f"  [{i+1}/{len(games)}] game {gid}: {len(actions)} actions")

    X = pd.concat(X_list, ignore_index=True)
    Y = pd.concat(Y_list, ignore_index=True)
    A = pd.concat(A_list, ignore_index=True)
    print(f"\n총 행동 {len(A):,}개, 피처 {X.shape[1]}개. XGBoost 학습 중...")

    models = {}
    for col in ["scores", "concedes"]:
        m = xgboost.XGBClassifier(
            n_estimators=100, max_depth=5, learning_rate=0.1,
            n_jobs=-1, eval_metric="logloss", verbosity=0,
        )
        m.fit(X, Y[col])
        models[col] = m

    p_scores = models["scores"].predict_proba(X)[:, 1]
    p_concedes = models["concedes"].predict_proba(X)[:, 1]

    values = vaepformula.value(A, pd.Series(p_scores), pd.Series(p_concedes))
    A = A.join(values)  # offensive_value, defensive_value, vaep_value 추가

    # 선수별 합산
    agg = A.groupby("player_id")["vaep_value"].agg(
        vaep_total="sum", actions="count").reset_index()
    agg["player"] = agg["player_id"].map(lambda pid: players_map.get(pid, ("?", 0))[0])
    agg["minutes"] = agg["player_id"].map(lambda pid: players_map.get(pid, ("?", 0))[1])
    agg = agg[agg["minutes"] >= 450]  # 5경기(450분) 이상
    agg["vaep_p90"] = agg["vaep_total"] / agg["minutes"] * 90
    agg = agg.sort_values("vaep_p90", ascending=False)

    print("\nVAEP 레이팅 — 90분당 (450분 이상, 상위 15):")
    print(f"  {'선수':<28}{'VAEP/90':>9}{'총VAEP':>9}{'분':>7}{'행동':>7}")
    for r in agg.head(15).itertuples(index=False):
        print(f"  {r.player:<28}{r.vaep_p90:>9.3f}{r.vaep_total:>9.2f}{int(r.minutes):>7}{int(r.actions):>7}")

    agg.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")
    print(f"\n저장 → {OUT_CSV}")


if __name__ == "__main__":
    main()
