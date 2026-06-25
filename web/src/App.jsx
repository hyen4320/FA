import { useEffect, useState } from "react";
import Pitch from "./Pitch.jsx";

const METRICS = {
  xt: {
    label: "xT (위협 생성)",
    endpoint: "/api/players/xt",
    valueKey: "xt_per_match",
    valueLabel: "경기당 xT",
    desc: "공을 더 위험한 구역으로 옮긴 정도. 전진 패스·운반 위주.",
  },
  vaep: {
    label: "VAEP (행동 가치)",
    endpoint: "/api/players/vaep",
    valueKey: "vaep_p90",
    valueLabel: "VAEP / 90분",
    desc: "득점 확률↑ + 실점 확률↓로 환산한 종합 가치. 수비·빌드업까지 포함.",
  },
};

export default function App() {
  const [metric, setMetric] = useState("xt");
  const [rows, setRows] = useState([]);
  const [selected, setSelected] = useState(null);
  const [pitchData, setPitchData] = useState(null);
  const [loading, setLoading] = useState(false);

  const cfg = METRICS[metric];

  useEffect(() => {
    fetch(cfg.endpoint + "?limit=25")
      .then((r) => r.json())
      .then(setRows)
      .catch(() => setRows([]));
  }, [metric]);

  function pickPlayer(name) {
    setSelected(name);
    setLoading(true);
    fetch(`/api/players/${encodeURIComponent(name)}/xt-actions?top=200`)
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => setPitchData(d))
      .catch(() => setPitchData(null))
      .finally(() => setLoading(false));
  }

  return (
    <div className="app">
      <header>
        <h1>FA — 풋볼 애널리틱스</h1>
        <p className="sub">분데스리가 2023/24 · 레버쿠젠 시즌 · 맥락의 상실을 푸는 첫 조각</p>
      </header>

      <div className="metric-tabs">
        {Object.entries(METRICS).map(([key, m]) => (
          <button
            key={key}
            className={key === metric ? "tab active" : "tab"}
            onClick={() => setMetric(key)}
          >
            {m.label}
          </button>
        ))}
      </div>
      <p className="metric-desc">{cfg.desc}</p>

      <div className="layout">
        <section className="ranking">
          <table>
            <thead>
              <tr>
                <th>#</th>
                <th>선수</th>
                <th className="num">{cfg.valueLabel}</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r, i) => (
                <tr
                  key={r.player}
                  className={r.player === selected ? "row sel" : "row"}
                  onClick={() => pickPlayer(r.player)}
                >
                  <td className="rank">{i + 1}</td>
                  <td>{r.player}</td>
                  <td className="num">{r[cfg.valueKey]?.toFixed(3)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>

        <section className="viz">
          {loading && <div className="placeholder">불러오는 중…</div>}
          {!loading && !pitchData && (
            <div className="placeholder">선수를 클릭하면 위협 생성 패스맵이 나타납니다.</div>
          )}
          {!loading && pitchData && <Pitch data={pitchData} />}
        </section>
      </div>
    </div>
  );
}
