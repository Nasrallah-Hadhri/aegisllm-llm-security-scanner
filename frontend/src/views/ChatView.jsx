import React, { useEffect, useRef, useState } from "react";
import { sendChat, targetLabel } from "../api.js";
import { Field, Spinner, Icon, Empty, useToast } from "../ui.jsx";

export default function ChatView({ models }) {
  const toast = useToast();
  const [model, setModel] = useState("");
  const [system, setSystem] = useState("");
  const [temp, setTemp] = useState(0.7);
  const [msgs, setMsgs] = useState([]);     // {role:'user'|'assistant', content, meta?, error?}
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const endRef = useRef(null);

  useEffect(() => { if (models[0] && !model) setModel(models[0]); }, [models, model]);
  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth" }); }, [msgs, busy]);

  const reset = () => setMsgs([]);

  const send = async () => {
    const text = input.trim();
    if (!text || busy || !model) return;
    const convo = [...msgs, { role: "user", content: text }];
    setMsgs(convo); setInput(""); setBusy(true);
    try {
      const payload = [
        ...(system.trim() ? [{ role: "system", content: system.trim() }] : []),
        ...convo.map((m) => ({ role: m.role, content: m.content })),
      ];
      const r = await sendChat({ target: model, messages: payload, temperature: Number(temp) });
      setMsgs((m) => [...m, {
        role: "assistant", content: r.text || "(réponse vide)",
        meta: `${Math.round(r.latency_ms)} ms · ${r.completion_tokens} jetons`,
      }]);
    } catch (e) {
      setMsgs((m) => [...m, { role: "assistant", content: String(e), error: true }]);
      toast("error", "Échec de l'appel au modèle");
    } finally { setBusy(false); }
  };

  const onKey = (e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } };

  return (
    <div className="two-col">
      <section className="card rise" style={{ "--i": 0 }}>
        <h2>Test manuel</h2>
        <p className="muted spc">Choisis un modèle et discute librement avec lui — pratique pour explorer son comportement avant un scan.</p>
        <Field label="Modèle">
          <select value={model} onChange={(e) => setModel(e.target.value)}>
            {models.map((m) => <option key={m} value={m}>{targetLabel(m)}</option>)}
          </select>
        </Field>
        <Field label={`Température : ${Number(temp).toFixed(1)}`} hint="(créativité)">
          <input type="range" min="0" max="1" step="0.1" value={temp} onChange={(e) => setTemp(e.target.value)} />
        </Field>
        <details>
          <summary>Instruction système (optionnel)</summary>
          <textarea className="ta" rows="4" value={system} onChange={(e) => setSystem(e.target.value)}
            placeholder="Ex. : Tu es un assistant concis en français." />
        </details>
        <button className="btn-ghost" style={{ marginTop: 16 }} onClick={reset} disabled={!msgs.length}>
          <Icon name="history" size={14} /> Effacer la conversation
        </button>
      </section>

      <section className="card rise chatcard" style={{ "--i": 1 }}>
        <div className="chat-log">
          {msgs.length === 0 && !busy && <Empty>Écris un message pour démarrer la conversation.</Empty>}
          {msgs.map((m, i) => (
            <div className={`chat-msg ${m.role}`} key={i}>
              <div className="chat-role">{m.role === "user" ? "Vous" : "Modèle"}</div>
              <div className={`chat-bubble ${m.error ? "err" : ""}`}>{m.content}</div>
              {m.meta && <div className="chat-meta">{m.meta}</div>}
            </div>
          ))}
          {busy && <div className="chat-msg assistant"><div className="chat-role">Modèle</div><div className="chat-bubble"><Spinner /> …</div></div>}
          <div ref={endRef} />
        </div>
        <div className="chat-input">
          <textarea rows="1" value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={onKey}
            placeholder="Votre message…  (Entrée pour envoyer, Maj+Entrée pour une nouvelle ligne)" />
          <button className="btn chat-send" disabled={busy || !input.trim() || !model} onClick={send}>
            {busy ? <Spinner /> : <Icon name="send" size={16} />}
          </button>
        </div>
      </section>
    </div>
  );
}
