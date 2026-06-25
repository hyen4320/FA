import { useEffect, useState } from "react";
import { getJSON, fmt } from "./lib.js";

// 포지션별 평균 VAEP/90 + 평균 xT/경기 (전부 실측, 레버쿠젠).
export default function PositionScope() {
  const [positions, setPositions] = useState([]);
  useEffect(() => { getJSON("/positions").then(setPositions).catch(() => setPositions([])); }, []);

  const maxV = positions.reduce((m, p) => Math.max(m, p.avg_vaep), 0) || 1;

  return (
    <div style={{ padding: "24px 32px 48px" }}>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 16, maxWidth: 1000 }}>
        {positions.map((p) => (
          <div key={p.pos} style={{ background: "var(--panel)", border: "1px solid var(--line)", borderRadius: 12, padding: "18px 18px 16px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
              <span className="serif" style={{ fontSize: 22, fontWeight: 600, color: "var(--ink)" }}>{p.pos}</span>
              <span className="num" style={{ fontSize: 11, color: "var(--faint)" }}>{p.n}명</span>
            </div>
            <div style={{ fontSize: 11.5, color: "var(--faint)", marginTop: 2 }}>{p.posKo}</div>
            <div className="num serif" style={{ fontSize: 34, fontWeight: 500, color: "var(--accent)", margin: "14px 0 2px" }}>{fmt(p.avg_vaep)}</div>
            <div style={{ fontSize: 10.5, color: "var(--faint)", letterSpacing: ".04em" }}>평균 VAEP/90 (실측)</div>
            <div style={{ height: 6, background: "var(--track)", borderRadius: 99, margin: "12px 0 14px" }}>
              <div style={{ height: 6, borderRadius: 99, width: (p.avg_vaep / maxV * 100).toFixed(1) + "%", background: "var(--accent)" }} />
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", paddingTop: 12, borderTop: "1px solid var(--line2)" }}>
              <div>
                <div style={{ fontSize: 10, color: "var(--faint2)" }}>최다 기여</div>
                <div style={{ fontSize: 12.5, color: "var(--ink)", fontWeight: 500, marginTop: 2, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis", maxWidth: 110 }}>{p.top}</div>
              </div>
              <div style={{ textAlign: "right" }}>
                <div style={{ fontSize: 10, color: "var(--faint2)" }}>평균 xT/경기</div>
                <div className="num" style={{ fontSize: 13, color: "var(--ink3)", fontWeight: 600, marginTop: 2 }}>{fmt(p.avg_xt)}</div>
              </div>
            </div>
          </div>
        ))}
      </div>
      <p style={{ fontSize: 12.5, color: "var(--faint)", margin: "18px 4px 0", maxWidth: 900, lineHeight: 1.6 }}>
        평균 VAEP/90·xT/경기 모두 <strong>실측</strong>(레버쿠젠 시즌). 풀백·수비형 MF가 VAEP 상위인데 xT는 낮은 포지션도 있어, 두 지표가 포지션별로 다른 기여를 잡아낸다 — 맥락의 상실 주제와 직결.
      </p>
    </div>
  );
}
