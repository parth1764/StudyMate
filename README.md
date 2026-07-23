# StudyMate — AI-Powered Learning Assistant

RAG-based study assistant that ingests PDFs, Word docs, PowerPoint slides, and
video transcripts, then lets you ask questions over them (RAG), generate
summaries, and auto-generate quizzes for revision.

Runs entirely on **CPU** — no GPU required:

- **Retrieval**: FAISS (local, in-process vector index) + `sentence-transformers/all-MiniLM-L6-v2` embeddings (small, fast on CPU)
- **Generation / Chat / Quiz**: Llama 3.3 70B via the **Groq API** (hosted inference, called over HTTPS — the 70B model never runs locally)
- **Summarization**: `sshleifer/distilbart-cnn-12-6` (DistilBART) run locally via HuggingFace `transformers`, CPU-only, small enough to run comfortably without a GPU
- **Backend**: FastAPI + SQLite (document registry) + FAISS (vectors on disk)
- **Frontend**: React (Vite)

## Architecture

```
Upload (PDF/DOCX/PPTX/transcript)
        │
        ▼
  Text extraction  (pypdf / python-docx / python-pptx / .srt,.vtt,.txt)
        │
        ▼
  Chunking (sliding window, char-based)
        │
        ▼
  Embedding (MiniLM, CPU)  ──────► FAISS index (data/index/*.faiss + metadata.jsonl)
        │
        ▼
  SQLite document registry (data/studymate.db)

Query flow (Ask):
  question ─► embed ─► FAISS top-k ─► prompt with retrieved chunks ─► Groq Llama-3.3-70B ─► answer + sources

Summarize flow:
  document chunks ─► DistilBART (local, CPU) map-reduce summarization ─► final summary

Quiz flow:
  document chunks (sampled) ─► Groq Llama-3.3-70B (structured JSON prompt) ─► MCQ quiz + answer key
```

## Prerequisites

- Python 3.10+
- Node 18+ (for the React frontend)
- A free [Groq API key](https://console.groq.com/keys) — this is the only external account you need. Everything else (embeddings, summarization) runs locally on CPU.

## Backend setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# CPU-only torch build — much smaller download than the default GPU wheel
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt

cp .env.example .env
# edit .env and set GROQ_API_KEY=gsk_...

uvicorn app.main:app --reload --port 8000
```

First run will download the embedding model (~90MB) and the DistilBART
summarization model (~300MB) from HuggingFace — this happens once and is
cached under `~/.cache/huggingface`.

API docs available at `http://localhost:8000/docs`.

## Frontend setup

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. The Vite dev server proxies `/api` to the
backend on port 8000 (see `vite.config.js`).

## Docker (optional, runs both services together)

```bash
docker compose up --build
```

Backend on `:8000`, frontend on `:5173`. Set `GROQ_API_KEY` in a root `.env`
file before running (see `.env.example` at the repo root, referenced by
`docker-compose.yml`).

## Environment variables (backend/.env)

| Variable | Default | Description |
|---|---|---|
| `GROQ_API_KEY` | *(required)* | API key from console.groq.com |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | Groq-hosted chat model used for Q&A and quiz generation |
| `EMBEDDING_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | CPU-friendly embedding model |
| `SUMMARIZATION_MODEL` | `sshleifer/distilbart-cnn-12-6` | Local CPU summarization model |
| `CHUNK_SIZE` | `1000` | Characters per chunk |
| `CHUNK_OVERLAP` | `150` | Overlap between consecutive chunks |
| `TOP_K` | `5` | Chunks retrieved per query |
| `DATA_DIR` | `../data` | Where uploads, FAISS index, and SQLite DB live |

## What "video transcripts" means here

There's no local speech-to-text step (that needs either a GPU or a slow CPU
Whisper pass). Instead, StudyMate ingests transcript files directly —
`.srt`, `.vtt`, or plain `.txt` — the same formats YouTube/Zoom/Teams let you
export. If you need audio-to-transcript, run `whisper` or `faster-whisper`
(`tiny`/`base` model, CPU) separately and feed the resulting `.srt` in.

## API endpoints

- `POST /api/documents/upload` — upload a file, extract + chunk + embed + index it
- `GET /api/documents` — list ingested documents
- `DELETE /api/documents/{id}` — remove a document and its vectors
- `POST /api/chat/ask` — ask a question (RAG over one document or the whole corpus)
- `POST /api/summarize/{document_id}` — generate a summary for a document
- `POST /api/quiz/{document_id}` — generate an MCQ quiz for a document

## Known limitations / next steps

- Single-process FAISS index held in memory + flushed to disk after writes — fine for a personal project, not for concurrent multi-user writes.
- No auth — add an API key / JWT layer before deploying publicly.
- DistilBART summarization is map-reduce'd over chunks for long docs; quality degrades for very long documents compared to a single-pass summary — bump `CHUNK_SIZE` or swap in `facebook/bart-large-cnn` (bigger, still CPU-runnable, slower) via `SUMMARIZATION_MODEL` if quality matters more than speed.
