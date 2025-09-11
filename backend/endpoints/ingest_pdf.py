from backend.utils.chunking import split_wordboxes_chunks
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import tempfile
import os
from core.doc_ocr import OCRDocProcessor
from core.vec_db import VecDB
from . import settings

router = APIRouter()

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
        
        # Initialize OCR processor with basic settings
        ocr_processor = OCRDocProcessor(settings)
        
        # Extract text from PDF
        extracted_text, line_boxes = ocr_processor.get_text_with_boxes(temp_file_path)

        # Initialize vector database
        vec_db = VecDB(
            settings=settings,
            dbpath="./vector_db",
            collection_name="documents",
            embedding_model="all-MiniLM-L6-v2"
        )
        
        # Add document to vector database using line_boxes
        doc_name = file.filename
        vec_db.add_document(doc_name, line_boxes)
        
        # Clean up temporary file
        os.unlink(temp_file_path)
        
        return JSONResponse(
            content={
                "success": True,
                "filename": file.filename,
                "extracted_text": extracted_text.strip(),
                "text_length": len(extracted_text.strip()),
                "document_name": doc_name,
                "line_boxes_count": len(line_boxes),
            }
        )
        
    except Exception as e:
        # Clean up temporary file if it exists
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")