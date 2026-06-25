"""FA 백엔드 API (FastAPI).

원칙(CLAUDE.md): 무거운 계산은 시작 시 1회만, 요청은 메모리에서 조회만.

- 시작 시 DuckDB events에서 xT 행동을 계산해 메모리에 보관
- VAEP는 배치로 만든 data/vaep_rating.csv 를 읽음

엔드포인트
  GET /api/health
  GET /api/players/xt              시즌 xT 랭킹(경기당)
  GET /api/players/vaep            VAEP 랭킹(90분당)
  GET /api/players/{player}/xt-actions   해당 선수의 위협 생성 행동(피치 좌표)

실행:
    PYTHONUTF8=1 .venv/Scripts/python.exe -m uvicorn api.main:app --reload --port 8000
"""

import sys
from pathlib import Path

import duckdb
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
import xt_core  # noqa: E402

VAEP_CSV = ROOT / "data" / "vaep_rating.csv"

app = FastAPI(title="FA API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 메모리 캐시 (시작 시 1회 채움)
STATE: dict = {}


@app.on_event("startup")
def warm_cache() -> None:
    grid = xt_core.load_xt_grid()
    con = duckdb.connect(str(xt_core.DB_PATH), read_only=True)
    actions = xt_core.compute_actions(con, grid)
    con.close()
    STATE["xt_actions"] = actions
    STATE["xt_ranking"] = xt_core.player_ranking(actions, min_matches=5)
    if VAEP_CSV.exists():
        STATE["vaep"] = pd.read_csv(VAEP_CSV)
    else:
        STATE["vaep"] = pd.DataFrame()
    print(f"[startup] xt_actions={len(actions):,}, "
          f"xt_ranking={len(STATE['xt_ranking'])}, vaep={len(STATE['vaep'])}")


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "xt_actions": len(STATE.get("xt_actions", []))}


@app.get("/api/players/xt")
def players_xt(limit: int = 30) -> list[dict]:
    df = STATE["xt_ranking"].head(limit).copy()
    df = df.round({"xt_total": 3, "xt_per_match": 3})
    return df.to_dict(orient="records")


@app.get("/api/players/vaep")
def players_vaep(limit: int = 30) -> list[dict]:
    df = STATE["vaep"]
    if df.empty:
        return []
    df = df.sort_values("vaep_p90", ascending=False).head(limit).copy()
    df = df.round({"vaep_total": 3, "vaep_p90": 3})
    keep = ["player", "vaep_p90", "vaep_total", "minutes", "actions"]
    return df[[c for c in keep if c in df.columns]].to_dict(orient="records")


@app.get("/api/players/{player}/xt-actions")
def player_xt_actions(player: str, top: int = 200) -> dict:
    acts = STATE["xt_actions"]
    sub = acts[(acts["player"] == player) & (acts["xt"] > 0)]
    if sub.empty:
        raise HTTPException(404, f"선수를 찾을 수 없거나 위협 행동이 없습니다: {player}")
    sub = sub.nlargest(top, "xt")
    cols = ["type", "x0", "y0", "x1", "y1", "xt"]
    return {
        "player": player,
        "team": str(sub["team"].iloc[0]),
        "count": int(len(sub)),
        "actions": sub[cols].round(4).to_dict(orient="records"),
    }
