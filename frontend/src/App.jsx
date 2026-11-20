import React, { useEffect, useState } from "react";
import { getHealth, getModels, getCategories } from "./api.js";
import { ToastProvider, Icon } from "./ui.jsx";
import MatrixRain from "./MatrixRain.jsx";
import OverviewView from "./views/OverviewView.jsx";
import ScanView from "./views/ScanView.jsx";
import CompareView from "./views/CompareView.jsx";
import ArenaView from "./views/ArenaView.jsx";
import ChatView from "./views/ChatView.jsx";
import LibraryView from "./views/LibraryView.jsx";
import HistoryView from "./views/HistoryView.jsx";
import AboutView from "./views/AboutView.jsx";

const NAV = [
  { id: "overview", icon: "overview", label: "Vue d'ensemble", desc: "Tableau de bord" },
  { id: "scan", icon: "scan", label: "Scanner", desc: "Tester un modèle" },
  { id: "compare", icon: "compare", label: "Comparaison", desc: "Classer des modèles" },
  { id: "arena", icon: "arena", label: "Arène IA vs IA", desc: "Duel de robustesse" },
  { id: "chat", icon: "chat", label: "Test manuel", desc: "Discuter avec un modèle" },
  { id: "library", icon: "library", label: "Bibliothèque", desc: "Les attaques testées" },
  { id: "history", icon: "history", label: "Historique", desc: "Scans & matchs" },
  { id: "about", icon: "about", label: "À propos", desc: "Méthode & éthique" },
];

export default function App() {
  const [view, setView] = useState("overview");
  const [health, setHealth] = useState(null);
  const [models, setModels] = useState([]);
  const [cats, setCats] = useState([]);

  useEffect(() => {
    getHealth().then(setHealth).catch(() => setHealth({ status: "down" }));
    getCategories().then(setCats).catch(() => {});
    getModels().then((d) => {
      const demo = (d.demo || []).map((x) => x.value);
      const ollama = (d.ollama || []).map((m) => `ollama:${m}`);
      setModels([...demo, ...ollama]);
    }).catch(() => {});
  }, []);

  const up = health?.status === "ok";

  return (
    <ToastProvider>
      <MatrixRain />
      <div className="shell">
        <aside className="sidebar">
          <div className="logo"><span className="shield">⛊</span> AegisLLM</div>
          <div className="logo-sub">Test de sécurité des LLM</div>
          <nav>
            {NAV.map((n) => (
              <button key={n.id} className={`nav ${view === n.id ? "active" : ""}`}
                aria-current={view === n.id ? "page" : undefined} onClick={() => setView(n.id)}>
                <span className="nav-ic"><Icon name={n.icon} /></span>
                <span className="nav-txt">
                  <span className="nav-label">{n.label}</span>
                  <span className="nav-desc">{n.desc}</span>
                </span>
              </button>
            ))}
          </nav>
          <div className="side-foot">
            <span className={`dot ${up ? "on" : "off"}`} />
            API {up ? "en ligne" : "hors ligne"}
            <div className="muted small">{models.length} modèle(s)</div>
          </div>
        </aside>

        <main className="main">
          <div className="view" key={view}>
            {view === "overview" && <OverviewView models={models} cats={cats} go={setView} />}
            {view === "scan" && <ScanView models={models} cats={cats} />}
            {view === "compare" && <CompareView models={models} cats={cats} />}
            {view === "arena" && <ArenaView models={models} />}
            {view === "chat" && <ChatView models={models} />}
            {view === "library" && <LibraryView />}
            {view === "history" && <HistoryView />}
            {view === "about" && <AboutView />}
          </div>
        </main>
      </div>
    </ToastProvider>
  );
}
