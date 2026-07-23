import { useRef, useState } from "react";
import { deleteDocument, uploadDocument } from "../api.js";

export default function Sidebar({ documents, selectedId, onSelect, onChange }) {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);
  const inputRef = useRef(null);

  async function handleFile(e) {
    const file = e.target.files[0];
    if (!file) return;
    setUploading(true);
    setError(null);
    try {
      await uploadDocument(file);
      await onChange();
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
      inputRef.current.value = "";
    }
  }

  async function handleDelete(e, id) {
    e.stopPropagation();
    await deleteDocument(id);
    if (selectedId === id) onSelect(null);
    await onChange();
  }

  return (
    <div className="sidebar">
      <div>
        <h1>StudyMate</h1>
        <p className="tagline">RAG study assistant · CPU-only</p>
      </div>

      <div className="upload-box">
        <input
          ref={inputRef}
          id="file-upload"
          type="file"
          accept=".pdf,.docx,.pptx,.srt,.vtt,.txt"
          onChange={handleFile}
          disabled={uploading}
        />
        <label htmlFor="file-upload">
          {uploading ? "Uploading & indexing…" : "+ Upload PDF / DOCX / PPTX / transcript"}
        </label>
      </div>

      {error && <div className="error-banner">{error}</div>}

      <ul className="doc-list">
        {documents.map((doc) => (
          <li
            key={doc.id}
            className={`doc-item ${selectedId === doc.id ? "selected" : ""}`}
            onClick={() => onSelect(doc.id)}
          >
            <span className="name" title={doc.filename}>
              {doc.filename}
            </span>
            <span className={`status status-${doc.status}`}>{doc.status}</span>
            <button title="Delete" onClick={(e) => handleDelete(e, doc.id)}>
              ✕
            </button>
          </li>
        ))}
        {documents.length === 0 && (
          <li className="empty-state">No documents yet — upload one to get started.</li>
        )}
      </ul>
    </div>
  );
}
