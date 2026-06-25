// 위협 생성 패스맵 — 실데이터(/api/players/{name}/xt-actions).
// 색·굵기 = xT 증가량. 테마는 CSS 변수(--pitch-*)로 라이트/다크 대응.

export default function Pitch({ data }) {
  const actions = data?.actions ?? [];
  const maxXt = actions.reduce((m, a) => Math.max(m, a.xt), 0) || 1;

  return (
    <div>
      <svg viewBox="-3 -3 126 86" style={{ width: "100%", height: "auto", display: "block" }}>
        <defs>
          <marker id="fa-arr" viewBox="0 0 10 10" refX="7" refY="5"
            markerWidth="4.5" markerHeight="4.5" orient="auto-start-reverse">
            <path d="M0 0 L10 5 L0 10 z" fill="context-stroke" />
          </marker>
        </defs>
        <rect x="0" y="0" width="120" height="80" rx="1"
          style={{ fill: "var(--pitch-bg)", stroke: "var(--pitch-line)", strokeWidth: 0.4 }} />
        <line x1="60" y1="0" x2="60" y2="80" style={{ stroke: "var(--pitch-line)", strokeWidth: 0.4 }} />
        <circle cx="60" cy="40" r="9.15" style={{ fill: "none", stroke: "var(--pitch-line)", strokeWidth: 0.4 }} />
        <circle cx="60" cy="40" r="0.7" style={{ fill: "var(--pitch-line)" }} />
        <rect x="0" y="18" width="18" height="44" style={{ fill: "none", stroke: "var(--pitch-line)", strokeWidth: 0.4 }} />
        <rect x="102" y="18" width="18" height="44" style={{ fill: "none", stroke: "var(--pitch-line)", strokeWidth: 0.4 }} />
        <rect x="0" y="30" width="6" height="20" style={{ fill: "none", stroke: "var(--pitch-line)", strokeWidth: 0.4 }} />
        <rect x="114" y="30" width="6" height="20" style={{ fill: "none", stroke: "var(--pitch-line)", strokeWidth: 0.4 }} />
        <rect x="-1.2" y="36" width="1.2" height="8" style={{ fill: "var(--pitch-line)" }} />
        <rect x="120" y="36" width="1.2" height="8" style={{ fill: "var(--pitch-line)" }} />
        <g>
          {actions.map((a, i) => {
            const t = a.xt / maxXt;
            const high = t > 0.72;
            return (
              <line key={i} x1={a.x0} y1={a.y0} x2={a.x1} y2={a.y1}
                strokeWidth={(0.4 + t * 1.5).toFixed(2)}
                strokeOpacity={(0.3 + t * 0.55).toFixed(2)}
                strokeLinecap="round" markerEnd="url(#fa-arr)"
                style={{ stroke: high ? "var(--amber2)" : "var(--accent)" }} />
            );
          })}
        </g>
      </svg>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: 8, padding: "0 2px" }}>
        <span style={{ fontSize: 11, color: "var(--faint)" }}>오른쪽으로 공격 · 색·굵기 = xT 증가량</span>
        <span style={{ fontSize: 11, color: "var(--faint)" }}>
          <span style={{ color: "var(--amber2)" }}>●</span> 고위협 · {data?.count ?? 0}개
        </span>
      </div>
    </div>
  );
}
