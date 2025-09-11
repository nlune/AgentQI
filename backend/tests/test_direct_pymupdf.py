#!/usr/bin/env python3
"""
Direct test of PyMuPDF word extraction and visualization.
This bypasses our OCR processor and directly tests PyMuPDF's word extraction.
"""

import sys
import os
sys.path.append('.')

import pymupdf

def test_pymupdf_word_visualization():
    """Test PyMuPDF word extraction and visualize directly."""
    test_pdf_path = "../test_files/Certificate-BAM-S030.pdf"
    output_path = "/home/lwei/Documents/AgentQI/vis_test/pymupdf_words.pdf"
    
    # Create output directory
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    if not os.path.exists(test_pdf_path):
        print(f"Test file not found: {test_pdf_path}")
        return
    
    print(f"Testing PyMuPDF word extraction on: {test_pdf_path}")
    
    # Open PDF
    doc = pymupdf.open(test_pdf_path)
    print(f"PDF has {len(doc)} pages")
    
    total_words = 0
    
    # Process each page
    for page_num in range(len(doc)):
        page = doc[page_num]
        page_rect = page.rect
        
        print(f"\nPage {page_num}: size = {page_rect.width:.1f} x {page_rect.height:.1f}")
        
        # Extract words with coordinates
        words = page.get_text("words")
        print(f"Found {len(words)} words on page {page_num}")
        
        # Colors for different pages
        page_colors = [(1, 0, 0), (0, 1, 0), (0, 0, 1), (1, 1, 0), (1, 0, 1), (0, 1, 1)]
        color = page_colors[page_num % len(page_colors)]
        
        # Draw bounding boxes for each word
        for i, word_info in enumerate(words):
            if len(word_info) >= 5:
                x0, y0, x1, y1, word_text = word_info[:5]
                
                # Validate coordinates
                if x0 >= x1 or y0 >= y1:
                    print(f"  Warning: Invalid word bbox for '{word_text}': ({x0}, {y0}, {x1}, {y1})")
                    continue
                
                # Check if coordinates are within page bounds
                if x0 < 0 or y0 < 0 or x1 > page_rect.width or y1 > page_rect.height:
                    print(f"  Warning: Word '{word_text}' outside page bounds: ({x0:.1f}, {y0:.1f}, {x1:.1f}, {y1:.1f})")
                    # Clamp to page bounds
                    x0 = max(0, min(x0, page_rect.width))
                    y0 = max(0, min(y0, page_rect.height))
                    x1 = max(x0, min(x1, page_rect.width))
                    y1 = max(y0, min(y1, page_rect.height))
                
                # Create rectangle for word
                rect = pymupdf.Rect(x0, y0, x1, y1)
                
                try:
                    # Draw word boundary
                    page.draw_rect(rect, color=color, width=1)
                    
                    # Add word text for first 10 words to verify alignment
                    if i < 10:
                        page.insert_text(
                            pymupdf.Point(x0, y0 - 2),
                            word_text[:10],  # Truncate long words
                            fontsize=6,
                            color=color
                        )
                        print(f"  Word {i:2d}: '{word_text:<15}' bbox=({x0:.1f}, {y0:.1f}, {x1:.1f}, {y1:.1f})")
                
                except Exception as e:
                    print(f"  Error drawing word '{word_text}': {e}")
                    continue
        
        total_words += len(words)
    
    # Save the visualized PDF
    try:
        doc.save(output_path)
        print(f"\n✅ Successfully saved word visualization to: {output_path}")
        print(f"Total words processed: {total_words}")
        
        # Verify the file was created
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            print(f"✅ File created successfully, size: {file_size} bytes")
        else:
            print("❌ File was not created")
            
    except Exception as e:
        print(f"❌ Error saving PDF: {e}")
    finally:
        doc.close()

def test_sample_coordinates():
    """Extract and display sample coordinates for analysis."""
    test_pdf_path = "../test_files/Certificate-BAM-A001.pdf"
    
    if not os.path.exists(test_pdf_path):
        print(f"Test file not found: {test_pdf_path}")
        return
    
    print(f"Extracting sample coordinates from: {test_pdf_path}")
    
    doc = pymupdf.open(test_pdf_path)
    
    # Look at first page only
    page = doc[0]
    page_rect = page.rect
    words = page.get_text("words")
    
    print(f"Page 0 dimensions: {page_rect.width:.1f} x {page_rect.height:.1f}")
    print(f"Found {len(words)} words")
    
    print(f"\nFirst 20 words with coordinates:")
    for i, word_info in enumerate(words[:20]):
        if len(word_info) >= 5:
            x0, y0, x1, y1, word_text = word_info[:5]
            width = x1 - x0
            height = y1 - y0
            print(f"{i:2d}: '{word_text:<15}' pos=({x0:6.1f}, {y0:6.1f}) size=({width:5.1f} x {height:4.1f})")
    
    doc.close()

if __name__ == "__main__":
    print("=== DIRECT PYMUPDF WORD VISUALIZATION TEST ===")
    test_sample_coordinates()
    
    print("\n" + "="*50)
    test_pymupdf_word_visualization()
    
    print("\n=== TEST COMPLETED ===")
