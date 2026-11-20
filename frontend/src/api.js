// Client de l'API AegisLLM.
// En dev (Vite sur :5173) on tape l'API sur :8000 ; servi par FastAPI, on reste en
// même origine (chemins relatifs) → une seule commande suffit à tout lancer.
const DEV = typeof location !== "undefined" && location.port === "5173";
export const API_BASE = DEV ? "http://127.0.0.1:8000" : "";
const WS_BASE = DEV
  ? "ws://127.0.0.1:8000"
  : `${location.protocol === "https:" ? "wss:" : "ws:"}//${location.host}`;

async function j(path, opts) {
  const r = await fetch(`${API_BASE}${path}`, opts);
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
  return r.json();
}
const post = (path, body) =>
  j(path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });

// --- commun ---
export const getHealth = () => j("/api/health");
export const getModels = () => j("/api/models");
export const getCategories = () => j("/api/categories");
export const getProbes = () => j("/api/probes");
export const reportUrl = (id) => `${API_BASE}/api/scans/${id}/report.html`;

const TARGET_LABELS = {
  "demo:vulnerable": "Démo — modèle vulnérable",
  "demo:hardened": "Démo — modèle durci",
};
export const targetLabel = (v) => TARGET_LABELS[v] || v;

// --- chat / test manuel ---
export const sendChat = (body) => post("/api/chat", body);

// --- scans ---
export const listScans = () => j("/api/scans");
export const getScan = (id) => j(`/api/scans/${id}`);
export const startScan = (body) => post("/api/scans", body);
export function openScanSocket(id, onEvent, onClose) {
  const ws = new WebSocket(`${WS_BASE}/api/scans/${id}/ws`);
  ws.onmessage = (e) => onEvent(JSON.parse(e.data));
  if (onClose) { ws.onerror = onClose; ws.onclose = onClose; }
  return ws;
}

// --- arène ---
export const listMatches = () => j("/api/arena");
export const getMatch = (id) => j(`/api/arena/${id}`);
export const getLeaderboard = () => j("/api/arena/leaderboard");
export const startMatch = (body) => post("/api/arena", body);
export function openMatchSocket(id, onEvent, onClose) {
  const ws = new WebSocket(`${WS_BASE}/api/arena/${id}/ws`);
  ws.onmessage = (e) => onEvent(JSON.parse(e.data));
  if (onClose) { ws.onerror = onClose; ws.onclose = onClose; }
  return ws;
}
