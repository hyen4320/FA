"""StatsBomb 무료 데이터 → DuckDB 적재 (시즌 단위).

한 대회/시즌의 모든 경기 이벤트를 받아 DuckDB에 적재한다.
- matches 테이블: 경기 메타(상대, 날짜, 스코어)
- events 테이블: 전 경기 이벤트(각 행에 match_id 부여)

기본값은 분데스리가 2023/24 (StatsBomb 무료 = 레버쿠젠 무패 시즌 전체).

실행:
    PYTHONUTF8=1 .venv/Scripts/python.exe analysis/ingest/statsbomb_to_duckdb.py
"""

import sys
import warnings
from pathlib import Path

import duckdb
import pandas as pd
from statsbombpy import sb

warnings.filterwarnings("ignore")
sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
DB_PATH = DATA_DIR / "fa.duckdb"

# 분데스리가 2023/2024 (무료 데이터 = 레버쿠젠 시즌 전체)
COMPETITION_ID = 9
SEASON_ID = 281


def serialize_nested(df: pd.DataFrame) -> pd.DataFrame:
    """DuckDB가 못 먹는 중첩 list/dict 컬럼을 문자열로 직렬화."""
    df = df.copy()
    for col in df.columns:
        if df[col].apply(lambda v: isinstance(v, (list, dict))).any():
            df[col] = df[col].astype(str)
    return df


def main() -> None:
    DATA_DIR.mkdir(exist_ok=True)

    matches = sb.matches(competition_id=COMPETITION_ID, season_id=SEASON_ID)
    matches = matches.sort_values("match_date").reset_index(drop=True)
    comp_name = matches["competition"].iloc[0] if "competition" in matches else "?"
    print(f"대회/시즌: {comp_name} {matches['season'].iloc[0]} — 경기 {len(matches)}개")

    all_events = []
    for i, m in matches.iterrows():
        mid = int(m["match_id"])
        try:
            ev = sb.events(match_id=mid)
        except Exception as e:
            print(f"  [{i+1}/{len(matches)}] match {mid} 실패: {e}")
            continue
        ev["match_id"] = mid
        all_events.append(ev)
        print(f"  [{i+1}/{len(matches)}] {m['home_team']} {m['home_score']}-{m['away_score']} "
              f"{m['away_team']}  ({len(ev)} events)")

    events = pd.concat(all_events, ignore_index=True)
    events = serialize_nested(events)
    matches_clean = serialize_nested(matches)

    con = duckdb.connect(str(DB_PATH))
    con.register("events_df", events)
    con.register("matches_df", matches_clean)
    con.execute("CREATE OR REPLACE TABLE events AS SELECT * FROM events_df")
    con.execute("CREATE OR REPLACE TABLE matches AS SELECT * FROM matches_df")
    n_ev = con.execute("SELECT count(*) FROM events").fetchone()[0]
    n_m = con.execute("SELECT count(*) FROM matches").fetchone()[0]
    con.close()

    print(f"\n적재 완료 → {DB_PATH}")
    print(f"  matches {n_m}경기, events {n_ev:,}행")


if __name__ == "__main__":
    main()
