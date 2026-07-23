import { useEffect, useState } from "react";
import Sidebar from "./components/Sidebar.jsx";
import ChatPanel from "./components/ChatPanel.jsx";
import SummaryPanel from "./components/SummaryPanel.jsx";
import QuizPanel from "./components/QuizPanel.jsx";
import { listDocuments } from "./api.js";

const TABS = ["Chat", "Summarize", "Quiz"];

export default function App() {
  const [documents, setDocuments] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [tab, setTab] = useState("Chat");

  async function refresh() {
    const docs = await listDocuments();
    setDocuments(docs);
  }

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, 4000);
    return () => clearInterval(interval);
  }, []);

  return (
    <>
      <Sidebar
        documents={documents}
        selectedId={selectedId}
        onSelect={setSelectedId}
        onChange={refresh}
      />
      <div className="main">
        <div className="tabs">
          {TABS.map((t) => (
            <button key={t} className={tab === t ? "active" : ""} onClick={() => setTab(t)}>
              {t}
            </button>
          ))}
        </div>

        {tab === "Chat" && <ChatPanel documentId={selectedId} />}
        {tab === "Summarize" && <SummaryPanel documentId={selectedId} />}
        {tab === "Quiz" && <QuizPanel documentId={selectedId} />}
      </div>
    </>
  );
}
