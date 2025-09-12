#!/usr/bin/env python3
"""
Test script to demonstrate the complete pipeline:
1. OCR extraction with line-level bounding boxes
2. Chunking and vector database storage
3. AI assistant with structured responses and evidence tracking
"""

import os
import json
from core.doc_ocr import OCRDocProcessor
from core.vec_db import VecDB
from core.assistant import OllamaExtractor
from settings import settings

def test_complete_pipeline():
    """Test the complete document processing and query pipeline."""
    
    # Test file path
    test_pdf = "/home/lwei/Documents/AgentQI/test_files/Certificate-BAM-S030.pdf"

    if not os.path.exists(test_pdf):
        print(f"Test file not found: {test_pdf}")
        return
    
    print("=== AgentQI Complete Pipeline Test ===\n")
    
    # Step 1: OCR Processing
    print("1. Processing PDF with line-level OCR...")
    ocr_processor = OCRDocProcessor(settings)
    extracted_text, line_boxes = ocr_processor.get_text_with_boxes(test_pdf)
    
    print(f"   - Extracted text length: {len(extracted_text)} characters")
    print(f"   - Line boxes extracted: {len(line_boxes)}")
    print(f"   - First few lines:")
    for i, line_info in enumerate(line_boxes[:3]):
        print(f"     Line {i+1}: '{line_info['text'][:50]}...'")
    print()
    
    # Step 2: Vector Database Storage
    print("2. Storing in vector database...")
    vec_db = VecDB(settings=settings)
    
    doc_name = os.path.basename(test_pdf)
    vec_db.add_document(doc_name, line_boxes)
    print(f"   - Document '{doc_name}' added to vector database")
    print()
    
    # Step 3: Query and AI Assistant
    print("3. Testing AI assistant with queries...")
    assistant = OllamaExtractor(settings)
    
    test_queries = [
        "What type of certificate is this?",
        "What are the test parameters and their values?",
        "Who issued this certificate?"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n   Query {i}: {query}")
        print("   " + "="*50)
        
        # Query vector database using get_context
        context, metadata = vec_db.get_context(query, doc_name)
        
        # Directly use context (already formatted as DOC_NAME ... CHUNK_ID ...)
        response = assistant.extract_from_document(query, context)
        
        print(f"context {context}\n\n")  # Print a snippet of context for debugging
        
        print(f"   Response Type: {type(response)}")
        if isinstance(response, dict):
            print(f"   Answer: {response.get('result', 'No result field')}")
            evidence = response.get('evidence', {})
            if evidence.get('doc_name') or evidence.get('chunk_id'):
                print(f"   Evidence - Documents: {evidence.get('doc_name', [])}")
                print(f"   Evidence - Chunks: {evidence.get('chunk_id', [])}")
            else:
                print("   No evidence tracking in response")
        else:
            print(f"   Answer: {response}")
        print()
    
    print("=== Pipeline Test Complete ===")

if __name__ == "__main__":
    test_complete_pipeline()
