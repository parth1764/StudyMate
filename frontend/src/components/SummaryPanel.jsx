import { useState } from "react";
import { summarizeDocument } from "../api.js";

export default function SummaryPanel({ documentId }) {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function handleSummarize() {
    setLoading(true);
    setError(null);
    try {
      const res = await summarizeDocument(documentId);
      setSummary(res.summary);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  if (!documentId) {
    return <p className="empty-state">Select a document from the sidebar to summarize it.</p>;
  }

  return (
    <div className="panel">
      <button className="primary" onClick={handleSummarize} disabled={loading}>
        {loading ? "Summarizing (DistilBART, CPU)…" : "Generate summary"}
      </button>
      {error && <div className="error-banner">{error}</div>}
      {summary && <div className="summary-box">{summary}</div>}
    </div>
  );
}
