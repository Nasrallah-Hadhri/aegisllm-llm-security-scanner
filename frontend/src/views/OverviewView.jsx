import React, { useEffect, useState } from "react";
import { getProbes, listScans } from "../api.js";
import { StatTile, Icon, GRADE_CLASS } from "../ui.jsx";

const ACTIONS = [
  ["scan", "scan", "Scanner un modèle", "Teste un LLM sur l'OWASP Top 10 et obtiens un score."],
  ["arena", "arena", "Lancer un duel", "Oppose deux IA dans l'arène de red teaming."],
  ["compare", "compare", "Comparer", "Classe plusieurs modèles côte à côte."],
];

export default function OverviewView({ models, cats, go }) {
  const [probes, setProbes] = useState(null);
  const [scans, setScans] = useState([]);

  useEffect(() => {
    getProbes().then((p) => setProbes(p.length)).catch(() => setProbes(0));
    listScans().then(setScans).catch(() => {});
  }, []);

  return (
    <div className="single">
      <div className="hero rise" style={{ "--i": 0 }}>
        <div className="hero-shield">⛊</div>
        <div>
          <h1 className="hero-title">AegisLLM</h1>
          <p className="hero-sub">Teste la robustesse de tes modèles de langage, mesure un score de sécurité et fais s'affronter deux IA — le tout depuis cette interface.</p>
          <button className="btn hero-btn" onClick={() => go("scan")}>
            <Icon name="scan" size={16} /> Démarrer un scan
          </button>
        </div>
      </div>

      <div className="stats">
        <StatTile icon="model" value={models.length} label="Modèles disponibles" i={0} />
        <StatTile icon="attack" value={probes ?? 0} label="Attaques prêtes" i={1} />
        <StatTile icon="category" value={cats.length} label="Catégories OWASP" i={2} />
        <StatTile icon="history" value={scans.length} label="Scans (session)" i={3} />
      </div>

      <div className="actions">
        {ACTIONS.map((a, i) => (
          <button className="action rise" style={{ "--i": i }} key={a[0]} onClick={() => go(a[0])}>
            <div className="action-ic"><Icon name={a[1]} size={22} /></div>
            <div className="action-t">{a[2]}</div>
            <div className="action-d">{a[3]}</div>
            <span className="action-go">→</span>
          </button>
        ))}
      </div>

      {scans.length > 0 && (
        <div className="card rise" style={{ "--i": 1 }}>
          <div className="row-between">
            <h3 style={{ margin: 0 }}>Derniers scans</h3>
            <button className="btn-ghost" onClick={() => go("history")}>Tout voir</button>
          </div>
          <table>
            <thead><tr><th>Modèle</th><th>Score</th><th>Vuln.</th><th>Statut</th></tr></thead>
            <tbody>
              {scans.slice(0, 5).map((s) => (
                <tr key={s.scan_id}>
                  <td className="mono">{s.target}</td>
                  <td><span className={`badge ${GRADE_CLASS[s.grade] || ""}`}>{s.score ?? "…"}{s.grade ? ` ${s.grade}` : ""}</span></td>
                  <td>{s.vulnerabilities ?? "—"}</td>
                  <td className="muted">{s.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
