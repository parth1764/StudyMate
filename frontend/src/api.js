const BASE = "/api";

async function handle(res) {
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || JSON.stringify(body);
    } catch {
      // ignore parse failure, keep statusText
    }
    throw new Error(detail);
  }
  return res.json();
}

export async function listDocuments() {
  const res = await fetch(`${BASE}/documents`);
  return handle(res);
}

export async function uploadDocument(file) {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${BASE}/documents/upload`, {
    method: "POST",
    body: form,
  });
  return handle(res);
}

export async function deleteDocument(documentId) {
  const res = await fetch(`${BASE}/documents/${documentId}`, { method: "DELETE" });
  return handle(res);
}

export async function askQuestion(question, documentId) {
  const res = await fetch(`${BASE}/chat/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, document_id: documentId || null }),
  });
  return handle(res);
}

export async function summarizeDocument(documentId) {
  const res = await fetch(`${BASE}/summarize/${documentId}`, { method: "POST" });
  return handle(res);
}

export async function generateQuiz(documentId, numQuestions = 5) {
  const res = await fetch(`${BASE}/quiz/${documentId}?num_questions=${numQuestions}`, {
    method: "POST",
  });
  return handle(res);
}
