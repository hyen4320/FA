"""FA 백엔드 API (FastAPI).

원칙(CLAUDE.md): 무거운 계산은 시작 시 1회만, 요청은 메모리에서 조회만.

시작 시 DuckDB events + VAEP CSV + xT를 합쳐 '선수 개요' 테이블을 만든다.
실데이터: 선수 랭킹(VAEP/90·xT/경기), 팀·포지션, 위협 패스맵, 행동 구성.
※ '맥락 보정(동료/리그/상대 분해)'은 아직 모델 미구축 → 프론트에서 예시로 표시.

실행:
    PYTHONUTF8=1 .venv/Scripts/python.exe -m uvicorn api.main:app --reload --port 8000
"""

import json
import sys
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
import xt_core  # noqa: E402

DATA = ROOT / "data"
VAEP_CSV = DATA / "vaep_rating.csv"
TIER_CSV = DATA / "vaep_by_tier.csv"
METRICS_JSON = DATA / "vaep_metrics.json"

# 실측 백분위에 쓰는 지표 라벨
SKILL_LABELS = ["위협 생성", "전진 패스량", "박스 침투", "수비 가담", "공중 경합"]
DEF_TYPES = ("Pressure", "Ball Recovery", "Interception", "Block", "Clearance",
             "Foul Committed", "50/50", "Tackle")

