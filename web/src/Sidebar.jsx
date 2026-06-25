const NAV = [
  { key: "player", label: "선수" },
  { key: "club", label: "구단" },
  { key: "position", label: "포지션" },
];

function navStyle(active) {
  return {
    display: "flex", alignItems: "center", gap: 9, padding: "9px 11px",
    borderRadius: 7, cursor: "pointer", fontSize: 13.5,
    color: active ? "var(--accent-ink)" : "var(--muted)",
    fontWeight: active ? 600 : 400,
    background: active ? "var(--accent-tint)" : "transparent",
    border: active ? "1px solid var(--accent-bd)" : "1px solid transparent",
  };
}

export default function Sidebar({ scope, setScope, metric, setMetric }) {
  const segBase = {
    flex: 1, textAlign: "center", fontSize: 12, fontWeight: 600,
    padding: "6px 0", borderRadius: 6, cursor: "pointer",
  };
  const seg = (active) => active
    ? { ...segBase, color: "var(--on-accent)", background: "var(--invert)" }
    : { ...segBase, color: "var(--faint)" };

  return (
    <aside style={{
      background: "var(--panel2)", borderRight: "1px solid var(--line)",
      padding: "24px 18px", display: "flex", flexDirection: "column", gap: 26, overflow: "auto",
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: 9 }}>
        <span style={{
          width: 26, height: 26, borderRadius: 6, background: "var(--accent)",
          color: "var(--on-accent)", fontWeight: 700, fontSize: 14,
          display: "flex", alignItems: "center", justifyContent: "center",
        }}>FA</span>
        <div>
          <div className="serif" style={{ fontSize: 17, fontWeight: 600, lineHeight: 1 }}>맥락 분석 콘솔</div>
          <div style={{ fontSize: 10.5, color: "var(--faint)", marginTop: 3, letterSpacing: ".02em" }}>
            Football Context Analytics
          </div>
        </div>
      </div>

      {/* nav */}
      <div>
        <div style={{ fontSize: 10.5, fontWeight: 600, letterSpacing: ".14em", textTransform: "uppercase", color: "var(--faint2)", margin: "0 4px 10px" }}>탐색</div>
        <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
          {NAV.map((n) => (
            <div key={n.key} style={navStyle(scope === n.key)} onClick={() => setScope(n.key)}>
              <span style={{ width: 7, height: 7, borderRadius: 2, background: "currentColor", opacity: 0.7 }} />
              {n.label}
            </div>
          ))}
        </div>
      </div>

      {/* filters */}
      <div>
        <div style={{ fontSize: 10.5, fontWeight: 600, letterSpacing: ".14em", textTransform: "uppercase", color: "var(--faint2)", margin: "0 4px 12px" }}>필터</div>

        <div style={{ marginBottom: 14 }}>
          <div style={{ fontSize: 11, color: "var(--faint)", margin: "0 4px 6px" }}>리그 · 시즌</div>
          <div style={{ background: "var(--panel)", border: "1px solid var(--line)", borderRadius: 7, padding: "9px 12px", fontSize: 12.5, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            분데스리가 23/24 <span style={{ color: "var(--faint2)" }}>▾</span>
          </div>
        </div>

        <div style={{ marginBottom: 14 }}>
          <div style={{ fontSize: 11, color: "var(--faint)", margin: "0 4px 6px" }}>기준 지표</div>
          <div style={{ display: "inline-flex", width: "100%", background: "var(--seg)", border: "1px solid var(--line)", borderRadius: 8, padding: 3 }}>
            <span style={seg(metric === "vaep")} onClick={() => setMetric("vaep")}>VAEP/90</span>
            <span style={seg(metric === "xt")} onClick={() => setMetric("xt")}>xT/경기</span>
          </div>
        </div>

        <div>
          <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, color: "var(--faint)", margin: "0 4px 8px" }}>
            <span>최소 출전</span><span className="num" style={{ color: "var(--muted)" }}>450분</span>
          </div>
          <div style={{ height: 5, background: "var(--line)", borderRadius: 99, margin: "0 4px" }}>
            <div style={{ height: 5, width: "30%", background: "var(--accent)", borderRadius: 99, position: "relative" }}>
              <span style={{ position: "absolute", right: -6, top: -4, width: 13, height: 13, borderRadius: 99, background: "var(--panel)", border: "2px solid var(--accent)" }} />
            </div>
          </div>
        </div>
      </div>

      <div style={{ marginTop: "auto", borderTop: "1px solid var(--line)", paddingTop: 14 }}>
        <div className="mono" style={{ fontSize: 10, color: "var(--faint2)", lineHeight: 1.7 }}>
          StatsBomb · socceraction<br />137,765 events · 34 matches
        </div>
      </div>
    </aside>
  );
}
