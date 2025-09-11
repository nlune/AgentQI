#!/usr/bin/env python3
"""
Visualize chunk-level bounding boxes from text chunking.
"""

import os
import sys
import pymupdf

# Add parent directory to path to import from backend modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.doc_ocr import OCRDocProcessor
from utils.chunking import split_wordboxes_chunks
from settings import settings

def visualize_chunk_bboxes():
    """Create a visualization PDF showing chunk bounding boxes."""
    
    # Test file paths
    test_pdf = "../../test_files/Certificate-BAM-A001.pdf"
    output_pdf = "chunks_visualization.pdf"
    
    print(f"🔍 Creating chunk-level bounding box visualization")
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
    
    print("🔄 Creating chunks from line boxes...")
    chunks_data, headers = split_wordboxes_chunks(line_boxes)

    print(f"✅ Created {len(chunks_data['chunk_text'])} chunks")
    print(f"📊 Chunks: {len(chunks_data['chunk_text'])}, Bboxes: {len(chunks_data['bboxes'])}, Headers: {len(headers)}")

    # Show first few chunks for debugging
    print("\n📝 First 3 chunks:")
    for i in range(min(3, len(chunks_data['chunk_text']))):
        bbox = chunks_data['bboxes'][i]
        text_preview = chunks_data['chunk_text'][i][:60]
        print(f"  {i:2d}: Page {chunks_data['pages'][i]} | '{text_preview}...' | BBox: ({bbox[0]:.1f}, {bbox[1]:.1f}, {bbox[2]:.1f}, {bbox[3]:.1f})")
    
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
    
    print(f"\n🎨 Drawing {len(chunks_data['bboxes'])} chunk boundaries...")
    
    # Draw chunk boxes
    for i in range(len(chunks_data['bboxes'])):
        bbox = chunks_data['bboxes'][i]
        chunk_text = chunks_data['chunk_text'][i]
        page_num = chunks_data['pages'][i]

        if page_num >= len(doc):
            print(f"Warning: Page {page_num} not found in document")
            continue
            
        page = doc[page_num]
        
        # Create rectangle
        try:
            rect = pymupdf.Rect(bbox[0], bbox[1], bbox[2], bbox[3])
            
            # Use different colors for different pages
            color = page_colors[page_num % len(page_colors)]
            
            # Draw chunk boundary with thicker line
            page.draw_rect(rect, color=color, width=3)
            
            # Add chunk number
            page.insert_text(
                pymupdf.Point(bbox[0] - 25, bbox[1]),
                f"C{i}",
                fontsize=10,
                color=color
            )
                
        except Exception as e:
            print(f"Error drawing chunk {i}: {e}")
            continue
    
    # Add a legend on the first page
    if len(doc) > 0:
        first_page = doc[0]
        legend_y = 30
        first_page.insert_text(
            pymupdf.Point(30, legend_y),
            "Chunk-level Bounding Boxes",
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
    
    print(f"\n🎉 Chunk visualization saved to: {output_pdf}")
    print(f"📊 Statistics:")
    print(f"   - Total lines: {len(line_boxes)}")
    print(f"   - Total chunks: {len(chunks_data['bboxes'])}")
    print(f"   - Pages processed: {len(set(chunks_data['pages']))}")
    
    # Show page distribution for chunks
    page_counts = {}
    for page in chunks_data['pages']:
        page_counts[page] = page_counts.get(page, 0) + 1
    
    print(f"   - Chunks per page: {dict(sorted(page_counts.items()))}")
    
    return output_pdf

if __name__ == "__main__":
    output_file = visualize_chunk_bboxes()
    if output_file:
        print(f"📖 Open '{output_file}' to see chunk bounding boxes!")
