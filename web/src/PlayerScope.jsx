import { useEffect, useMemo, useState } from "react";
import Pitch from "./Pitch.jsx";
import { getJSON, rankPlayers, fmt } from "./lib.js";

export default function PlayerScope({ players, metric, selected, setSelected }) {
  const [detail, setDetail] = useState(null);
  const [actions, setActions] = useState(null);

  const ranked = useMemo(() => rankPlayers(players, metric), [players, metric]);
  const valKey = metric === "xt" ? "xt_per_match" : "vaep_p90";
  const otherLabel = metric === "xt" ? "vs VAEP" : "vs xT";

  useEffect(() => {
    if (!selected) return;
    setDetail(null); setActions(null);
    getJSON(`/players/${encodeURIComponent(selected)}`).then(setDetail).catch(() => setDetail(null));
    getJSON(`/players/${encodeURIComponent(selected)}/xt-actions?top=200`).then(setActions).catch(() => setActions(null));
  }, [selected]);

  const sel = ranked.find((p) => p.player === selected) || ranked[0];

  return (
    <div style={{ display: "grid", gridTemplateColumns: "380px 1fr", gap: 24, padding: "24px 32px 48px", alignItems: "start" }}>
      <section style={{ background: "var(--panel)", border: "1px solid var(--line)", borderRadius: 12, overflow: "hidden" }}>
        <div style={{ display: "grid", gridTemplateColumns: "26px 1fr auto 52px", gap: 10, padding: "12px 14px", borderBottom: "1px solid var(--line)", fontSize: 10.5, fontWeight: 600, letterSpacing: ".08em", textTransform: "uppercase", color: "var(--faint)", background: "var(--panel2)" }}>
          <span>#</span><span>선수</span>
          <span style={{ textAlign: "right" }}>{metric === "xt" ? "xT" : "VAEP"}</span>
          <span style={{ textAlign: "right" }}>{otherLabel}</span>
        </div>
        {ranked.map((p, i) => {
          const active = p.player === selected;
          const d = metric === "xt" ? p.vaepRank - p.xtRank : p.xtRank - p.vaepRank;
          const deltaText = d > 0 ? "▲" + d : d < 0 ? "▼" + -d : "–";
          const deltaColor = d > 0 ? "var(--accent)" : d < 0 ? "var(--amber)" : "var(--bar-muted)";
          return (
            <div key={p.player} onClick={() => setSelected(p.player)}
              style={{ display: "grid", gridTemplateColumns: "26px 1fr auto 52px", gap: 10, alignItems: "center", padding: "9px 14px", cursor: "pointer", borderBottom: "1px solid var(--line2)", background: active ? "var(--accent-tint)" : "transparent" }}>
              <span className="num" style={{ fontSize: 13, color: "var(--faint)" }}>{i + 1}</span>
              <div>
                <div style={{ fontSize: 13.5, color: "var(--ink)", fontWeight: 500 }}>{p.player}</div>
                <div style={{ fontSize: 11, color: "var(--faint)", marginTop: 2 }}>{p.pos} · {p.team}</div>
              </div>
              <span className="num" style={{ fontSize: 14, fontWeight: 600, color: "var(--ink)", textAlign: "right" }}>{fmt(p[valKey])}</span>
              <span className="num" style={{ fontSize: 12, textAlign: "right", color: deltaColor }} title="다른 지표 기준 순위 대비 변동">{deltaText}</span>
            </div>
          );
        })}
      </section>

      <section style={{ background: "var(--panel)", border: "1px solid var(--line)", borderRadius: 12, overflow: "hidden" }}>
        <div style={{ height: 4, background: "var(--accent)" }} />
        {sel && <DetailBody sel={sel} detail={detail} actions={actions} />}
      </section>
    </div>
  );
}

function Label({ children, note }) {
  return (
    <div style={{ display: "flex", gap: 8, alignItems: "center", fontSize: 11, fontWeight: 600, letterSpacing: ".12em", textTransform: "uppercase", color: "var(--ink2)", marginBottom: 14 }}>
      {children}{note && <span style={{ fontSize: 10, fontWeight: 500, letterSpacing: 0, textTransform: "none", color: "var(--faint)" }}>{note}</span>}
    </div>
  );
}

