# AgentQI Backend

FastAPI backend providing:
- PDF OCR (line-level bounding boxes)
- Chunking & semantic embedding storage (ChromaDB + SentenceTransformers)
- Retrieval + structured LLM answering with evidence (doc + chunk ids)

## 1. Tech Stack
- FastAPI / Uvicorn
- PyMuPDF (primary PDF text & layout extraction)
- Tesseract (fallback OCR)
- SentenceTransformers (`all-MiniLM-L6-v2` default)
- ChromaDB persistent vector store (`backend/vector_db/`)
- Local LLM (Ollama compatible endpoint at `http://localhost:8880/api/generate`)

## 2. Environment Setup
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip

# Core dependencies
pip install fastapi uvicorn requests pymupdf pytesseract opencv-python-headless chromadb sentence-transformers
pip install torch --index-url https://download.pytorch.org/whl/cu121  # (Optional GPU)
```

(If Tesseract not installed on OS: `sudo apt-get install tesseract-ocr`)

## 3. Run the API
```bash
uvicorn main:app --host 0.0.0.0 --port 8880 --reload
```
Root health check:
```
GET http://localhost:8880/
```
All functional routes are under `/api/v1`.

## 4. Endpoints
### 4.1 Ingest / Process PDF
`POST /api/v1/process-pdf`
Form-Data: `file=@/absolute/path/to/Certificate-BAM-A001.pdf`

Response sample:
```json
{
  "success": true,
  "filename": "Certificate-BAM-A001.pdf",
  "extracted_text": "...",
  "text_length": 12345,
  "document_name": "Certificate-BAM-A001.pdf",
  "line_boxes_count": 210
}
```

### 4.2 Query Document
`POST /api/v1/query?query=Who+issued+this+certificate?&doc_name=Certificate-BAM-A001.pdf&k=5`

Response sample:
```json
{
  "success": true,
  "query": "Who issued this certificate?",
  "doc_name": "Certificate-BAM-A001.pdf",
  "result": "Issued by ...",
  "evidence": {
    "doc_name": ["Certificate-BAM-A001.pdf"],
    "chunk_id": ["0", "3"]
  },
  "context_chunk_count": 5
}
```

## 5. Retrieval Context Format
Each retrieved chunk is concatenated into a single context string with this pattern:
```
DOC_NAME <source> CHUNK_ID <chunk_idx>:
<chunk text>(Header: <optional header>)
---
```
This context plus user query is injected into the prompt template: `prompts/assistant_prompt.txt` (hot-reloaded each call).

## 6. Files of Interest
| Purpose | File |
|---------|------|
| FastAPI entry | `backend/main.py` |
| Upload & query endpoints | `backend/endpoints/ingest_pdf.py` |
| OCR processing | `backend/core/doc_ocr.py` |
| Chunking logic | `backend/utils/chunking.py` |
| Vector DB wrapper | `backend/core/vec_db.py` |
| Assistant / LLM caller | `backend/core/assistant.py` |
| Prompt template | `backend/prompts/assistant_prompt.txt` |
| API test script | `backend/test_api.py` |
| Pipeline (offline) test | `backend/test_complete_pipeline.py` |

## 7. Testing
### 7.1 End-to-End (no server)
```bash
python test_complete_pipeline.py
```
### 7.2 API Tests
Run server, then in another shell:
```bash
python test_api.py
```
### 7.3 Curl Examples
```bash
curl -X POST -F "file=@/path/Certificate-BAM-A001.pdf" http://localhost:8880/api/v1/process-pdf

curl -X POST "http://localhost:8880/api/v1/query" \
  -G --data-urlencode "query=What type of certificate is this?" \
     --data-urlencode "doc_name=Certificate-BAM-A001.pdf" \
     --data-urlencode "k=5"
```

## 8. Data Model (Chroma Metadata)
Each chunk stored with metadata:
```json
{
  "source": "Certificate-BAM-A001.pdf",
  "chunk_idx": 0,
  "header": "<optional section header>",
  "bbox": "[[x0,y0,x1,y1], ...]",  // serialized list
  "page": 2
}
```
`bbox` converted back to list when retrieved.

## 9. Evidence Schema (Assistant Output)
```json
{
  "result": "Answer text...",
  "evidence": {
    "doc_name": ["Certificate-BAM-A001.pdf"],
    "chunk_id": ["4"]
  }
}
```
Arrays aligned index-wise.

## 10. Rebuilding Vector DB
Delete persistence folder:
```bash
rm -rf backend/vector_db
```
Re-ingest documents via `/process-pdf`.

## 11. Troubleshooting
| Issue | Cause | Fix |
|-------|-------|-----|
| 500 on /query | doc not ingested | Call `/process-pdf` first |
| No chunks returned | Overly small k or embedding mismatch | Increase `k`, verify model name |
| BBox empty | Non-text page or OCR failure | Ensure Tesseract installed |
| GPU not used | Torch CPU wheel | Install CUDA wheel |
| Prompt not updating | Old version cached | File hot-loaded; ensure editing correct path |

## 12. Future (GraphRAG Roadmap)
Planned additions:
- Entity & relation extraction per chunk
- Graph store (Neo4j or SQLite adjacency)
- Hybrid graph + vector traversal
- Multi-document reasoning with citation ranking

## 13. Changing Models
Edit initialization in `core/vec_db.py` and `core/assistant.py`.
For embeddings:
```python
VecDB(..., embedding_model="all-MiniLM-L12-v2")
```
For LLM model update settings (e.g. in `settings.py`).

## 14. License
See root `LICENSE`.

---
Questions or extensions needed—open an issue or request a feature.
