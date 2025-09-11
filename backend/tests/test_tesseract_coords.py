#!/usr/bin/env python3
"""
Test OCR coordinate extraction for image-based PDFs.
This tests the Tesseract OCR path specifically.
"""

import sys
import os
sys.path.append('.')

import pymupdf
import pytesseract
from PIL import Image
import cv2
import numpy as np
from utils import crop_right_rect

def test_tesseract_coordinates():
    """Test Tesseract OCR coordinate extraction."""
    test_pdf_path = "../test_files/Certificate-BAM-A001.pdf"
    output_path = "/home/lwei/Documents/AgentQI/vis_test/tesseract_coords.pdf"
    
    # Create output directory
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    if not os.path.exists(test_pdf_path):
        print(f"Test file not found: {test_pdf_path}")
        return
    
    print(f"Testing Tesseract OCR coordinates on: {test_pdf_path}")
    
    doc = pymupdf.open(test_pdf_path)
    
    # Process first page only for testing
    page = doc[0]
    page_rect = page.rect
    print(f"Page dimensions: {page_rect.width:.1f} x {page_rect.height:.1f}")
    
    # Convert page to image
    pix = page.get_pixmap(dpi=600)
    img_arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
        pix.height, pix.width, pix.n
    )
    print(f"Image dimensions: {img_arr.shape}")
    
    # Apply preprocessing (same as in OCR processor)
    img_arr = crop_right_rect(img_arr)
    gray = cv2.cvtColor(img_arr, cv2.COLOR_BGR2GRAY)
    denoised = cv2.fastNlMeansDenoising(gray, None, h=5, templateWindowSize=7, searchWindowSize=21)
    _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    print(f"Processed image dimensions: {binary.shape}")
    
    # Convert to PIL Image for Tesseract
    img = Image.fromarray(binary)
    
    # Get OCR data with bounding boxes
    print("Running Tesseract OCR...")
    ocr_data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
    
    print(f"OCR found {len(ocr_data['text'])} text elements")
    print(f" max confidence: {max([int(c) for c in ocr_data['conf']])} min confidence: {min([int(c) for c in ocr_data['conf']])} ")
    
    # Extract valid words with coordinates
    valid_words = []
    for i in range(len(ocr_data['text'])):
        conf = int(ocr_data['conf'][i]) 
        word = ocr_data['text'][i].strip()
        
        if word:  # Filter low confidence and empty words
            x = ocr_data['left'][i]
            y = ocr_data['top'][i]
            w = ocr_data['width'][i]
            h = ocr_data['height'][i]
            
            # Convert to x0, y0, x1, y1 format
            bbox = [x, y, x + w, y + h]
            
            valid_words.append({
                'text': word,
                'bbox': bbox,
                'confidence': conf
            })
            
            if len(valid_words) <= 10:  # Show first 10 words
                print(f"Word {len(valid_words):2d}: '{word:<15}' conf={conf:2d} bbox=({x:4d}, {y:4d}, {x+w:4d}, {y+h:4d})")
    
    print(f"Found {len(valid_words)} valid words")
    
    # Now visualize these coordinates on the original PDF
    print("Visualizing OCR coordinates on PDF...")
    
    # We need to scale coordinates from image space to PDF space
    img_height, img_width = binary.shape
    scale_x = page_rect.width / img_width
    scale_y = page_rect.height / img_height
    
    print(f"Scaling factors: x={scale_x:.3f}, y={scale_y:.3f}")
    
    # Draw bounding boxes
    for i, word_data in enumerate(valid_words):  # First 50 words
        bbox = word_data['bbox']
        word_text = word_data['text']
        
        # Scale coordinates to PDF space
        x0 = bbox[0] * scale_x
        y0 = bbox[1] * scale_y
        x1 = bbox[2] * scale_x
        y1 = bbox[3] * scale_y
        
        # Create rectangle
        rect = pymupdf.Rect(x0, y0, x1, y1)
        
        try:
            # Draw word boundary (red for OCR words)
            page.draw_rect(rect, color=(1, 0, 0), width=1)
            
            # Add word text for first 10 words
            page.insert_text(
                pymupdf.Point(x0, y0 - 2),
                word_text[:10],
                fontsize=6,
                color=(1, 0, 0)
            )
            print(f"Drew word '{word_text}' at PDF coords ({x0:.1f}, {y0:.1f}, {x1:.1f}, {y1:.1f})")
        
        except Exception as e:
            print(f"Error drawing word '{word_text}': {e}")
    
    # Save the visualized PDF
    try:
        doc.save(output_path)
        print(f"✅ Successfully saved OCR visualization to: {output_path}")
    except Exception as e:
        print(f"❌ Error saving PDF: {e}")
    finally:
        doc.close()

if __name__ == "__main__":
    print("=== TESSERACT OCR COORDINATE TEST ===")
    test_tesseract_coordinates()
    print("=== TEST COMPLETED ===")
