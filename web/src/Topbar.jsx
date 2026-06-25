export default function Topbar({ title, sub, count, theme, toggleTheme }) {
  const dark = theme === "dark";
  return (
    <div style={{
      position: "sticky", top: 0, zIndex: 5, background: "var(--bg)",
      borderBottom: "1px solid var(--line)", padding: "18px 32px",
      display: "flex", justifyContent: "space-between", alignItems: "center",
    }}>
      <div>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <h1 className="serif" style={{ fontWeight: 600, fontSize: 22, margin: 0, color: "var(--ink)" }}>{title}</h1>
          <span style={{ fontSize: 11, color: "var(--muted)", background: "var(--panel)", border: "1px solid var(--line)", borderRadius: 99, padding: "3px 10px" }}>{count}</span>
        </div>
        <p style={{ fontSize: 12.5, color: "var(--faint)", margin: "5px 0 0" }}>{sub}</p>
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, background: "var(--panel)", border: "1px solid var(--line)", borderRadius: 8, padding: "8px 12px", width: 200 }}>
          <span style={{ color: "var(--faint2)", fontSize: 13 }}>⌕</span>
          <span style={{ fontSize: 12.5, color: "var(--faint2)" }}>선수·구단 검색</span>
        </div>
        <div onClick={toggleTheme} style={{ display: "flex", alignItems: "center", gap: 7, background: "var(--panel)", border: "1px solid var(--line)", borderRadius: 8, padding: "8px 12px", cursor: "pointer" }}>
          <span style={{ fontSize: 13 }}>{dark ? "☀" : "☾"}</span>
          <span style={{ fontSize: 12, fontWeight: 500, color: "var(--muted)" }}>{dark ? "라이트" : "다크"}</span>
        </div>
      </div>
    </div>
  );
}