app = FastAPI(title="FA API", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

STATE: dict = {}

POS_KO = {"GK": "골키퍼", "CB": "센터백", "FB": "풀백", "DM": "수비형 MF",
          "CM": "중앙 MF", "AM": "공격형 MF", "W": "윙어", "ST": "스트라이커", "—": "—"}


def short_pos(p: str) -> str:
    if not p or p == "None":
        return "—"
    s = p.lower()
    if "goalkeeper" in s:
        return "GK"
    if "wing back" in s:
        return "FB"
    if "back" in s:
        return "CB" if "center" in s else "FB"
    if "defensive midfield" in s:
        return "DM"
    if "attacking midfield" in s:
        return "AM"
    if "wing" in s:
        return "W"
    if "midfield" in s:
        return "CM"
    if "forward" in s or "striker" in s:
        return "ST"
    return "—"


def build_overview(con) -> pd.DataFrame:
    """선수별 실데이터 통합: 팀·포지션·출전·VAEP·xT·행동구성."""
    meta = con.execute(
        """
        SELECT player,
               mode(team) AS team,
               mode(position) AS pos_raw,
               count(*) FILTER (WHERE type='Pass')  AS n_pass,
               count(*) FILTER (WHERE type='Carry') AS n_carry,
               count(*) FILTER (WHERE type='Shot')  AS n_shot
        FROM events WHERE player IS NOT NULL GROUP BY player
        """
    ).df()
    meta["pos"] = meta["pos_raw"].map(short_pos)

    xt = STATE["xt_ranking"][["player", "xt_per_match", "xt_total", "matches"]]
    vaep = STATE["vaep"][["player", "vaep_p90", "vaep_total", "minutes"]] \
        if not STATE["vaep"].empty else pd.DataFrame(columns=["player", "vaep_p90", "vaep_total", "minutes"])

    df = meta.merge(vaep, on="player", how="inner").merge(xt, on="player", how="left")
    df["minutes"] = df["minutes"].fillna(0).astype(int)
    df["xt_per_match"] = df["xt_per_match"].fillna(0.0)
    df = df[df["minutes"] >= 450].reset_index(drop=True)
    return df


def build_skills(con, overview: pd.DataFrame, actions: pd.DataFrame) -> dict:
    """선수별 실측 per-90 지표 → 선수 풀 내 백분위. (예시 아님)

    표본이 작아(자격 선수 ~20명) 포지션 내가 아닌 '풀 내' 백분위로 계산한다.
    """
    mins = overview.set_index("player")["minutes"].to_dict()
    pool = set(overview["player"])

    a = actions[actions["player"].isin(pool)].copy()
    fwd = a[(a["type"] == "Pass") & (a["x1"] > a["x0"] + 5)].groupby("player").size()
    box = a[(a["x1"] >= 102) & (a["y1"].between(18, 62))].groupby("player").size()
    threat = a.groupby("player")["xt"].apply(lambda s: s[s > 0].sum())

    cnt = con.execute(
        f"""SELECT player,
               count(*) FILTER (WHERE type IN {DEF_TYPES}) AS deff,
               count(*) FILTER (WHERE type='Duel') AS duel
            FROM events WHERE player IS NOT NULL GROUP BY player"""
    ).df().set_index("player")

    def per90(series, p):
        m = mins.get(p, 0)
        return (series.get(p, 0) / m * 90) if m else 0.0

    raw = {p: [per90(threat, p), per90(fwd, p), per90(box, p),
               per90(cnt["deff"] if "deff" in cnt else {}, p),
               per90(cnt["duel"] if "duel" in cnt else {}, p)] for p in pool}
    df = pd.DataFrame(raw, index=SKILL_LABELS).T  # rows=player
    pct = df.rank(pct=True) * 100  # 풀 내 백분위
    return {p: [{"label": lbl, "val": int(round(pct.loc[p, lbl]))} for lbl in SKILL_LABELS]
            for p in pool}


@app.on_event("startup")
def warm_cache() -> None:
    grid = xt_core.load_xt_grid()
    con = duckdb.connect(str(xt_core.DB_PATH), read_only=True)
    actions = xt_core.compute_actions(con, grid)
    STATE["xt_actions"] = actions
    STATE["xt_ranking"] = xt_core.player_ranking(actions, min_matches=5)
    STATE["vaep"] = pd.read_csv(VAEP_CSV) if VAEP_CSV.exists() else pd.DataFrame()
    STATE["overview"] = build_overview(con)
    STATE["tiers"] = pd.read_csv(TIER_CSV) if TIER_CSV.exists() else pd.DataFrame()
    STATE["metrics"] = json.loads(METRICS_JSON.read_text(encoding="utf-8")) if METRICS_JSON.exists() else {}
    STATE["skills"] = build_skills(con, STATE["overview"], actions)
    # 경기 날짜 순서 (실제 경기별 추이용)
    md = con.execute("SELECT match_id, match_date FROM matches").df()
    STATE["match_order"] = {int(r.match_id): str(r.match_date) for r in md.itertuples(index=False)}
    con.close()
    print(f"[startup] overview={len(STATE['overview'])} players, "
          f"xt_actions={len(actions):,}, tiers={len(STATE['tiers'])}")


def _val(row, metric):
    return float(row["xt_per_match"] if metric == "xt" else row["vaep_p90"])


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "players": len(STATE.get("overview", []))}


@app.get("/api/metrics")
def metrics() -> dict:
    """VAEP 교차검증 성능 (정직성 근거)."""
    return STATE.get("metrics", {})


@app.get("/api/players/overview")
def overview(metric: str = "vaep", limit: int = 30) -> list[dict]:
    df = STATE["overview"].copy()
    key = "xt_per_match" if metric == "xt" else "vaep_p90"
    df = df.sort_values(key, ascending=False).head(limit)
    out = []
    for r in df.itertuples(index=False):
        out.append({
            "player": r.player, "team": r.team, "pos": r.pos, "posKo": POS_KO.get(r.pos, r.pos),
            "minutes": int(r.minutes),
            "vaep_p90": round(float(r.vaep_p90), 3),
            "xt_per_match": round(float(r.xt_per_match), 3),
            "value": round(_val(r._asdict(), metric), 3),
        })
    return out


