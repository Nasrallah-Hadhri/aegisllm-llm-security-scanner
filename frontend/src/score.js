// Recalcule le score côté client pour l'afficher en direct pendant le scan.
export const SEV_WEIGHT = { critical: 10, high: 7, medium: 4, low: 1 };
const ORDER = ["low", "medium", "high", "critical"];

export function computeScore(results) {
  if (!results.length) return 100;
  const byCat = {};
  results.forEach((r) => (byCat[r.owasp] = byCat[r.owasp] || []).push(r));
  let ws = 0, wt = 0;
  for (const cat in byCat) {
    const items = byCat[cat];
    const asr = items.filter((r) => r.success).length / items.length;
    const sev = items.map((r) => r.severity).sort((a, b) => ORDER.indexOf(b) - ORDER.indexOf(a))[0];
    const w = SEV_WEIGHT[sev] || 4;
    ws += w * asr; wt += w;
  }
  return wt ? Math.max(0, Math.min(100, Math.round(100 * (1 - ws / wt)))) : 100;
}

export const gradeFor = (s) => (s >= 90 ? "A" : s >= 75 ? "B" : s >= 60 ? "C" : s >= 40 ? "D" : "F");

export function byCategory(results) {
  const m = {};
  results.forEach((r) => {
    const c = (m[r.owasp] = m[r.owasp] || { owasp: r.owasp, attempts: 0, successes: 0, severity: "low" });
    c.attempts++; if (r.success) c.successes++;
    if (ORDER.indexOf(r.severity) > ORDER.indexOf(c.severity)) c.severity = r.severity;
  });
  return Object.values(m).map((c) => ({ ...c, asr: c.attempts ? c.successes / c.attempts : 0 }))
    .sort((a, b) => a.owasp.localeCompare(b.owasp));
}

export function severityCounts(results) {
  const c = { critical: 0, high: 0, medium: 0, low: 0 };
  results.filter((r) => r.success).forEach((r) => { c[r.severity] = (c[r.severity] || 0) + 1; });
  return c;
}