function DetailBody({ sel, detail, actions }) {
  const tiers = detail?.tiers ?? [];
  const mix = detail?.mix ?? [];
  const trend = detail?.trend ?? [];
  const pct = detail?.percentiles ?? [];
  const tierMax = Math.max(0.5, ...tiers.map((t) => t.vaep_p90 ?? 0));
  const trendMax = Math.max(0.3, ...trend.map((t) => t.xt));

  const strong = tiers.find((t) => t.tier === "강")?.vaep_p90;
  const weak = tiers.find((t) => t.tier === "약")?.vaep_p90;

  return (
    <div style={{ padding: "28px 30px 30px" }}>
      {/* header */}
      <div style={{ display: "grid", gridTemplateColumns: "96px 1fr auto", gap: 22, alignItems: "center" }}>
        <div style={{ width: 96, height: 118, borderRadius: 4, backgroundImage: "repeating-linear-gradient(135deg,var(--photo1) 0 8px,var(--photo2) 8px 16px)", border: "1px solid var(--line)", display: "flex", alignItems: "flex-end", justifyContent: "center", paddingBottom: 8 }}>
          <span className="mono" style={{ fontSize: 9, color: "var(--faint2)" }}>PHOTO</span>
        </div>
        <div>
          <div className="serif" style={{ fontWeight: 600, fontSize: 27, lineHeight: 1.05, color: "var(--ink)" }}>{sel.player}</div>
          <div style={{ fontSize: 13, color: "var(--muted)", marginTop: 7 }}>
            {detail ? `${detail.posKo} · ${detail.minutes.toLocaleString()}분 · ${detail.matches}경기` : "…"}
          </div>
          <div style={{ display: "flex", gap: 7, marginTop: 13 }}>
            {[sel.team, detail?.posKo ?? sel.pos].map((c, i) => (
              <span key={i} style={{ fontSize: 11, color: "var(--muted)", background: "var(--chip)", border: "1px solid var(--line)", borderRadius: 99, padding: "4px 10px" }}>{c}</span>
            ))}
          </div>
        </div>
        <div style={{ textAlign: "right", paddingLeft: 22, borderLeft: "1px solid var(--line)" }}>
          <div style={{ fontSize: 10.5, fontWeight: 600, letterSpacing: ".1em", textTransform: "uppercase", color: "var(--faint)" }}>VAEP / 90 · 교차검증</div>
          <div className="num serif" style={{ fontWeight: 500, fontSize: 50, lineHeight: 1, color: "var(--accent)", marginTop: 4 }}>{fmt(sel.vaep_p90)}</div>
          <div className="num" style={{ fontSize: 12, color: "var(--faint)", marginTop: 6 }}>xT/경기 {fmt(sel.xt_per_match)}</div>
        </div>
      </div>

      {/* 상대 수준별 VAEP (실측, 워터폴 대체) */}
      <div style={{ marginTop: 26, background: "var(--panel2)", border: "1px solid var(--line3)", borderRadius: 8, padding: "22px 24px 18px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 16 }}>
          <span style={{ fontSize: 11, fontWeight: 600, letterSpacing: ".12em", textTransform: "uppercase", color: "var(--ink2)" }}>상대 수준별 기여 (실측)</span>
          <span style={{ fontSize: 11, color: "var(--faint)" }}>VAEP/90 · 최종 순위 티어</span>
        </div>
        {tiers.map((t) => (
          <div key={t.tier} style={{ display: "grid", gridTemplateColumns: "92px 1fr 64px", alignItems: "center", gap: 14, height: 40 }}>
            <span style={{ fontSize: 13, color: "var(--ink)" }}>{t.tier}팀 <span style={{ color: "var(--faint2)", fontSize: 11 }}>{t.minutes}′</span></span>
            <div style={{ position: "relative", height: 24, background: "var(--track)", borderRadius: 3 }}>
              <div style={{ position: "absolute", top: 0, bottom: 0, left: 0, width: ((t.vaep_p90 ?? 0) / tierMax * 100).toFixed(1) + "%", background: t.tier === "강" ? "var(--accent)" : t.tier === "중" ? "var(--amber-bar)" : "var(--bar-muted)", borderRadius: 3 }} />
            </div>
            <span className="num" style={{ fontSize: 13.5, fontWeight: 600, color: "var(--ink3)", textAlign: "right" }}>{t.vaep_p90 == null ? "–" : fmt(t.vaep_p90)}</span>
          </div>
        ))}
        <p style={{ fontSize: 11, color: "var(--faint)", margin: "12px 2px 0", lineHeight: 1.55 }}>
          상대 강도는 분데스리가 23/24 최종 순위로 티어링한 실측값. <strong style={{ color: "var(--ink3)" }}>동료·리그 효과 분해</strong>는 다중 팀·리그 데이터가 필요해 아직 미구축.
        </p>
      </div>

      {/* pitch + side */}
      <div style={{ marginTop: 24 }}>
        <Label>위협 생성 패스맵</Label>
        <div style={{ display: "grid", gridTemplateColumns: "1.55fr 1fr", gap: 24, alignItems: "stretch" }}>
          <div style={{ background: "var(--panel2)", border: "1px solid var(--line3)", borderRadius: 8, padding: 14 }}>
            {actions ? <Pitch data={actions} /> : <div style={{ color: "var(--faint)", fontSize: 12, padding: 40, textAlign: "center" }}>패스맵 불러오는 중…</div>}
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
            <div style={{ background: "var(--panel2)", border: "1px solid var(--line3)", borderRadius: 8, padding: "16px 18px" }}>
              <div style={{ fontSize: 10.5, fontWeight: 600, letterSpacing: ".1em", textTransform: "uppercase", color: "var(--faint)", marginBottom: 12 }}>행동 구성</div>
              {mix.map((m) => (
                <div key={m.label} style={{ marginBottom: 10 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12.5, color: "var(--ink)", marginBottom: 4 }}>
                    <span>{m.label}</span><span className="num" style={{ color: "var(--muted)" }}>{m.pct}%</span>
                  </div>
                  <div style={{ height: 6, background: "var(--track)", borderRadius: 99 }}>
                    <div style={{ height: 6, borderRadius: 99, background: "var(--accent)", width: m.pct + "%" }} />
                  </div>
                </div>
              ))}
            </div>
            <div style={{ background: "var(--panel2)", border: "1px solid var(--line3)", borderRadius: 8, padding: "16px 18px", flex: 1 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 12 }}>
                <span style={{ fontSize: 10.5, fontWeight: 600, letterSpacing: ".1em", textTransform: "uppercase", color: "var(--faint)" }}>경기별 xT 추이</span>
                <span style={{ fontSize: 10.5, color: "var(--faint2)" }}>최근 {trend.length}경기</span>
              </div>
              <div style={{ display: "flex", alignItems: "flex-end", gap: 3, height: 64 }}>
                {trend.map((b, i) => (
                  <div key={i} title={`${b.date}: ${b.xt}`} style={{ flex: 1, borderRadius: "2px 2px 0 0", background: b.xt < trendMax * 0.4 ? "var(--bar-muted)" : "var(--accent)", height: Math.max(4, b.xt / trendMax * 100) + "%" }} />
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* percentiles + insight */}
      <div style={{ display: "grid", gridTemplateColumns: "1.4fr 1fr", gap: 28, marginTop: 24 }}>
        <div>
          <Label note="선수 풀 내 백분위 (실측)">기여 프로필</Label>
          {pct.map((m) => (
            <div key={m.label} style={{ marginBottom: 13 }}>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12.5, color: "var(--ink)", marginBottom: 5 }}>
                <span>{m.label}</span>
                <span className="num" style={{ fontWeight: 600, color: m.val >= 60 ? "var(--accent)" : "var(--faint)" }}>{m.val}</span>
              </div>
              <div style={{ height: 7, background: "var(--track)", borderRadius: 99 }}>
                <div style={{ height: 7, borderRadius: 99, width: m.val + "%", background: m.val >= 60 ? "var(--accent)" : "var(--bar-muted)" }} />
              </div>
            </div>
          ))}
        </div>
        <div style={{ background: "var(--panel2)", border: "1px solid var(--line3)", borderRadius: 8, padding: "18px 20px" }}>
          <div style={{ fontSize: 11, fontWeight: 600, letterSpacing: ".12em", textTransform: "uppercase", color: "var(--ink2)", marginBottom: 12 }}>맥락 인사이트</div>
          <p style={{ fontSize: 13, lineHeight: 1.6, color: "var(--ink2)", margin: 0 }}>
            {strong != null && weak != null ? (
              <>강팀 상대 VAEP/90 <strong>{fmt(strong)}</strong>, 약팀 상대 <strong>{fmt(weak)}</strong>.{" "}
                {strong >= weak
                  ? "강한 상대에도 기여가 유지·상승 — 맥락에 덜 휘둘리는 신호."
                  : "약팀 상대에 비해 강팀 상대 기여가 낮아, 상대 수준 의존도가 보인다."}</>
            ) : "상대 티어별 표본을 모으는 중."}
            {" "}xT 대비 VAEP 순위 변동({metric === "xt" ? sel.vaepRank - sel.xtRank : sel.xtRank - sel.vaepRank >= 0 ? "+" : ""}
            {metric === "xt" ? sel.vaepRank - sel.xtRank : sel.xtRank - sel.vaepRank})은 수비·연결 기여 비중을 시사한다.
          </p>
        </div>
      </div>
    </div>
  );
}
