from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
import tempfile
import os
import io
import hashlib
import ast
import pymupdf  # PyMuPDF
from typing import List, Optional
from pydantic import BaseModel, Field
from core.doc_ocr import OCRDocProcessor
from core.vec_db import VecDB
from core.assistant import OllamaExtractor
from . import settings
from utils.highlighting import generate_highlight_pdf  # new reusable function

router = APIRouter()

# Storage directories
ORIGINAL_DIR = os.path.join("storage", "original_pdfs")
ANNOTATED_DIR = os.path.join("storage", "annotated_pdfs")
os.makedirs(ORIGINAL_DIR, exist_ok=True)
os.makedirs(ANNOTATED_DIR, exist_ok=True)

class HighlightRequest(BaseModel):
    doc_name: str = Field(..., description="Exact document name used at ingestion")
    chunk_ids: List[int] = Field(..., description="List of chunk indices to highlight")
    color: Optional[List[float]] = Field(default=None, description="RGB values 0-1, e.g. [1,0.85,0.2]")
    return_pdf: bool = Field(default=False, description="If true returns PDF bytes instead of JSON metadata only")

@router.post("/process-pdf")
async def process_pdf(file: UploadFile = File(...)):
    """
    Process a PDF file with OCR and return extracted text.
    """
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    try:
        # Create a temporary file to save the uploaded PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        # Persist original if not already stored
        stored_path = os.path.join(ORIGINAL_DIR, file.filename)
        if not os.path.exists(stored_path):
            with open(stored_path, 'wb') as outf:
                outf.write(content)
        # Initialize OCR processor with basic settings
        ocr_processor = OCRDocProcessor(settings)
        # Extract text from PDF
        extracted_text, line_boxes = ocr_processor.get_text_with_boxes(temp_file_path)
        # Initialize vector database
        vec_db = VecDB(
            settings=settings,
        )
        # Add document to vector database using line_boxes
        doc_name = file.filename
        vec_db.add_document(doc_name, line_boxes)
        # Clean up temporary file
        os.unlink(temp_file_path)
        return JSONResponse(content={
            "success": True,
            "filename": file.filename,
            "extracted_text": extracted_text.strip(),
            "text_length": len(extracted_text.strip()),
            "document_name": doc_name,
            "line_boxes_count": len(line_boxes),
            "stored_path": stored_path
        })
    except Exception as e:
        # Clean up temporary file if it exists
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")

@router.post("/query")
async def query_documents(query: str, doc_name: str, k: int = 5):
    """Query a specific document and return structured JSON answer."""
    try:
        vec_db = VecDB(
            settings=settings,
        )
        context, metadata = vec_db.get_context(query, doc_name)
        assistant = OllamaExtractor(settings)
        assistant_response = assistant.extract_from_document(query, context)
        # Ensure expected keys exist
        result = assistant_response.get("result", "") if isinstance(assistant_response, dict) else str(assistant_response)
        evidence = assistant_response.get("evidence", {}) if isinstance(assistant_response, dict) else {"doc_name": [], "chunk_id": []}
        return JSONResponse(content={
            "success": True,
            "query": query,
            "doc_name": doc_name,
            "result": result,
            "evidence": evidence,
            "context_chunk_count": len(metadata),
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error querying documents: {str(e)}")

@router.post("/highlight")
async def highlight_chunks(payload: HighlightRequest):
    """Generate (or reuse cached) annotated PDF with highlighted chunk rectangles (delegated)."""
    result = generate_highlight_pdf(payload.doc_name, payload.chunk_ids, payload.color)
    if not result.get("success"):
        error = result.get("error", "Highlight generation failed")
        status = 404 if "not found" in error.lower() or "no valid" in error.lower() else 500
        raise HTTPException(status_code=status, detail=error)

    if payload.return_pdf:
        try:
            with open(result["annotated_pdf_path"], 'rb') as f:
                import io
                return StreamingResponse(io.BytesIO(f.read()), media_type="application/pdf")
        except FileNotFoundError:
            raise HTTPException(status_code=500, detail="Annotated file missing after generation")

    # Strip internal path before returning
    result.pop("annotated_pdf_path", None)
    return JSONResponse(content=result)
