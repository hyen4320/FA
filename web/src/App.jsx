import { useEffect, useState } from "react";
import Sidebar from "./Sidebar.jsx";
import Topbar from "./Topbar.jsx";
import PlayerScope from "./PlayerScope.jsx";
import ClubScope from "./ClubScope.jsx";
import PositionScope from "./PositionScope.jsx";
import { getJSON } from "./lib.js";

const TITLES = {
  player: { t: "선수 랭킹", s: "교차검증 VAEP/90 · 선수를 클릭하면 상세를 봅니다", c: "선수" },
  club: { t: "구단 분석", s: "경기당 위협 생성(xT) 기준 구단 비교", c: "구단" },
  position: { t: "포지션 분석", s: "포지션별 평균 기여 (실측)", c: "포지션" },
};

export default function App() {
  const [theme, setTheme] = useState("light");
  const [scope, setScope] = useState("player");
  const [metric, setMetric] = useState("vaep"); // vaep | xt
  const [players, setPlayers] = useState([]);
  const [selected, setSelected] = useState(null);

  useEffect(() => {
    document.body.style.background = theme === "dark" ? "#13151a" : "#f4f2ee";
  }, [theme]);

  useEffect(() => {
    getJSON("/players/overview?metric=vaep&limit=30")
      .then((d) => { setPlayers(d); if (d.length && !selected) setSelected(d[0].player); })
      .catch(() => setPlayers([]));
  }, []);

  const ti = TITLES[scope];
  const count = scope === "player" ? `${players.length}명`
    : scope === "club" ? "전 구단" : "포지션별";

  return (
    <div className="fa-app" data-theme={theme}
      style={{ display: "grid", gridTemplateColumns: "248px 1fr", height: "100vh", minWidth: 1240, color: "var(--ink)", background: "var(--bg)" }}>
      <Sidebar scope={scope} setScope={setScope} metric={metric} setMetric={setMetric} />
      <main style={{ overflow: "auto", background: "var(--bg)" }}>
        <Topbar title={ti.t} sub={ti.s} count={count} theme={theme} toggleTheme={() => setTheme(theme === "dark" ? "light" : "dark")} />
        {scope === "player" && (
          <PlayerScope players={players} metric={metric} selected={selected} setSelected={setSelected} />
        )}
        {scope === "club" && <ClubScope />}
        {scope === "position" && <PositionScope />}
      </main>
    </div>
  );
}
