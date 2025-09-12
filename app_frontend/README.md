# AgentQI Frontend (Vite + React)

Minimal UI for the three backend endpoints:
- `POST /api/v1/process-pdf` — upload PDF and ingest
- `POST /api/v1/query` — ask a question about the ingested PDF
- `POST /api/v1/highlight` — generate highlighted PDF for retrieved chunk ids

The left panel shows the PDF (original first, then the highlighted file). The right panel is a chat for the query and answer.

## Run (dev)
1. Start the backend (FastAPI) on `http://localhost:8000`.
2. From `app_frontend/` run:
   - `npm run dev`
3. In the top-right API base box set either:
   - `/api/v1` to use the Vite dev proxy (no CORS), or
   - `http://localhost:8000/api/v1` to call the backend directly.

Dev proxy targets `VITE_PROXY_TARGET` (default `http://localhost:8000`) for `'/api/v1'` and `'/pdfs'`.

## Build
`npm run build` then serve `dist/` with any static server. Set the API base to your backend URL.

## Notes
- Highlight response returns `annotated_pdf_url` (relative). The app derives the API origin from the API base and swaps the viewer to the annotated PDF automatically.
- Evidence `chunk_id` values from `/query` are strings; the app converts them to integers for `/highlight`.