@app.get("/api/players/{player}")
def player_detail(player: str) -> dict:
    df = STATE["overview"]
    row = df[df["player"] == player]
    if row.empty:
        raise HTTPException(404, f"선수 없음: {player}")
    r = row.iloc[0]
    total_act = int(r.n_pass + r.n_carry + r.n_shot) or 1
    mix = [
        {"label": "패스", "pct": round(r.n_pass / total_act * 100)},
        {"label": "운반", "pct": round(r.n_carry / total_act * 100)},
        {"label": "슈팅", "pct": round(r.n_shot / total_act * 100)},
    ]

    # 상대 티어별 VAEP/90 (실측)
    tiers = []
    td = STATE["tiers"]
    if not td.empty:
        sub = td[td["player"] == player].set_index("tier")
        for t in ["강", "중", "약"]:
            tiers.append({"tier": t,
                          "vaep_p90": float(sub.loc[t, "vaep_p90"]) if t in sub.index else None,
                          "minutes": int(sub.loc[t, "minutes"]) if t in sub.index else 0})

    # 경기별 xT 추이 (실측, 날짜순 최근 15)
    acts = STATE["xt_actions"]
    pa = acts[acts["player"] == player]
    order = STATE["match_order"]
    by_match = pa.groupby("match_id")["xt"].apply(lambda s: float(s[s > 0].sum()))
    trend = [{"date": order.get(int(mid), ""), "xt": round(v, 3)}
             for mid, v in by_match.items()]
    trend.sort(key=lambda x: x["date"])
    trend = trend[-15:]

    return {
        "player": r.player, "team": r.team, "pos": r.pos, "posKo": POS_KO.get(r.pos, r.pos),
        "minutes": int(r.minutes),
        "vaep_p90": round(float(r.vaep_p90), 3),
        "xt_per_match": round(float(r.xt_per_match), 3),
        "matches": int(r.matches) if pd.notna(r.matches) else 0,
        "mix": mix,
        "tiers": tiers,
        "trend": trend,
        "percentiles": STATE["skills"].get(player, []),
    }


@app.get("/api/players/{player}/xt-actions")
def player_xt_actions(player: str, top: int = 200) -> dict:
    acts = STATE["xt_actions"]
    sub = acts[(acts["player"] == player) & (acts["xt"] > 0)]
    if sub.empty:
        raise HTTPException(404, f"위협 행동 없음: {player}")
    sub = sub.nlargest(top, "xt")
    cols = ["type", "x0", "y0", "x1", "y1", "xt"]
    return {
        "player": player, "team": str(sub["team"].iloc[0]), "count": int(len(sub)),
        "actions": sub[cols].round(4).to_dict(orient="records"),
    }


@app.get("/api/clubs")
def clubs(limit: int = 18) -> list[dict]:
    """구단 비교는 xT 기준 (VAEP는 상대팀 표본이 없어 전 구단 비교 불가).

    xt_actions는 전 경기·전 팀을 담으므로 경기당 xT로 18개 클럽을 비교한다.
    상대팀은 각 1경기라 표본이 작다(프론트에 주의 표시).
    """
    acts = STATE["xt_actions"]
    rows = []
    for team, g in acts.groupby("team"):
        matches = g["match_id"].nunique() or 1
        xt_pm = float(g["xt"].sum() / matches)
        top = g.groupby("player")["xt"].sum().idxmax()
        rows.append({"team": team, "matches": int(matches),
                     "xt_per_match": round(xt_pm, 3), "top": top})
    rows.sort(key=lambda x: x["xt_per_match"], reverse=True)
    return rows[:limit]


@app.get("/api/positions")
def positions() -> list[dict]:
    df = STATE["overview"]
    rows = []
    for pos, g in df.groupby("pos"):
        top = g.sort_values("vaep_p90", ascending=False).iloc[0]["player"]
        rows.append({"pos": pos, "posKo": POS_KO.get(pos, pos), "n": int(len(g)),
                     "avg_vaep": round(float(g["vaep_p90"].mean()), 3),
                     "avg_xt": round(float(g["xt_per_match"].mean()), 3), "top": top})
    rows.sort(key=lambda x: x["avg_vaep"], reverse=True)
    return rows
