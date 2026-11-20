import React, { useEffect, useRef, useState } from "react";
import { startScan, openScanSocket, listScans, getScan, reportUrl, targetLabel } from "../api.js";
import { Gauge, Pct, Empty, Field, GRADE_CLASS, Spinner, Icon, useToast } from "../ui.jsx";
import { computeScore, gradeFor, byCategory, severityCounts } from "../score.js";

const SEV_COLOR = { critical: "#b42318", high: "#d4574c", medium: "#a16207", low: "#c6a94e" };
const asrClass = (a) => (a >= 0.5 ? "g-bad-bg" : a > 0 ? "g-warn-bg" : "g-ok-bg");

function verdict(r) {
  if (r.error) return ["! err", "g-warn", "Erreur"];
  if (r.success) return ["✗ vuln", "g-bad", "Vulnérabilité"];
  return ["✓ tenu", "g-ok", "Tenu"];
}

function TestItem({ r }) {
  const [tag, cls, label] = verdict(r);
  return (
    <details className="test">
      <summary>
        <span className={`t-verdict ${cls}`}>{tag}</span>
        <span className="mono tag">{r.owasp}</span>
        <span className="t-title">{r.title}</span>
        <span className="muted t-mut">{r.mutation}</span>
        <span className="muted small t-meta">
          {r.latency_ms ? `${Math.round(r.latency_ms)} ms` : ""}{r.completion_tokens ? ` · ${r.completion_tokens} tok` : ""}
        </span>
      </summary>
      <div className={`why ${cls}`}>{label} — {r.rationale || r.error || "—"}</div>
      <div className="lbl">Prompt envoyé</div>
      <pre>{r.prompt_sent || "—"}</pre>
      <div className="lbl">Réponse du modèle</div>
      <pre>{r.response_text || "—"}</pre>
    </details>
  );
}

function CatBars({ cats }) {
  return (
    <div className="bars">
      {cats.map((c) => (
        <div className="barrow" key={c.owasp}>
          <div className="barlabel mono">{c.owasp}</div>
          <div className="bartrack"><div className={`barfill ${asrClass(c.asr)}`} style={{ width: `${Math.round(c.asr * 100)}%` }} /></div>
          <div className="barval">{c.successes}/{c.attempts} · {Math.round(c.asr * 100)}%</div>
        </div>
      ))}
    </div>
  );
}

function SeverityBar({ results }) {
  const counts = severityCounts(results);
  const total = Object.values(counts).reduce((a, b) => a + b, 0);
  if (!total) return <div className="g-ok">Aucune vulnérabilité — le modèle a tout tenu.</div>;
  return (
    <>
      <div className="sevbar">
        {["critical", "high", "medium", "low"].map((s) => counts[s] > 0 && (
          <div key={s} style={{ flex: counts[s], background: SEV_COLOR[s] }} title={`${s}: ${counts[s]}`} />
        ))}
      </div>
      <div className="sevlegend">
        {["critical", "high", "medium", "low"].map((s) => (
          <span key={s}><i style={{ background: SEV_COLOR[s] }} />{s} · {counts[s]}</span>
        ))}
      </div>
    </>
  );
}

