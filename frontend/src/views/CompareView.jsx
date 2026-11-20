import React, { useEffect, useRef, useState } from "react";
import { startScan, listScans, getScan, targetLabel } from "../api.js";
import { Empty, Field, Pct, GRADE_CLASS, Spinner, Icon, useToast } from "../ui.jsx";

const BAR_CLASS = (s) => (s >= 75 ? "g-ok" : s >= 40 ? "g-warn" : "g-bad");

export default function CompareView({ models, cats }) {
  const toast = useToast();
  const [chosen, setChosen] = useState(new Set());
  const [picked, setPicked] = useState(new Set());
  const [rows, setRows] = useState([]); // {target, scan_id, status, score, grade, report}
  const [running, setRunning] = useState(false);
  const timer = useRef(null);

  useEffect(() => () => clearInterval(timer.current), []);

  const toggleModel = (m) => { const n = new Set(chosen); n.has(m) ? n.delete(m) : n.add(m); setChosen(n); };
  const toggleCat = (c) => { const n = new Set(picked); n.has(c) ? n.delete(c) : n.add(c); setPicked(n); };

  const compare = async () => {
    const targets = [...chosen];
    if (targets.length < 2) return;
    setRunning(true); setRows([]);
    try {
      const started = [];
      for (const t of targets) {
        const { scan_id } = await startScan({ target: t, only: [...picked] });
        started.push({ target: t, scan_id, status: "running", score: null, grade: null, report: null });
      }
      setRows(started);
      clearInterval(timer.current);
      timer.current = setInterval(() => poll(started.map((s) => s.scan_id)), 2500);
    } catch (e) {
      clearInterval(timer.current); setRunning(false);
      toast("error", "Échec du lancement de la comparaison");
    }
  };

  const poll = async (ids) => {
    try {
      const all = await listScans();
      const byId = Object.fromEntries(all.map((s) => [s.scan_id, s]));
      const updated = await Promise.all(ids.map(async (id) => {
        const s = byId[id];
        if (!s) return { target: "?", scan_id: id, status: "running", score: null, grade: null, report: null };
        let report = null;
        if (s.status === "done") report = (await getScan(id)).report;
        return { target: s.target, scan_id: id, status: s.status, score: s.score, grade: s.grade, report };
      }));
      setRows(updated);
      if (updated.every((r) => r.status !== "running")) {
        clearInterval(timer.current); setRunning(false);
        toast("ok", "Comparaison terminée");
      }
    } catch {
      /* transient — on réessaiera au prochain tick */
    }
  };

  const allCats = () => {
    const set = new Set();
    rows.forEach((r) => (r.report?.categories || []).forEach((c) => set.add(c.owasp)));
    return [...set].sort();
  };
  const asr = (r, owasp) => r.report?.categories.find((c) => c.owasp === owasp)?.asr;

  return (
    <div className="two-col">
      <section className="card rise" style={{ "--i": 0 }}>
        <h2>Comparer des modèles</h2>
        <Field label="Modèles" hint="(2 ou plus)">
          <div className="chips col">
            {models.map((m) => (
              <button key={m} className={`chip wide ${chosen.has(m) ? "on" : ""}`}
                aria-pressed={chosen.has(m)} onClick={() => toggleModel(m)}>{targetLabel(m)}</button>
            ))}
          </div>
        </Field>
        <Field label="Catégories" hint="(aucune = toutes)">
          <div className="chips">
            {cats.map((c) => (
              <button key={c} className={`chip ${picked.has(c) ? "on" : ""}`}
                aria-pressed={picked.has(c)} onClick={() => toggleCat(c)}>{c}</button>
            ))}
          </div>
        </Field>
        <button className="btn" disabled={running || chosen.size < 2} onClick={compare}>
          {running ? <><Spinner /> Comparaison en cours…</> : <><Icon name="compare" size={16} /> Comparer</>}
        </button>
      </section>

      <section className="card rise" style={{ "--i": 1 }}>
        {rows.length === 0 ? (
          <Empty>Sélectionne au moins deux modèles pour comparer leur robustesse.</Empty>
        ) : (
          <>
            <h2>Scores</h2>
            <div className="bars">
              {rows.map((r) => (
                <div className="barrow" key={r.scan_id}>
                  <div className="barlabel mono">{targetLabel(r.target)}</div>
                  <div className="bartrack">
                    <div className={`barfill ${r.score != null ? BAR_CLASS(r.score) + "-bg" : ""}`}
                      style={{ width: `${r.score ?? 0}%` }} />
                  </div>
                  <div className="barval">{r.status === "done" ? `${r.score} ${r.grade}` : "…"}</div>
                </div>
              ))}
            </div>

            {rows.every((r) => r.status === "done") && (
              <>
                <h3>ASR par catégorie</h3>
                <table>
                  <thead><tr><th scope="col">Catégorie</th>{rows.map((r) => <th scope="col" key={r.scan_id} className="mono small">{targetLabel(r.target)}</th>)}</tr></thead>
                  <tbody>
                    {allCats().map((owasp) => (
                      <tr key={owasp}>
                        <th scope="row" className="mono">{owasp}</th>
                        {rows.map((r) => {
                          const v = asr(r, owasp);
                          return <td key={r.scan_id}>{v == null ? "—" : <Pct v={v} />}</td>;
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </>
            )}
          </>
        )}
      </section>
    </div>
  );
}
