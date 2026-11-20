import React, { useEffect, useMemo, useState } from "react";
import { getProbes } from "../api.js";

const SEV_CLASS = { critical: "g-bad", high: "g-bad", medium: "g-warn", low: "muted" };

const OWASP_LABEL = {
  LLM01: "Prompt Injection", LLM02: "Fuite d'informations", LLM05: "Sorties non sécurisées",
  LLM06: "Agentivité excessive", LLM07: "Fuite du system prompt", LLM08: "Vecteurs / RAG",
  LLM09: "Désinformation", LLM10: "Consommation non bornée", jailbreak: "Jailbreak",
};

export default function LibraryView() {
  const [probes, setProbes] = useState([]);
  useEffect(() => { getProbes().then(setProbes).catch(() => {}); }, []);

  const groups = useMemo(() => {
    const g = {};
    probes.forEach((p) => (g[p.owasp] = g[p.owasp] || []).push(p));
    return g;
  }, [probes]);

  return (
    <div className="single">
      <div className="card rise" style={{ "--i": 0 }}>
        <h2>Bibliothèque d'attaques</h2>
        <p className="muted spc">
          {probes.length} attaques réparties sur {Object.keys(groups).length} catégories.
          Toutes utilisent des objectifs « proxy » inoffensifs (jeton canari ou secret factice).
        </p>
      </div>

      {Object.entries(groups).map(([owasp, list], gi) => (
        <div className="card rise" style={{ "--i": gi + 1 }} key={owasp}>
          <div className="lib-head">
            <span className="mono tag">{owasp}</span>
            <h3 style={{ margin: 0 }}>{OWASP_LABEL[owasp] || owasp}</h3>
            <span className="muted">{list.length} attaque(s)</span>
          </div>
          <div className="probe-grid">
            {list.map((p) => (
              <div className="probe" key={p.id}>
                <div className="probe-top">
                  <strong>{p.title}</strong>
                  <span className={SEV_CLASS[p.severity] || "muted"}>{p.severity}</span>
                </div>
                <div className="muted small">technique : {p.technique} · détecteur : {p.detector}</div>
                <div className="chips small-chips">
                  {p.mutations.map((m) => <span className="chip mini" key={m}>{m}</span>)}
                </div>
                <details>
                  <summary>Voir le prompt</summary>
                  <pre>{p.prompt}</pre>
                </details>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
