#!/usr/bin/env python3
"""
Visualize chunk-level bounding boxes from text chunking.
"""

import os
import sys
import shutil
import pymupdf

# Add parent directory to path to import from backend modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.doc_ocr import OCRDocProcessor
from utils.chunking import split_wordboxes_chunks
from core.vec_db import VecDB
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

    # Initialize vector database and add document
    print("🔄 Setting up vector database...")
    
    
    vec_db = VecDB(settings)
    
    # Add document to vector database
    doc_name = "Certificate-BAM-A001"
    print(f"📝 Adding document '{doc_name}' to vector database...")
    vec_db.add_document(doc_name, line_boxes)
    
    # Query for Transport and Storage section
    print("🔍 Querying for 'Transport and Storage' section...")
    query = "Transport and Storage"
    context, retrieved_metadata = vec_db.get_context(query, doc_name)
    
    print(f"📝 Retrieved {len(retrieved_metadata)} chunks for query: '{query}'")
    print("\n📄 Retrieved context:")
    print("-" * 80)
    print(context[:500] + "..." if len(context) > 500 else context)
    print("-" * 80)
    
    # Get chunk indices that were retrieved
    retrieved_chunk_indices = set(metadata['chunk_idx'] for metadata in retrieved_metadata)
    print(f"🎯 Retrieved chunk indices: {sorted(retrieved_chunk_indices)}")
    
    # Prepare retrieved bbox data for visualization (bbox should already be converted to list in vec_db)
    retrieved_bboxes = []
    for metadata in retrieved_metadata:
        bbox = metadata.get('bbox', [])  # Should already be a list from vec_db conversion
        retrieved_bboxes.append({
            'bbox': bbox,
            'chunk_idx': metadata['chunk_idx'],
            'page': metadata['page'],
            'header': metadata.get('header', '')
        })
    
    print(f"🎯 Retrieved {len(retrieved_bboxes)} bboxes for visualization")

    # Show first few retrieved chunks for debugging
    print("\n📝 First 3 retrieved chunks:")
    for i, chunk_info in enumerate(retrieved_bboxes[:3]):
        bbox = chunk_info['bbox']
        chunk_idx = chunk_info['chunk_idx']
        header = chunk_info['header']
        print(f"  {i:2d}: Chunk #{chunk_idx} | Page {chunk_info['page']} | Header: '{header}' | BBox: ({bbox[0]:.1f}, {bbox[1]:.1f}, {bbox[2]:.1f}, {bbox[3]:.1f})")
    
    # Open PDF for annotation
    doc = pymupdf.open(test_pdf)
    
    # Color scheme for different pages and retrieval highlighting
    page_colors = [
        (1, 0, 0),     # Red for page 0
        (0, 1, 0),     # Green for page 1  
        (0, 0, 1),     # Blue for page 2
        (1, 1, 0),     # Yellow for page 3
        (1, 0, 1),     # Magenta for page 4
        (0, 1, 1),     # Cyan for page 5
    ]
    
    # Special color for retrieved chunks
    retrieved_color = (1, 0.5, 0)  # Orange for retrieved chunks
    
    print(f"\n🎨 Drawing {len(retrieved_bboxes)} retrieved chunk boundaries...")
    
    # Draw only retrieved chunk boxes
    for i, chunk_info in enumerate(retrieved_bboxes):
        bbox = chunk_info['bbox']
        chunk_idx = chunk_info['chunk_idx']
        page_num = chunk_info['page']

        if page_num >= len(doc):
            print(f"Warning: Page {page_num} not found in document")
            continue
            
        page = doc[page_num]
        
        # Create rectangle
        try:
            rect = pymupdf.Rect(bbox[0], bbox[1], bbox[2], bbox[3])
            
            # Use retrieved color
            color = retrieved_color
            width = 5  # Thicker line for retrieved chunks
            label = f"R{chunk_idx}"  # R for Retrieved with original chunk index
            
            # Draw chunk boundary
            page.draw_rect(rect, color=color, width=width)
            
            # Add chunk number/label
            page.insert_text(
                pymupdf.Point(bbox[0] - 25, bbox[1]),
                label,
                fontsize=10,
                color=color
            )
                
        except Exception as e:
            print(f"Error drawing retrieved chunk {chunk_idx}: {e}")
            continue
    
    # Add a legend on the first page
    if len(doc) > 0:
        first_page = doc[0]
        legend_y = 30
        first_page.insert_text(
            pymupdf.Point(30, legend_y),
            f"Chunk Visualization - Query: '{query}'",
            fontsize=12,
            color=(0, 0, 0)
        )
        
        # Add retrieved chunks legend
        legend_y += 20
        sample_rect = pymupdf.Rect(30, legend_y - 8, 50, legend_y)
        first_page.draw_rect(sample_rect, color=retrieved_color, fill=retrieved_color)
        first_page.insert_text(
            pymupdf.Point(55, legend_y),
            f"Retrieved Chunks ({len(retrieved_bboxes)})",
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
    print(f"   - Retrieved chunks: {len(retrieved_chunk_indices)} (highlighted in orange)")
    print(f"   - Query: '{query}'")
    print(f"   - Pages processed: {len(set(chunks_data['pages']))}")
    
    # Show page distribution for chunks
    page_counts = {}
    retrieved_page_counts = {}
    for i, page in enumerate(chunks_data['pages']):
        page_counts[page] = page_counts.get(page, 0) + 1
        if i in retrieved_chunk_indices:
            retrieved_page_counts[page] = retrieved_page_counts.get(page, 0) + 1
    
    print(f"   - Chunks per page: {dict(sorted(page_counts.items()))}")
    print(f"   - Retrieved chunks per page: {dict(sorted(retrieved_page_counts.items()))}")
    
    return output_pdf

if __name__ == "__main__":
    output_file = visualize_chunk_bboxes()
    if output_file:
        print(f"📖 Open '{output_file}' to see chunk bounding boxes!")
