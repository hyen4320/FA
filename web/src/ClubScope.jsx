import { useEffect, useState } from "react";
import { getJSON, fmt } from "./lib.js";

// 구단 비교는 xT 기준(전 구단). '보정'은 예시값.
export default function ClubScope() {
  const [clubs, setClubs] = useState([]);
  useEffect(() => { getJSON("/clubs?limit=12").then(setClubs).catch(() => setClubs([])); }, []);

  const maxXt = clubs.reduce((m, c) => Math.max(m, c.xt_per_match), 0) || 1;

  return (
    <div style={{ padding: "24px 32px 48px" }}>
      <section style={{ background: "var(--panel)", border: "1px solid var(--line)", borderRadius: 12, overflow: "hidden", maxWidth: 880 }}>
        <div style={{ display: "grid", gridTemplateColumns: "34px 1fr 220px 120px 70px", gap: 14, padding: "13px 20px", borderBottom: "1px solid var(--line)", fontSize: 10.5, fontWeight: 600, letterSpacing: ".08em", textTransform: "uppercase", color: "var(--faint)", background: "var(--panel2)" }}>
          <span>#</span><span>구단</span><span>경기당 xT (위협 생성)</span><span>최다 기여</span><span style={{ textAlign: "right" }}>경기</span>
        </div>
        {clubs.map((c, i) => {
          const lev = c.team === "Bayer Leverkusen";
          return (
            <div key={c.team} style={{ display: "grid", gridTemplateColumns: "34px 1fr 220px 120px 70px", gap: 14, alignItems: "center", padding: "13px 20px", borderBottom: "1px solid var(--line2)", background: lev ? "var(--accent-tint)" : "transparent" }}>
              <span className="num" style={{ fontSize: 14, color: "var(--faint)" }}>{i + 1}</span>
              <span style={{ fontSize: 14.5, fontWeight: 600, color: "var(--ink)", whiteSpace: "nowrap" }}>{c.team}</span>
              <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                <div style={{ flex: 1, height: 9, background: "var(--track)", borderRadius: 99 }}>
                  <div style={{ height: 9, borderRadius: 99, width: (c.xt_per_match / maxXt * 100).toFixed(1) + "%", background: "var(--accent)" }} />
                </div>
                <span className="num" style={{ fontSize: 13, fontWeight: 600, color: "var(--accent)", width: 42, textAlign: "right" }}>{fmt(c.xt_per_match)}</span>
              </div>
              <span style={{ fontSize: 12.5, color: "var(--muted)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{c.top}</span>
              <span className="num" style={{ fontSize: 13, color: "var(--faint)", textAlign: "right" }}>{c.matches}</span>
            </div>
          );
        })}
      </section>
      <p style={{ fontSize: 12.5, color: "var(--faint)", margin: "16px 4px 0", maxWidth: 820, lineHeight: 1.6 }}>
        구단 비교는 <strong>경기당 xT(위협 생성)</strong> 기준 — VAEP는 레버쿠젠 외 팀의 표본(각 1경기)이 없어 사용 못 함. 레버쿠젠(34경기) 외 상대팀은 1경기 표본이라 값이 불안정하다. 스쿼드 평균 맥락 보정은 전 구단 시즌 데이터가 갖춰지면 추가 예정.
      </p>
    </div>
  );
}
