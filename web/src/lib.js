// 공통 헬퍼. (이전의 '예시 모델'은 실데이터 API로 대체되어 제거됨)

export const API = "/api";

export async function getJSON(path) {
  const r = await fetch(API + path);
  if (!r.ok) throw new Error(`${r.status} ${path}`);
  return r.json();
}

export const fmt = (v, d = 2) => (v ?? 0).toFixed(d);

// 두 지표(vaep/xt)로 각각 순위를 매겨 각 선수의 rank를 부여하고,
// 선택 지표 기준으로 정렬해 반환. delta = xtRank - vaepRank
// (양수 = VAEP에서 더 높이 평가됨 = 수비·연결 기여형).
export function rankPlayers(players, metric) {
  const byVaep = [...players].sort((a, b) => b.vaep_p90 - a.vaep_p90);
  byVaep.forEach((p, i) => (p.vaepRank = i + 1));
  const byXt = [...players].sort((a, b) => b.xt_per_match - a.xt_per_match);
  byXt.forEach((p, i) => (p.xtRank = i + 1));
  const key = metric === "xt" ? "xt_per_match" : "vaep_p90";
  return [...players].sort((a, b) => b[key] - a[key]);
}
