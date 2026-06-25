import { useMemo } from "react";
import * as d3 from "d3";

// StatsBomb 피치 규격 (가로 120 x 세로 80), 공격 방향 = 오른쪽(x 증가)
const W = 120;
const H = 80;

function PitchMarkings() {
  const line = { stroke: "#3a4351", strokeWidth: 0.4, fill: "none" };
  return (
    <g>
      <rect x={0} y={0} width={W} height={H} fill="#0d1117" stroke="#3a4351" strokeWidth={0.5} />
      <line x1={W / 2} y1={0} x2={W / 2} y2={H} {...line} />
      <circle cx={W / 2} cy={H / 2} r={10} {...line} />
      <circle cx={W / 2} cy={H / 2} r={0.6} fill="#3a4351" />
      {/* 양쪽 페널티 박스 */}
      <rect x={0} y={18} width={18} height={44} {...line} />
      <rect x={W - 18} y={18} width={18} height={44} {...line} />
      {/* 골 에어리어 */}
      <rect x={0} y={30} width={6} height={20} {...line} />
      <rect x={W - 6} y={30} width={6} height={20} {...line} />
      {/* 골대 */}
      <rect x={-0.8} y={36} width={0.8} height={8} {...line} />
      <rect x={W} y={36} width={0.8} height={8} {...line} />
    </g>
  );
}

export default function Pitch({ data }) {
  const actions = data?.actions ?? [];

  const color = useMemo(() => {
    const max = d3.max(actions, (a) => a.xt) ?? 1;
    const min = d3.min(actions, (a) => a.xt) ?? 0;
    return d3.scaleSequential(d3.interpolateViridis).domain([min, max]);
  }, [actions]);

  return (
    <div className="pitch-wrap">
      <svg viewBox={`-2 -2 ${W + 4} ${H + 4}`} className="pitch-svg">
        <defs>
          <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5"
            markerWidth="5" markerHeight="5" orient="auto-start-reverse">
            <path d="M 0 0 L 10 5 L 0 10 z" fill="context-stroke" />
          </marker>
        </defs>
        <PitchMarkings />
        <g>
          {actions.map((a, i) => (
            <line
              key={i}
              x1={a.x0} y1={a.y0} x2={a.x1} y2={a.y1}
              stroke={color(a.xt)}
              strokeWidth={0.25 + (a.xt / (color.domain()[1] || 1)) * 0.55}
              strokeOpacity={0.6}
              markerEnd="url(#arrow)"
            />
          ))}
        </g>
      </svg>
      {data && (
        <div className="pitch-caption">
          <strong>{data.player}</strong> · {data.team} · 위협 생성 행동 {data.count}개
          <span className="hint"> (오른쪽으로 공격 · 색·굵기 = xT 증가량)</span>
        </div>
      )}
    </div>
  );
}
