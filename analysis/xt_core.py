"""xT(Expected Threat) 공통 로직 — 시각화 스크립트와 API가 함께 쓴다.

피치를 격자로 나눠 각 구역의 '득점 위협값'을 미리 학습해 둔 그리드를 이용해,
패스·운반 한 행동의 가치 = xT(도착 구역) - xT(출발 구역) 로 계산한다.
(Karun Singh 공개 12x8 그리드)
"""

import json
from pathlib import Path
from urllib.request import urlretrieve

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
DB_PATH = DATA_DIR / "fa.duckdb"
GRID_PATH = DATA_DIR / "open_xt_12x8_v1.json"
GRID_URL = "https://karun.in/blog/data/open_xt_12x8_v1.json"

PITCH_X, PITCH_Y = 120.0, 80.0


def load_xt_grid() -> np.ndarray:
    if not GRID_PATH.exists():
        urlretrieve(GRID_URL, GRID_PATH)
    return np.array(json.loads(GRID_PATH.read_text()))


def parse_xy(s):
    if s is None or s == "None" or (isinstance(s, float) and np.isnan(s)):
        return None
    try:
        v = json.loads(s) if isinstance(s, str) else s
        return float(v[0]), float(v[1])
    except Exception:
        return None


def compute_actions(con, grid: np.ndarray) -> pd.DataFrame:
    """DuckDB 연결에서 전 경기 패스·운반의 xT 증가량 계산 → DataFrame.

    반환 컬럼: match_id, player, team, type, x0, y0, x1, y1, xt
    """
    n_rows, n_cols = grid.shape

    def cell(x, y):
        col = min(int(x / PITCH_X * n_cols), n_cols - 1)
        row = min(int(y / PITCH_Y * n_rows), n_rows - 1)
        return float(grid[row, col])

    df = con.execute(
        """
        SELECT match_id, player, team, type, location,
               pass_end_location, carry_end_location
        FROM events
        WHERE type IN ('Pass', 'Carry') AND location IS NOT NULL
        """
    ).df()

    rows = []
    for r in df.itertuples(index=False):
        start = parse_xy(r.location)
        end = parse_xy(r.pass_end_location if r.type == "Pass" else r.carry_end_location)
        if start is None or end is None:
            continue
        xt = cell(*end) - cell(*start)
        rows.append((r.match_id, r.player, r.team, r.type,
                     start[0], start[1], end[0], end[1], xt))
    return pd.DataFrame(rows, columns=[
        "match_id", "player", "team", "type", "x0", "y0", "x1", "y1", "xt"])


def player_ranking(actions: pd.DataFrame, min_matches: int = 5) -> pd.DataFrame:
    """선수별 시즌 xT 누적 랭킹 (경기당 xT, min_matches 이상)."""
    agg = actions.groupby(["player", "team"]).agg(
        xt_total=("xt", "sum"),
        actions=("xt", "count"),
        matches=("match_id", "nunique"),
    ).reset_index()
    agg["xt_per_match"] = agg["xt_total"] / agg["matches"]
    agg = agg[agg["matches"] >= min_matches].sort_values("xt_per_match", ascending=False)
    return agg.reset_index(drop=True)
