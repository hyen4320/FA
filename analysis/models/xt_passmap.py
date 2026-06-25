"""xT 시즌 누적 랭킹 + 1위 선수 패스맵 시각화.

xT 계산 로직은 analysis/xt_core.py 에 공통화되어 있고(여기·API가 공유),
이 스크립트는 그 결과를 표/그림으로 보여주는 역할만 한다.

실행:
    PYTHONUTF8=1 .venv/Scripts/python.exe analysis/models/xt_passmap.py
"""

import sys
from pathlib import Path

import duckdb
import matplotlib as mpl
from mplsoccer import Pitch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # analysis/ 를 import 경로에
import xt_core  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
mpl.rcParams["font.family"] = "Malgun Gothic"
mpl.rcParams["axes.unicode_minus"] = False

OUT_PNG = xt_core.DATA_DIR / "xt_passmap.png"


def main() -> None:
    grid = xt_core.load_xt_grid()
    con = duckdb.connect(str(xt_core.DB_PATH))
    actions = xt_core.compute_actions(con, grid)
    con.close()
    print(f"분석 행동(패스+운반): {len(actions):,}개")

    rank = xt_core.player_ranking(actions, min_matches=5)
    print("\n시즌 xT 기여 랭킹 — 경기당 (5경기 이상, 상위 15):")
    print(f"  {'선수':<26}{'팀':<22}{'경기당xT':>8}{'총xT':>9}{'경기':>5}")
    for r in rank.head(15).itertuples(index=False):
        print(f"  {r.player:<26}{r.team:<22}{r.xt_per_match:>8.3f}{r.xt_total:>9.2f}{r.matches:>5}")

    star = rank.iloc[0]["player"]
    sub = actions[(actions["player"] == star) & (actions["xt"] > 0)]
    print(f"\n시각화 대상: {star} (위협 생성 행동 {len(sub)}개)")

    norm = mpl.colors.Normalize(vmin=sub["xt"].min(), vmax=sub["xt"].max())
    colors = mpl.colormaps["viridis"](norm(sub["xt"].values))
    pitch = Pitch(pitch_type="statsbomb", line_color="#888888", pitch_color="#0d1117")
    fig, ax = pitch.draw(figsize=(11, 7))
    fig.set_facecolor("#0d1117")
    pitch.arrows(sub["x0"], sub["y0"], sub["x1"], sub["y1"],
                 ax=ax, width=1.8, headwidth=4, headlength=4, color=colors, alpha=0.55)
    sm = mpl.cm.ScalarMappable(norm=norm, cmap="viridis")
    cbar = fig.colorbar(sm, ax=ax, shrink=0.6, pad=0.01)
    cbar.set_label("xT 증가량", color="white")
    cbar.ax.yaxis.set_tick_params(color="white")
    mpl.pyplot.setp(mpl.pyplot.getp(cbar.ax.axes, "yticklabels"), color="white")
    ax.set_title(f"{star} — 시즌 위협 생성 행동 (색 = xT 증가량)", color="white", fontsize=13)
    fig.savefig(OUT_PNG, dpi=130, bbox_inches="tight", facecolor="#0d1117")
    print(f"패스맵 저장 → {OUT_PNG}")


if __name__ == "__main__":
    main()
