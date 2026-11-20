import React, { useEffect, useState } from "react";
import { listScans, listMatches, reportUrl, targetLabel } from "../api.js";
import { GRADE_CLASS, Empty, Spinner, Icon, useToast } from "../ui.jsx";

const fmt = (iso) => (iso ? new Date(iso).toLocaleString("fr-FR") : "—");

export default function HistoryView() {
  const toast = useToast();
  const [scans, setScans] = useState([]);
  const [matches, setMatches] = useState([]);
  const [busy, setBusy] = useState(false);

  useEffect(() => { refresh(false); }, []);
  const refresh = async (notify = true) => {
    setBusy(true);
    try {
      const [s, m] = await Promise.all([listScans(), listMatches()]);
      setScans(s); setMatches(m);
      if (notify) toast("ok", "Historique à jour");
    } catch { if (notify) toast("error", "Rafraîchissement impossible"); }
    finally { setBusy(false); }
  };

  const empty = scans.length === 0 && matches.length === 0;

  return (
    <div className="single">
      <div className="card rise" style={{ "--i": 0 }}>
        <div className="row-between">
          <h2>Historique</h2>
          <button className="btn-ghost" disabled={busy} onClick={() => refresh(true)}>
            {busy ? <Spinner /> : <Icon name="history" size={15} />} Rafraîchir
          </button>
        </div>
      </div>

      {empty && <div className="card rise" style={{ "--i": 1 }}><Empty>Aucun scan ni match pour cette session. Lance un scan ou un duel.</Empty></div>}

      {scans.length > 0 && (
        <div className="card rise" style={{ "--i": 1 }}>
          <h3>Scans</h3>
          <table>
            <thead><tr><th scope="col">Modèle</th><th scope="col">Score</th><th scope="col">Vuln.</th><th scope="col">Statut</th><th scope="col">Date</th><th scope="col"></th></tr></thead>
            <tbody>
              {scans.map((s) => (
                <tr key={s.scan_id}>
                  <th scope="row" className="mono">{targetLabel(s.target)}</th>
                  <td><span className={`badge ${GRADE_CLASS[s.grade] || ""}`}>{s.score ?? "…"}{s.grade ? ` ${s.grade}` : ""}</span></td>
                  <td>{s.vulnerabilities ?? "—"}</td>
                  <td className="muted">{s.status}</td>
                  <td className="muted small">{fmt(s.started_at)}</td>
                  <td>{s.status === "done" && <a className="link" href={reportUrl(s.scan_id)} target="_blank" rel="noreferrer"><Icon name="download" size={14} /> Rapport</a>}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {matches.length > 0 && (
        <div className="card rise" style={{ "--i": 2 }}>
          <h3>Matchs d'arène</h3>
          <table>
            <thead><tr><th scope="col">Attaquant</th><th scope="col">Cible</th><th scope="col">Vainqueur</th><th scope="col">Tours</th><th scope="col">Date</th></tr></thead>
            <tbody>
              {matches.map((m) => (
                <tr key={m.match_id}>
                  <th scope="row" className="mono small">{targetLabel(m.attacker)}</th>
                  <td className="mono small">{targetLabel(m.target)}</td>
                  <td className={m.winner === "attacker" ? "g-bad" : "g-ok"}>
                    {m.winner === "attacker" ? "Attaquant" : m.winner === "defender" ? "Cible" : m.status}
                  </td>
                  <td>{m.rounds_played}/{m.max_rounds}</td>
                  <td className="muted small">{fmt(m.started_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
