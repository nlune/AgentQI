LLM Hackathon for Applications in Materials & Chemistry

# AgentQI — PDF QA with Visual Evidence 

AgentQI is a lightweight RAG demo that turns a material certificate PDF into line‑aware chunks, stores them in a vector DB, and lets you query the document with an LLM. Answers come back with structured evidence (doc name + chunk ids), and the UI can render a highlighted PDF to show exactly where the answer came from.

Note: demo for core PDF → chunks → retrieval → answer → highlight loop. The agentic workflow and knowledge‑graph (KG) pieces are to be integrated.

## Quick Demo
- Upload a PDF in the frontend.
- Ask a question in the chat panel.
- The backend retrieves relevant chunks and calls a local LLM.
- The UI then requests `/highlight` to render an annotated PDF and scrolls to the evidence.

## Project Layout
- `backend/` — FastAPI service for OCR, chunking, retrieval, LLM call, and highlight generation
- `app_frontend/` — Vite + React app with a PDF viewer and simple chat UI

## Architecture
- **OCR + layout:** PyMuPDF for text and line‑level boxes; Tesseract as a fallback for image‑only pages.
- **Chunking:** Lines are grouped into semantically useful chunks; each chunk stores a merged bbox and page index.
- **Embeddings + store:** SentenceTransformers (`all‑MiniLM‑L6‑v2`) + ChromaDB (persistent at `backend/vector_db/`).
- **Retrieval:** Build a standardized context string with doc and chunk identifiers, returned alongside metadata.
- **LLM answering:** Calls an Ollama‑compatible endpoint at `http://localhost:8880/api/generate`. The prompt template lives at `backend/prompts/assistant_prompt.txt` and enforces a JSON response with `result` and `evidence`.
- **Visual evidence:** `/highlight` generates an annotated PDF (cached) under `backend/storage/annotated_pdfs/` and exposes it under `/pdfs/annotated/...`.

## Quickstart
- install requirements
- run resources (set up ollama with port 8880)
- start back and frontend

```
ssh 8880:slurmnode:8880 name@slurmnode
srun --gres=gpu --time=4:00:00 --pty bash
ollama serve


cd backend/
python main.py

cd ../app_frontend/
npm run dev

```

## Backend
- Tech: FastAPI, PyMuPDF, Tesseract (optional), ChromaDB, SentenceTransformers
- Entry: `backend/main.py`
- Settings: `backend/settings.py` (DB path, models, etc.)

Run locally (Python 3.10+):
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt 

# Start API (defaults to 8000)
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
OS package for OCR fallback (optional): `sudo apt-get install tesseract-ocr`.

Note: we are self-hosting ollama on our slurm GPU node on port 8880
LLM requirement: Ollama‑compatible server exposing `POST /api/generate` at `http://localhost:8880`. 

### API Endpoints (prefix `/api/v1`)
- `POST /process-pdf` — form‑data `file=@/path/to/file.pdf`. Ingests the PDF, extracts text and line boxes, stores chunks in Chroma.
- `POST /query?query=...&doc_name=...&k=5` — retrieves context for the document and calls the LLM. Returns `result` and `evidence`.
- `POST /highlight` — JSON: `{ doc_name, chunk_ids: [int], color?: [r,g,b], return_pdf?: bool }`. Returns metadata and an `annotated_pdf_url`; optionally streams the PDF.

Static file mounts:
- `/pdfs/original/...` → `backend/storage/original_pdfs/`
- `/pdfs/annotated/...` → `backend/storage/annotated_pdfs/`

Curl examples:
```bash
# Upload / process
curl -X POST -F "file=@test_files/Certificate-BAM-A001.pdf" http://localhost:8000/api/v1/process-pdf

# Query
curl -G "http://localhost:8000/api/v1/query" \
  --data-urlencode "query=What type of certificate is this?" \
  --data-urlencode "doc_name=Certificate-BAM-A001.pdf" \
  --data-urlencode "k=5"

# Highlight
curl -X POST http://localhost:8000/api/v1/highlight \
  -H 'Content-Type: application/json' \
  -d '{"doc_name":"Certificate-BAM-A001.pdf","chunk_ids":[0,3],"color":[1,0.85,0.2],"return_pdf":false}'
```

## Frontend (Vite + React)
- `app_frontend/` contains a minimal UI: left side PDF viewer, right side chat.
- The API base is configurable in the top‑right input at runtime.
- For local dev, the Vite proxy forwards `/api/v1` and `/pdfs` to `http://localhost:8000`.

Run locally (Node 18+):
```bash
cd app_frontend
npm install
npm run dev
```
- Set API base input to `/api/v1` to use the proxy, or `http://localhost:8000/api/v1` to call directly.
- Build: `npm run build` (serve `dist/` with any static server).

## Data & Persistence
- Vector DB: `backend/vector_db/` (safe to delete to rebuild index)
- Original PDFs: `backend/storage/original_pdfs/`
- Annotated PDFs: `backend/storage/annotated_pdfs/`

## Known Gaps / Hackathon Notes
- Agent workflow and KG extraction are not wired in yet; they are next on the roadmap.
- The LLM endpoint is expected at `http://localhost:8880/api/generate`. Adjust your local runtime accordingly (or adapt `backend/core/assistant.py`).
- Bounding boxes come from PyMuPDF line extraction when possible; OCR fallback uses Tesseract and may vary in quality for complex scans.

## Roadmap
- Agentic multi‑step reasoning and tool use (e.g., follow‑up retrievals, tabular extraction)
- Knowledge graph creation (entities/relations per chunk) and graph‑aware retrieval
- Multi‑document queries and results aggregation
- Richer UI for evidence review and side‑by‑side comparisons

## License
MIT — see `LICENSE`.


---

