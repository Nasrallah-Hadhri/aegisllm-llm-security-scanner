import React, { useEffect, useRef, useState } from "react";
import { startMatch, openMatchSocket, getLeaderboard, targetLabel } from "../api.js";
import { Empty, Field, Spinner, Icon, useToast } from "../ui.jsx";

export default function ArenaView({ models }) {
  const toast = useToast();
  const [attacker, setAttacker] = useState("");
  const [target, setTarget] = useState("");
  const [judge, setJudge] = useState("");
  const [rounds, setRounds] = useState(4);
  const [status, setStatus] = useState("idle");
  const [live, setLive] = useState([]);
  const [phase, setPhase] = useState(null);     // {round, stage} — « ce que fait l'IA »
  const [result, setResult] = useState(null);
  const [board, setBoard] = useState([]);
  const [err, setErr] = useState("");
  const wsRef = useRef(null);
  const doneRef = useRef(false);

  useEffect(() => {
    if (models[0] && !attacker) setAttacker(models[0]);
    if (models[1] && !target) setTarget(models[1] || models[0]);
    refreshBoard();
  }, [models, attacker, target]);
  useEffect(() => () => closeWs(), []);
  const refreshBoard = () => getLeaderboard().then(setBoard).catch(() => {});

  const closeWs = () => {
    const ws = wsRef.current; wsRef.current = null;
    if (ws) { ws.onclose = null; ws.onerror = null; try { ws.close(); } catch {} }
  };
  const handleClose = () => {
    if (doneRef.current) return;
    setStatus("error"); setErr("Connexion au serveur interrompue");
    toast("error", "Connexion au serveur interrompue");
  };

  const launch = async () => {
    setErr(""); setResult(null); setLive([]); setPhase(null); setStatus("running");
    doneRef.current = false;
    try {
      const { match_id } = await startMatch({ attacker, target, judge: judge || null, max_rounds: Number(rounds) });
      closeWs();
      wsRef.current = openMatchSocket(match_id, onEvent, handleClose);
    } catch (e) { setErr(String(e)); setStatus("error"); toast("error", "Échec du lancement du match"); }
  };

  const onEvent = (ev) => {
    if (ev.type === "phase") setPhase({ round: ev.round, stage: ev.stage });
    else if (ev.type === "round") { setPhase(null); setLive((l) => [...l, ev.round]); }
    else if (ev.type === "done") {
      doneRef.current = true; setPhase(null);
      setStatus("done"); setResult(ev.result); refreshBoard();
      toast(ev.result?.winner === "attacker" ? "info" : "ok",
        ev.result?.winner === "attacker"
          ? `Attaquant vainqueur en ${ev.result?.rounds_played} tour(s)`
          : `La cible a résisté aux ${ev.result?.rounds_played} tours`);
    } else if (ev.type === "error") { doneRef.current = true; setPhase(null); setStatus("error"); setErr(ev.error); toast("error", ev.error); }
  };

  const winnerAttacker = result?.winner === "attacker";
  const PHASE_LABEL = {
    attacking: "L'IA attaquante prépare sa tentative…",
    responding: "L'IA cible réfléchit à sa réponse…",
    judging: "Le juge évalue le tour…",
  };

  return (
    <div className="two-col">
      <section className="card rise" style={{ "--i": 0 }}>
        <h2>Arène IA vs IA</h2>
        <p className="muted spc">Une IA attaquante tente, tour après tour, de faire céder une IA cible (objectif factice et inoffensif). Un juge peut arbitrer.</p>
        <Field label="IA attaquante">
          <select value={attacker} onChange={(e) => setAttacker(e.target.value)}>
            {models.map((m) => <option key={m} value={m}>{targetLabel(m)}</option>)}
          </select>
        </Field>
        <Field label="IA cible">
          <select value={target} onChange={(e) => setTarget(e.target.value)}>
            {models.map((m) => <option key={m} value={m}>{targetLabel(m)}</option>)}
          </select>
        </Field>
        <Field label="Juge LLM" hint="(optionnel)">
          <select value={judge} onChange={(e) => setJudge(e.target.value)}>
            <option value="">— aucun —</option>
            {models.map((m) => <option key={m} value={m}>{targetLabel(m)}</option>)}
          </select>
        </Field>
        <Field label="Nombre de tours">
          <input type="number" min="1" max="10" value={rounds} onChange={(e) => setRounds(e.target.value)} />
        </Field>
        <button className="btn" disabled={status === "running" || !attacker || !target} onClick={launch}>
          {status === "running" ? <><Spinner /> Match en cours…</> : <><Icon name="arena" size={16} /> Lancer le match</>}
        </button>
        {err && <div className="err">{err}</div>}

        <h3>Classement</h3>
        <table>
          <thead><tr><th scope="col">Modèle</th><th scope="col">Déf. G-P</th><th scope="col">Att. G-P</th></tr></thead>
          <tbody>
            {board.length === 0 && <tr><td colSpan="3" className="muted">aucun match</td></tr>}
            {board.map((e) => (
              <tr key={e.model}>
                <th scope="row" className="mono small">{e.model}</th>
                <td className="g-ok">{e.def_wins}–{e.def_losses}</td>
                <td className="g-bad">{e.atk_wins}–{e.atk_losses}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section className="card rise" style={{ "--i": 1 }}>
        {status === "idle" && live.length === 0 && <Empty>Oppose deux modèles pour lancer un duel de robustesse.</Empty>}

        {(status === "running" || status === "done") && (
          <>
            {result && (
              <div className={`winner pop ${winnerAttacker ? "att" : "def"}`}>
                {winnerAttacker
                  ? <><Icon name="arena" size={16} /> L'IA attaquante a percé en {result.rounds_played} tour(s)</>
                  : <><Icon name="attack" size={16} /> L'IA cible a résisté aux {result.rounds_played} tours</>}
              </div>
            )}
            <h2>Déroulé du match</h2>
            <div className="rounds">
              {live.map((r) => (
                <div className={`round round-in ${r.leaked ? "leak" : ""}`} key={r.index}>
                  <div className="round-head">
                    <span className="round-no">Tour {r.index}</span>
                    {r.judge_score != null && <span className="round-score">juge : {r.judge_score}/10</span>}
                    <span className={r.leaked ? "g-bad" : "g-ok"}>{r.leaked ? "✗ secret révélé" : "✓ tenu"}</span>
                  </div>
                  <div className="bubble att"><b>Attaquant</b><p>{r.attack_prompt}</p></div>
                  <div className="bubble def"><b>Cible</b><p>{r.target_response}</p></div>
                  {r.judge_rationale && <div className="bubble judge"><b>Juge</b><p>{r.judge_rationale}</p></div>}
                </div>
              ))}
              {status === "running" && phase && (
                <div className="thinking">
                  <Spinner /> <span><strong>Tour {phase.round}</strong> — {PHASE_LABEL[phase.stage] || "en cours…"}</span>
                </div>
              )}
              {status === "running" && !phase && <div className="muted">… tour suivant en cours</div>}
            </div>
          </>
        )}
        {status === "error" && <div className="err">Erreur : {err}</div>}
      </section>
    </div>
  );
}
