import { useState } from "react";
import { generateQuiz } from "../api.js";

export default function QuizPanel({ documentId }) {
  const [questions, setQuestions] = useState([]);
  const [selected, setSelected] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function handleGenerate() {
    setLoading(true);
    setError(null);
    setSelected({});
    try {
      const res = await generateQuiz(documentId, 5);
      setQuestions(res.questions);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  function choose(qIdx, optIdx) {
    setSelected((prev) => ({ ...prev, [qIdx]: optIdx }));
  }

  if (!documentId) {
    return <p className="empty-state">Select a document from the sidebar to generate a quiz.</p>;
  }

  return (
    <div className="panel">
      <button className="primary" onClick={handleGenerate} disabled={loading}>
        {loading ? "Generating quiz (Llama 3.3 70B via Groq)…" : "Generate quiz"}
      </button>
      {error && <div className="error-banner">{error}</div>}

      {questions.map((q, qIdx) => {
        const chosen = selected[qIdx];
        return (
          <div className="quiz-question" key={qIdx}>
            <strong>
              {qIdx + 1}. {q.question}
            </strong>
            {q.options.map((opt, optIdx) => {
              let cls = "quiz-option";
              if (chosen !== undefined) {
                if (optIdx === q.correct_index) cls += " correct";
                else if (optIdx === chosen) cls += " incorrect";
              }
              return (
                <div key={optIdx} className={cls} onClick={() => choose(qIdx, optIdx)}>
                  {opt}
                </div>
              );
            })}
            {chosen !== undefined && (
              <div className="answer-box">{q.explanation}</div>
            )}
          </div>
        );
      })}
    </div>
  );
}
