#!/usr/bin/env python3
"""Test the reusable generate_highlight_pdf function using VecDB retrieval metadata.

Flow:
1. Ingest PDF (if not already) via VecDB directly (avoids HTTP layer for speed).
2. Run a sample query through VecDB to obtain retrieved chunk metadata.
3. Collect chunk_idx values from metadata (authoritative) and highlight them.
4. Assert success or print diagnostic info.
"""
import code
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.doc_ocr import OCRDocProcessor
from core.vec_db import VecDB
from settings import settings
from utils.highlighting import generate_highlight_pdf

TEST_PDF = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "test_files", "Certificate-BAM-S030.pdf"))

def ensure_document_ingested(doc_path: str) -> str:
    doc_name = os.path.basename(doc_path)
    vec_db = VecDB(settings=settings) # Use centralized path
    if not vec_db.document_exists(doc_name):
        ocr = OCRDocProcessor(settings)
        _, line_boxes = ocr.get_text_with_boxes(doc_path)
        vec_db.add_document(doc_name, line_boxes)
    return doc_name

def test_highlight_generation():
    if not os.path.exists(TEST_PDF):
        print(f"Test PDF missing: {TEST_PDF}")
        return

    doc_name = ensure_document_ingested(TEST_PDF)

    query = "Transport and Storage requirements"
    vec_db = VecDB(settings=settings) # Use centralized path
    context, metadata = vec_db.get_context(query, doc_name)

    # Extract authoritative chunk indices from retrieval metadata
    retrieved_chunk_ids = sorted({m.get('chunk_idx') for m in metadata if m.get('chunk_idx') is not None})
    print("Retrieved chunk indices:", retrieved_chunk_ids)

    if not retrieved_chunk_ids:
        print("No chunks retrieved; cannot highlight.")
        return

    # Use first few for highlight demo
    chunk_ids = retrieved_chunk_ids[:3]
    print("Using chunk_ids for highlight:", chunk_ids)

    result = generate_highlight_pdf(doc_name, chunk_ids, color=[1, 0.85, 0.2])

    print("Highlight result:", result)
    assert result.get("success"), "Highlight generation failed"
    assert result.get("highlights"), "No highlights returned"

if __name__ == "__main__":
    test_highlight_generation()
