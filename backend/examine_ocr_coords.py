#!/usr/bin/env python3
"""
Test script to examine OCR coordinate extraction in detail.
This will help us understand what coordinates are being returned and why they might not be working.
"""

import sys
import os
sys.path.append('.')

import pymupdf
from core.doc_ocr import OCRDocProcessor
from settings import settings

def examine_ocr_coordinates():
    """Examine the OCR coordinates in detail."""
    test_pdf_path = "../test_files/Certificate-BAM-A001.pdf"
    
    if not os.path.exists(test_pdf_path):
        print(f"Test file not found: {test_pdf_path}")
        return
    
    print(f"Examining OCR coordinates for: {test_pdf_path}")
    
    # Initialize OCR processor
    ocr_processor = OCRDocProcessor(settings)
    
    # Check if the get_text_with_boxes method exists
    if not hasattr(ocr_processor, 'get_text_with_boxes'):
        print("❌ OCRDocProcessor doesn't have get_text_with_boxes method!")
        print("Available methods:")
        for attr in dir(ocr_processor):
            if not attr.startswith('_'):
                print(f"  - {attr}")
        return
    
    try:
        # Extract text and word boxes
        print("Extracting text and bounding boxes...")
        extracted_text, word_boxes = ocr_processor.get_text_with_boxes(test_pdf_path)
        
        print(f"✅ Successfully extracted {len(word_boxes)} word boxes")
        print(f"Text length: {len(extracted_text)} characters")
        
        # Examine the structure of word_boxes
        if word_boxes:
            print(f"\n=== WORD BOX STRUCTURE ===")
            first_box = word_boxes[0]
            print(f"First word box type: {type(first_box)}")
            print(f"First word box keys: {first_box.keys() if isinstance(first_box, dict) else 'Not a dict'}")
            print(f"First word box: {first_box}")
            
            # Check coordinate ranges
            print(f"\n=== COORDINATE ANALYSIS ===")
            all_pages = set()
            x_coords = []
            y_coords = []
            
            for i, word_box in enumerate(word_boxes):
                if isinstance(word_box, dict) and 'bbox' in word_box and 'page' in word_box:
                    page_num = word_box['page']
                    bbox = word_box['bbox']
                    
                    all_pages.add(page_num)
                    
                    if len(bbox) >= 4:
                        x_coords.extend([bbox[0], bbox[2]])
                        y_coords.extend([bbox[1], bbox[3]])
                        
                        # Show details for first 10 words
                        if i < 10:
                            word_text = word_box.get('text', 'N/A')
                            print(f"Word {i:2d}: '{word_text:<15}' page={page_num} bbox={bbox}")
            
            print(f"\nPages found: {sorted(all_pages)}")
            if x_coords and y_coords:
                print(f"X coordinate range: {min(x_coords):.1f} to {max(x_coords):.1f}")
                print(f"Y coordinate range: {min(y_coords):.1f} to {max(y_coords):.1f}")
            
            # Compare with actual PDF page dimensions
            print(f"\n=== PDF PAGE DIMENSIONS ===")
            doc = pymupdf.open(test_pdf_path)
            for page_num in range(len(doc)):
                page = doc[page_num]
                page_rect = page.rect
                print(f"Page {page_num}: {page_rect.width:.1f} x {page_rect.height:.1f}")
            doc.close()
            
        else:
            print("❌ No word boxes extracted!")
            
    except Exception as e:
        print(f"❌ Error extracting coordinates: {e}")
        import traceback
        traceback.print_exc()

def test_ocr_methods():
    """Test what OCR methods are actually available."""
    print("=== TESTING OCR METHODS ===")
    
    test_pdf_path = "../test_files/Certificate-BAM-A001.pdf"
    
    if not os.path.exists(test_pdf_path):
        print(f"Test file not found: {test_pdf_path}")
        return
    
    # Initialize OCR processor
    ocr_processor = OCRDocProcessor(settings)
    
    # Test regular get_text method
    print("Testing regular get_text method...")
    try:
        extracted_text = ocr_processor.get_text(test_pdf_path)
        print(f"✅ get_text worked, extracted {len(extracted_text)} characters")
        print(f"First 200 characters:\n{extracted_text[:200]}...")
    except Exception as e:
        print(f"❌ get_text failed: {e}")
    
    # Check what methods exist
    print(f"\nAvailable methods in OCRDocProcessor:")
    methods = [attr for attr in dir(ocr_processor) if not attr.startswith('_') and callable(getattr(ocr_processor, attr))]
    for method in methods:
        print(f"  - {method}")

def test_pymupdf_text_extraction():
    """Test PyMuPDF's built-in text extraction with coordinates."""
    print("=== TESTING PYMUPDF TEXT EXTRACTION ===")
    
    test_pdf_path = "../test_files/Certificate-BAM-A001.pdf"
    
    if not os.path.exists(test_pdf_path):
        print(f"Test file not found: {test_pdf_path}")
        return
    
    doc = pymupdf.open(test_pdf_path)
    
    for page_num in range(min(2, len(doc))):  # Test first 2 pages
        page = doc[page_num]
        page_rect = page.rect
        
        print(f"\n--- Page {page_num} (size: {page_rect.width:.1f} x {page_rect.height:.1f}) ---")
        
        # Test different text extraction methods
        
        # Method 1: get_text("words") - returns word-level coordinates
        print("Method 1: get_text('words')")
        try:
            words = page.get_text("words")
            print(f"Found {len(words)} words")
            for i, word_info in enumerate(words[:5]):  # First 5 words
                if len(word_info) >= 5:
                    x0, y0, x1, y1, word_text = word_info[:5]
                    print(f"  Word {i}: '{word_text}' bbox=({x0:.1f}, {y0:.1f}, {x1:.1f}, {y1:.1f})")
        except Exception as e:
            print(f"  Error: {e}")
        
        # Method 2: get_text("dict") - returns detailed structure
        print("\nMethod 2: get_text('dict')")
        try:
            text_dict = page.get_text("dict")
            block_count = len(text_dict.get('blocks', []))
            print(f"Found {block_count} text blocks")
            
            word_count = 0
            for block in text_dict.get('blocks', [])[:2]:  # First 2 blocks
                if 'lines' in block:
                    for line in block['lines'][:2]:  # First 2 lines per block
                        for span in line.get('spans', [])[:2]:  # First 2 spans per line
                            bbox = span.get('bbox', [])
                            text = span.get('text', '')
                            if text.strip():
                                print(f"  Span: '{text[:20]}...' bbox={bbox}")
                                word_count += len(text.split())
            
            print(f"Estimated word count: {word_count}")
        except Exception as e:
            print(f"  Error: {e}")
    
    doc.close()

if __name__ == "__main__":
    print("=== OCR COORDINATE EXAMINATION ===")
    examine_ocr_coordinates()
    
    print("\n" + "="*50)
    test_ocr_methods()
    
    print("\n" + "="*50)
    test_pymupdf_text_extraction()
    
    print("\n=== EXAMINATION COMPLETED ===")
