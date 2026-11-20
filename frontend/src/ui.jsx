import React, { createContext, useContext, useEffect, useRef, useState } from "react";

export const GRADE_CLASS = { A: "g-ok", B: "g-ok", C: "g-warn", D: "g-warn", F: "g-bad" };

/* ----------------------------- count-up ----------------------------- */
export function useCountUp(target, dur = 900) {
  const [v, setV] = useState(0);
  const reduce = usePrefersReducedMotion();
  useEffect(() => {
    if (target == null) { setV(0); return; }
    if (reduce) { setV(target); return; }
    let raf; const start = performance.now();
    const tick = (now) => {
      const t = Math.min(1, (now - start) / dur);
      const eased = 1 - Math.pow(1 - t, 3);
      setV(Math.round(target * eased));
      if (t < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [target, dur, reduce]);
  return v;
}

export function usePrefersReducedMotion() {
  const [reduce, setReduce] = useState(false);
  useEffect(() => {
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    setReduce(mq.matches);
    const on = () => setReduce(mq.matches);
    mq.addEventListener?.("change", on);
    return () => mq.removeEventListener?.("change", on);
  }, []);
  return reduce;
}

/* ----------------------------- gauge ----------------------------- */
export function Gauge({ score, grade, size = 170 }) {
  const r = 70, c = 2 * Math.PI * r;
  const shown = useCountUp(score ?? 0, 1000);
  const off = c * (1 - shown / 100); // arc + number advance together, frame by frame
  const cls = GRADE_CLASS[grade] || "g-warn";
  return (
    <div className="gauge" style={{ width: size, height: size }}>
      <svg viewBox="0 0 180 180" width={size} height={size}>
        <circle cx="90" cy="90" r={r} className="gauge-track" />
        <circle cx="90" cy="90" r={r} className={`gauge-arc ${cls}`}
          strokeDasharray={c} strokeDashoffset={off} transform="rotate(-90 90 90)" />
      </svg>
      <div className="gauge-center">
        <div className={`gauge-score ${cls}`}>{score == null ? "—" : shown}</div>
        <div className="gauge-sub">/ 100 · {grade ?? "?"}</div>
      </div>
    </div>
  );
}

export function Pct({ v }) {
  const cls = v >= 0.5 ? "g-bad" : v > 0 ? "g-warn" : "g-ok";
  return <span className={cls}>{Math.round(v * 100)}%</span>;
}

export function Spinner({ size = 16 }) {
  return (
    <svg className="spin" width={size} height={size} viewBox="0 0 24 24" aria-hidden="true">
      <circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round"
        strokeDasharray="42 60" opacity="0.9" />
    </svg>
  );
}

export function Empty({ children }) {
  return (
    <div className="empty">
      <div className="shield-big float">⛊</div>
      <p>{children}</p>
    </div>
  );
}

export function Field({ label, hint, children }) {
  const id = React.useId();
  const control = React.isValidElement(children) ? React.cloneElement(children, { id }) : children;
  return (
    <div className="field">
      <label htmlFor={id}>{label} {hint && <span className="muted">{hint}</span>}</label>
      {control}
    </div>
  );
}

export function StatTile({ icon, value, label, i = 0 }) {
  const shown = useCountUp(typeof value === "number" ? value : null);
  return (
    <div className="stat rise" style={{ "--i": i }}>
      <div className="stat-ic"><Icon name={icon} /></div>
      <div className="stat-v">{typeof value === "number" ? shown : value}</div>
      <div className="stat-l">{label}</div>
    </div>
  );
}

/* ----------------------------- toasts ----------------------------- */
const ToastCtx = createContext(() => {});
export const useToast = () => useContext(ToastCtx);

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);
  const idRef = useRef(0);
  const push = (type, msg) => {
    const id = ++idRef.current;
    setToasts((t) => [...t, { id, type, msg, leaving: false }]);
    setTimeout(() => setToasts((t) => t.map((x) => (x.id === id ? { ...x, leaving: true } : x))), 3900);
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 4250);
  };
  return (
    <ToastCtx.Provider value={push}>
      {children}
      <div className="toasts" role="status" aria-live="polite" aria-atomic="false">
        {toasts.map((t) => (
          <div key={t.id} role={t.type === "error" ? "alert" : "status"}
            className={`toast ${t.type} ${t.leaving ? "leaving" : ""}`}>
            <Icon name={t.type === "error" ? "alert" : t.type === "ok" ? "check" : "info"} />
            <span>{t.msg}</span>
          </div>
        ))}
      </div>
    </ToastCtx.Provider>
  );
}

/* ----------------------------- icons (minimal line) ----------------------------- */
const PATHS = {
  overview: "M4 13h7V4H4v9Zm9 7h7V4h-7v16ZM4 20h7v-5H4v5Z",
  scan: "M11 4a7 7 0 1 0 0 14 7 7 0 0 0 0-14Zm10 17-5-5",
  compare: "M4 19V9m5 10V5m5 14v-7m5 7V8",
  arena: "M5 5l7 7m7-7-7 7m0 0-4 7m4-7 4 7",
  library: "M5 4h10l4 4v12H5V4Zm10 0v4h4M8 12h8M8 16h8",
  history: "M12 7v5l3 2M4 12a8 8 0 1 0 2.3-5.6M4 4v3h3",
  about: "M12 10v6m0-9h.01M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18Z",
  model: "M4 7h16M4 12h16M4 17h16M8 4v16",
  attack: "M12 3l8 4v5c0 5-3.5 8-8 9-4.5-1-8-4-8-9V7l8-4Z",
  category: "M4 4h7v7H4V4Zm9 0h7v7h-7V4ZM4 13h7v7H4v-7Zm9 0h7v7h-7v-7Z",
  check: "M5 12l4 4L19 7",
  alert: "M12 8v5m0 3h.01M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0Z",
  info: "M12 11v5m0-8h.01M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18Z",
  download: "M12 3v12m0 0 4-4m-4 4-4-4M4 21h16",
  chat: "M5 5h14v10H9l-4 4V5Z",
  send: "M4 12l16-8-6 16-3-6-7-2Z",
};
export function Icon({ name, size = 18 }) {
  const d = PATHS[name] || PATHS.info;
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor"
      strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d={d} />
    </svg>
  );
}
