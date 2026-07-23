import { useState } from "react";
import { askQuestion } from "../api.js";

export default function ChatPanel({ documentId }) {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState(null);
  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function handleAsk() {
    if (!question.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const res = await askQuestion(question, documentId);
      setAnswer(res.answer);
      setSources(res.sources);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="panel">
      <p>
        {documentId
          ? "Asking questions scoped to the selected document."
          : "No document selected — searching across your whole corpus."}
      </p>
      <textarea
        rows={3}
        placeholder="Ask something about your material…"
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
      />
      <button className="primary" onClick={handleAsk} disabled={loading}>
        {loading ? "Thinking…" : "Ask"}
      </button>

      {error && <div className="error-banner">{error}</div>}

      {answer && <div className="answer-box">{answer}</div>}

      {sources.length > 0 && (
        <div className="sources">
          <strong>Sources</strong>
          {sources.map((s, i) => (
            <div className="source-card" key={i}>
              <div className="meta">
                {s.filename} · chunk #{s.chunk_index} · score {s.score.toFixed(3)}
              </div>
              {s.text}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