export default function ScanView({ models, cats }) {
  const toast = useToast();
  const [target, setTarget] = useState("");
  const [judge, setJudge] = useState("");
  const [picked, setPicked] = useState(new Set());
  const [recent, setRecent] = useState([]);
  const [status, setStatus] = useState("idle");
  const [total, setTotal] = useState(0);
  const [done, setDone] = useState(0);
  const [log, setLog] = useState([]);           // tous les résultats reçus en direct
  const [report, setReport] = useState(null);
  const [scanId, setScanId] = useState(null);
  const [filter, setFilter] = useState("all");
  const [err, setErr] = useState("");
  const wsRef = useRef(null);
  const doneRef = useRef(false);
  const seqRef = useRef(0);

  useEffect(() => { if (models[0] && !target) setTarget(models[0]); }, [models, target]);
  useEffect(() => { refresh(); return () => closeWs(); }, []);
  const refresh = () => listScans().then(setRecent).catch(() => {});

  const closeWs = () => {
    const ws = wsRef.current; wsRef.current = null;
    if (ws) { ws.onclose = null; ws.onerror = null; try { ws.close(); } catch {} }
  };
  const handleClose = () => {
    if (doneRef.current) return;
    setStatus("error"); setErr("Connexion au serveur interrompue");
    toast("error", "Connexion au serveur interrompue");
  };

  const toggle = (c) => { const n = new Set(picked); n.has(c) ? n.delete(c) : n.add(c); setPicked(n); };

  const launch = async () => {
    setErr(""); setReport(null); setLog([]); setDone(0); setStatus("running"); setFilter("all");
    doneRef.current = false;
    try {
      const { scan_id, total } = await startScan({ target, only: [...picked], judge: judge || null });
      setTotal(total); setScanId(scan_id);
      closeWs();
      wsRef.current = openScanSocket(scan_id, onEvent, handleClose);
    } catch (e) { setErr(String(e)); setStatus("error"); toast("error", "Échec du lancement du scan"); }
  };

  const onEvent = (ev) => {
    if (ev.type === "started") setTotal(ev.total);
    else if (ev.type === "progress") {
      setDone(ev.done);
      setLog((l) => [{ ...ev.result, _k: ++seqRef.current }, ...l]);
    } else if (ev.type === "done") {
      doneRef.current = true;
      setStatus("done"); setReport(ev.report); refresh();
      const nv = (ev.report?.results || []).filter((r) => r.success).length;
      toast(nv ? "info" : "ok", `Scan terminé — ${ev.report?.score}/100 (${ev.report?.grade}) · ${nv} vuln.`);
    } else if (ev.type === "error") {
      doneRef.current = true; setStatus("error"); setErr(ev.error); toast("error", ev.error);
    }
  };

  const load = async (id) => {
    closeWs(); doneRef.current = true;
    try {
      const d = await getScan(id);
      if (d.report) { setReport(d.report); setScanId(id); setStatus("done"); setLog([]); setFilter("all"); }
      else toast("info", "Scan en cours — résultat indisponible");
    } catch { toast("error", "Impossible de charger ce scan"); }
  };

  const pct = total ? Math.round((done / total) * 100) : 0;
  // live metrics
  const liveScore = computeScore(log);
  const liveVuln = log.filter((r) => r.success).length;
  const liveTokens = log.reduce((a, r) => a + (r.completion_tokens || 0), 0);
  const liveLat = log.length ? Math.round(log.reduce((a, r) => a + (r.latency_ms || 0), 0) / log.length) : 0;
  const liveCats = byCategory(log);
  // report data
  const results = report?.results || [];
  const categories = report?.categories || [];
  const vulns = results.filter((r) => r.success);
  const shown = filter === "vuln" ? vulns : filter === "ok" ? results.filter((r) => !r.success) : results;

  return (
    <div className="two-col">
      <section className="card rise" style={{ "--i": 0 }}>
        <h2>Nouveau scan</h2>
        <Field label="Modèle cible">
          <select value={target} onChange={(e) => setTarget(e.target.value)}>
            {models.map((m) => <option key={m} value={m}>{targetLabel(m)}</option>)}
          </select>
        </Field>
        <Field label="Catégories" hint="(aucune = toutes)">
          <div className="chips">
            {cats.map((c) => (
              <button key={c} className={`chip ${picked.has(c) ? "on" : ""}`} aria-pressed={picked.has(c)} onClick={() => toggle(c)}>{c}</button>
            ))}
          </div>
        </Field>
        <Field label="Juge LLM" hint="(optionnel)">
          <select value={judge} onChange={(e) => setJudge(e.target.value)}>
            <option value="">— aucun —</option>
            {models.map((m) => <option key={m} value={m}>{targetLabel(m)}</option>)}
          </select>
        </Field>
        <button className="btn" disabled={status === "running" || !target} onClick={launch}>
          {status === "running" ? <><Spinner /> Scan en cours…</> : <><Icon name="scan" size={16} /> Lancer le scan</>}
        </button>
        {err && <div className="err">{err}</div>}

        <h3>Scans récents</h3>
        <ul className="recent">
          {recent.length === 0 && <li className="muted">aucun</li>}
          {recent.map((s) => (
            <li key={s.scan_id}>
              <button className="recent-row" onClick={() => load(s.scan_id)} aria-label={`Charger le scan ${s.target}`}>
                <span className="mono">{targetLabel(s.target)}</span>
                <span className={`badge ${GRADE_CLASS[s.grade] || ""}`}>{s.score ?? "…"}{s.grade ? ` ${s.grade}` : ""}</span>
              </button>
            </li>
          ))}
        </ul>
      </section>

      <section className="card rise" style={{ "--i": 1 }}>
        {status === "running" && (
          <>
            <h2>En direct</h2>
            <div className="metrics">
              <div className="metric"><div className="m-v">{done}/{total}</div><div className="m-l">attaques</div></div>
              <div className="metric"><div className="m-v g-bad">{liveVuln}</div><div className="m-l">vulnérabilités</div></div>
              <div className="metric"><div className={`m-v ${GRADE_CLASS[gradeFor(liveScore)]}`}>{liveScore}</div><div className="m-l">score provisoire</div></div>
              <div className="metric"><div className="m-v">{liveTokens}</div><div className="m-l">jetons générés</div></div>
              <div className="metric"><div className="m-v">{liveLat}<span className="u">ms</span></div><div className="m-l">latence moy.</div></div>
            </div>
            <div className="progress" role="progressbar" aria-valuemin={0} aria-valuemax={100} aria-valuenow={pct} aria-label="Progression du scan">
              <div className="bar" style={{ width: `${pct}%` }} />
            </div>

            {liveCats.length > 0 && <><h3>Par catégorie (en cours)</h3><CatBars cats={liveCats} /></>}

            <h3>Flux des tests — ce que « pense » le modèle</h3>
            <div className="feed">
              {log.map((r) => <div className="log-in" key={r._k}><TestItem r={r} /></div>)}
            </div>
          </>
        )}

        {status === "done" && report && (
          <>
            <div className="score-row">
              <Gauge score={report.score} grade={report.grade} />
              <div style={{ flex: 1, minWidth: 0 }}>
                <div className="mono big">{targetLabel(report.target)}</div>
                <div className="muted spc">{results.length} tests · <strong className="g-bad">{vulns.length}</strong> vulnérabilités · {report.judge ? `juge ${report.judge}` : "sans juge"}</div>
                {scanId && (
                  <a className="btn-ghost inline" href={reportUrl(scanId)} target="_blank" rel="noreferrer">
                    <Icon name="download" size={15} /> Exporter le rapport (PDF)
                  </a>
                )}
              </div>
            </div>

            <h3>Gravité des vulnérabilités</h3>
            <SeverityBar results={results} />

            <h3>Taux de réussite des attaques (ASR) par catégorie</h3>
            <CatBars cats={byCategory(results).length ? byCategory(results) : categories.map((c) => ({ ...c }))} />

            <div className="row-between" style={{ marginTop: 26 }}>
              <h3 style={{ margin: 0 }}>Détail des tests</h3>
              <div className="seg">
                <button className={filter === "all" ? "on" : ""} onClick={() => setFilter("all")}>Tous · {results.length}</button>
                <button className={filter === "vuln" ? "on" : ""} onClick={() => setFilter("vuln")}>Vuln. · {vulns.length}</button>
                <button className={filter === "ok" ? "on" : ""} onClick={() => setFilter("ok")}>Tenus · {results.length - vulns.length}</button>
              </div>
            </div>
            <div className="feed">
              {shown.map((r, i) => <TestItem r={r} key={i} />)}
            </div>
          </>
        )}

        {status === "idle" && <Empty>Choisis un modèle et lance un scan pour voir son score, et suivre en direct chaque attaque et la réponse du modèle.</Empty>}
        {status === "error" && <div className="err">Erreur : {err}</div>}
      </section>
    </div>
  );
}
