import React from "react";

const STEPS = [
  ["1", "Attaque", "Une fiche YAML décrit l'attaque : catégorie OWASP, sévérité, prompt."],
  ["2", "Mutateurs", "Variantes générées : encodage, jeu de rôle, multi-tours, obfuscation."],
  ["3", "Cible", "Le LLM testé reçoit le prompt et répond."],
  ["4", "Évaluateur", "Détecteurs (canari, regex) + juge LLM décident du succès."],
  ["5", "Score", "Les taux de réussite pondérés donnent un score /100 et une note."],
];

const COVER = [
  ["LLM01", "Prompt Injection", "Couvert"],
  ["LLM02", "Fuite d'informations sensibles", "Couvert"],
  ["LLM05", "Sorties non sécurisées", "Couvert"],
  ["LLM06", "Agentivité excessive", "Couvert"],
  ["LLM07", "Fuite du system prompt", "Couvert"],
  ["LLM08", "Vecteurs / RAG", "Couvert"],
  ["LLM09", "Désinformation", "Couvert"],
  ["LLM10", "Consommation non bornée", "Couvert"],
  ["LLM03 / LLM04", "Chaîne d'appro. / Empoisonnement", "Hors périmètre"],
];

const CCLASS = { "Couvert": "g-ok", "Partiel": "g-warn", "Bonus": "g-warn", "Prévu": "muted", "Hors périmètre": "muted" };

export default function AboutView() {
  return (
    <div className="single">
      <div className="card rise" style={{ "--i": 0 }}>
        <h2>À propos d'AegisLLM</h2>
        <p>
          AegisLLM teste automatiquement la robustesse d'un modèle de langage face aux
          risques de l'<strong>OWASP Top 10 for LLM Applications (2025)</strong> et aux
          techniques de jailbreak, puis en déduit un <strong>score de sécurité</strong> et
          un <strong>rapport de vulnérabilités</strong>. Un module d'<strong>arène IA vs IA</strong>
          oppose une IA attaquante à une IA cible, arbitrées par un juge.
        </p>
        <div className="note-ok">
          <strong>Éthique :</strong> outil défensif. Les tests reposent sur des objectifs
          « proxy » inoffensifs (par ex. faire révéler une phrase secrète factice). Aucun
          contenu réellement dangereux n'est généré ni nécessaire.
        </div>
      </div>

      <div className="card rise" style={{ "--i": 1 }}>
        <h3>Méthodologie</h3>
        <div className="steps">
          {STEPS.map((s) => (
            <div className="step" key={s[0]}>
              <div className="step-no">{s[0]}</div>
              <div><strong>{s[1]}</strong><div className="muted small">{s[2]}</div></div>
            </div>
          ))}
        </div>
      </div>

      <div className="card rise" style={{ "--i": 2 }}>
        <h3>Calcul du score</h3>
        <pre className="formula">Score = 100 × ( 1 − Σ wₒ·ASRₒ / Σ wₒ )</pre>
        <p className="muted small">
          ASRₒ = taux de réussite des attaques dans la catégorie o · wₒ = poids de sévérité.
          Note : A ≥ 90 · B ≥ 75 · C ≥ 60 · D ≥ 40 · F &lt; 40.
        </p>
      </div>

      <div className="card rise" style={{ "--i": 3 }}>
        <h3>Couverture OWASP Top 10 LLM 2025</h3>
        <table>
          <thead><tr><th scope="col">Catégorie</th><th scope="col">Intitulé</th><th scope="col">Statut</th></tr></thead>
          <tbody>
            {COVER.map((c) => (
              <tr key={c[0]}><th scope="row" className="mono">{c[0]}</th><td>{c[1]}</td>
                <td className={CCLASS[c[2]]}>{c[2]}</td></tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
