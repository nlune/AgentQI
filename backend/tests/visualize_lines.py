#!/usr/bin/env python3
"""
Visualize individual line-level bounding boxes from OCR processing.
"""

import os
import sys
import pymupdf

# Add parent directory to path to import from backend modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.doc_ocr import OCRDocProcessor
from settings import settings

def visualize_line_bboxes():
    """Create a visualization PDF showing individual line bounding boxes."""
    
    # Test file paths
    test_pdf = "../../test_files/Certificate-BAM-A001.pdf"
    output_pdf = "lines_visualization.pdf"
    
    print(f"🔍 Creating line-level bounding box visualization")
    print(f"Input PDF: {test_pdf}")
    print(f"Output PDF: {output_pdf}")
    
    if not os.path.exists(test_pdf):
        print(f"❌ Test file not found: {test_pdf}")
        return None
    
    # Initialize OCR processor
    ocr_processor = OCRDocProcessor(settings)
    
    print("🔄 Extracting text and line bounding boxes...")
    
    # Extract text and line boxes using the new method
    extracted_text, line_boxes = ocr_processor.get_text_with_boxes(test_pdf)
    
    print(f"✅ Extracted {len(line_boxes)} line boxes")
    
    # Show first few lines for debugging
    print("\n📝 First 5 line boxes:")
    for i, line_box in enumerate(line_boxes[:5]):
        bbox = line_box['bbox']
        text_preview = line_box['text'][:40]
        print(f"  {i:2d}: Page {line_box['page']} | '{text_preview}' | BBox: ({bbox[0]:.1f}, {bbox[1]:.1f}, {bbox[2]:.1f}, {bbox[3]:.1f})")
    
    # Open PDF for annotation
    doc = pymupdf.open(test_pdf)
    
    # Color scheme for different pages
    page_colors = [
        (1, 0, 0),     # Red for page 0
        (0, 1, 0),     # Green for page 1  
        (0, 0, 1),     # Blue for page 2
        (1, 1, 0),     # Yellow for page 3
        (1, 0, 1),     # Magenta for page 4
        (0, 1, 1),     # Cyan for page 5
    ]
    
    print(f"\n🎨 Drawing {len(line_boxes)} line boundaries...")
    
    # Draw line boxes
    for i, line_box in enumerate(line_boxes):
        page_num = line_box['page']
        bbox = line_box['bbox']
        line_text = line_box['text']

        if page_num >= len(doc):
            print(f"Warning: Page {page_num} not found in document")
            continue
            
        page = doc[page_num]
        
        # Create rectangle
        try:
            rect = pymupdf.Rect(bbox[0], bbox[1], bbox[2], bbox[3])
            
            # Use different colors for different pages
            color = page_colors[page_num % len(page_colors)]
            
            # Draw line boundary
            page.draw_rect(rect, color=color, width=1)
            
            # Add line number for first 10 lines
            if i < 10:
                page.insert_text(
                    pymupdf.Point(bbox[0] - 15, bbox[1]),
                    f"L{i}",
                    fontsize=6,
                    color=color
                )
                
        except Exception as e:
            print(f"Error drawing line {i}: {e}")
            continue
    
    # Add a legend on the first page
    if len(doc) > 0:
        first_page = doc[0]
        legend_y = 30
        first_page.insert_text(
            pymupdf.Point(30, legend_y),
            "Individual Line Bounding Boxes",
            fontsize=12,
            color=(0, 0, 0)
        )
        
        for page_idx in range(min(len(doc), len(page_colors))):
            color = page_colors[page_idx]
            legend_y += 15
            # Draw color sample
            sample_rect = pymupdf.Rect(30, legend_y - 8, 50, legend_y)
            first_page.draw_rect(sample_rect, color=color, fill=color)
            # Add text
            first_page.insert_text(
                pymupdf.Point(55, legend_y),
                f"Page {page_idx + 1}",
                fontsize=8,
                color=(0, 0, 0)
            )
    
    # Save highlighted PDF
    doc.save(output_pdf)
    doc.close()
    
    print(f"\n🎉 Line visualization saved to: {output_pdf}")
    print(f"📊 Statistics:")
    print(f"   - Total lines: {len(line_boxes)}")
    print(f"   - Pages processed: {len(set(box['page'] for box in line_boxes))}")
    
    # Show page distribution
    page_counts = {}
    for box in line_boxes:
        page = box['page']
        page_counts[page] = page_counts.get(page, 0) + 1
    
    print(f"   - Lines per page: {dict(sorted(page_counts.items()))}")
    
    return output_pdf

if __name__ == "__main__":
    output_file = visualize_line_bboxes()
    if output_file:
        print(f"📖 Open '{output_file}' to see individual line bounding boxes!")
