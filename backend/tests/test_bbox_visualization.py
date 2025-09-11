#!/usr/bin/env python3
"""
Test file to visualize bounding box outputs from OCR processing.
Located in tests/ directory to keep testing separate from core functionality.
"""

import os
import sys
import pymupdf

# Add parent directory to path to import from backend modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.doc_ocr import OCRDocProcessor

from settings import settings

def test_visualize_word_bboxes():
    """Test function to visualize word-level bounding boxes."""
    
    # Test file paths
    test_pdf = "../../test_files/Certificate-BAM-S030.pdf"
    output_pdf = "word_bbox_visualization.pdf"
    
    print(f"🔍 Testing word-level bounding box visualization")
    print(f"Input PDF: {test_pdf}")
    print(f"Output PDF: {output_pdf}")
    
    if not os.path.exists(test_pdf):
        print(f"❌ Test file not found: {test_pdf}")
        return None, None
    
    # Initialize OCR processor
    ocr_processor = OCRDocProcessor(settings)
    
    print("🔄 Extracting text and word bounding boxes...")
    
    # Extract text and word boxes using existing method
    extracted_text, word_boxes = ocr_processor.get_text(test_pdf, out_path='extr.txt', save_text=True)
    
    print(f"✅ Extracted {len(word_boxes)} word boxes")
    print(f"📄 Text length: {len(extracted_text)} characters")
    
    # Show first few words for debugging
    print("\n📝 First 10 word boxes:")
    for i, word_box in enumerate(word_boxes[:10]):
        bbox = word_box['bbox']
        text_preview = word_box['text'][:30]
        print(f"  {i:2d}: Page {word_box['page']} | '{text_preview}' | BBox: ({bbox[0]:.1f}, {bbox[1]:.1f}, {bbox[2]:.1f}, {bbox[3]:.1f})")
    
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
    
    print(f"\n🎨 Drawing {len(word_boxes)} word boundaries...")
    
    # Draw word boxes (limit to first 50 for clarity)
    for i, word_box in enumerate(word_boxes[:50]):
        page_num = word_box['page']
        bbox = word_box['bbox']
        word_text = word_box['text']
        
        if page_num >= len(doc):
            print(f"Warning: Page {page_num} not found in document")
            continue
            
        page = doc[page_num]
        
        # Create rectangle
        try:
            rect = pymupdf.Rect(bbox[0], bbox[1], bbox[2], bbox[3])
            
            # Use different colors for different pages
            color = page_colors[page_num % len(page_colors)]
            
            # Draw word boundary
            page.draw_rect(rect, color=color, width=1)
            
            # Add word number for first 20 words
            if i < 20:
                page.insert_text(
                    pymupdf.Point(bbox[0], bbox[1] - 2),
                    f"W{i}",
                    fontsize=6,
                    color=color
                )
                
        except Exception as e:
            print(f"Error drawing word {i}: {e}")
            continue
    
    # Add a legend on the first page
    if len(doc) > 0:
        first_page = doc[0]
        legend_y = 30
        first_page.insert_text(
            pymupdf.Point(30, legend_y),
            "Word-level Bounding Box Visualization (First 50 words)",
            fontsize=10,
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
    
    print(f"\n🎉 Visualization saved to: {output_pdf}")
    print(f"📊 Statistics:")
    print(f"   - Total words: {len(word_boxes)}")
    print(f"   - Words visualized: {min(50, len(word_boxes))}")
    print(f"   - Pages processed: {len(set(box['page'] for box in word_boxes))}")
    
    # Show page distribution
    page_counts = {}
    for box in word_boxes:
        page = box['page']
        page_counts[page] = page_counts.get(page, 0) + 1
    
    print(f"   - Words per page: {dict(sorted(page_counts.items()))}")
    
    return output_pdf, word_boxes

def test_text_extraction_only():
    """Quick test to check text extraction without visualization."""
    test_pdf = "../../test_files/Certificate-BAM-A001.pdf"
    
    if not os.path.exists(test_pdf):
        print(f"❌ Test file not found: {test_pdf}")
        return None
    
    print(f"🔍 Testing text extraction from: {test_pdf}")
    
    ocr_processor = OCRDocProcessor(settings)
    
    # Extract text and word boxes
    text, boxes = ocr_processor.get_text_with_boxes(test_pdf)
    
    print("📋 Extracted text preview (first 300 chars):")
    print("-" * 60)
    print(text[:300])
    print("-" * 60)
    print(f"Total text length: {len(text)} characters")
    print(f"Total word bboxes: {len(boxes)}")
    
    # Show extraction method used per page
    extraction_methods = {}
    for box in boxes:
        page = box['page']
        if page not in extraction_methods:
            extraction_methods[page] = 0
        extraction_methods[page] += 1
    
    print(f"Word boxes per page: {dict(sorted(extraction_methods.items()))}")
    
    return text, boxes

def test_compare_pdfs():
    """Test multiple PDFs to compare bounding box extraction."""
    test_files = [
        "../../test_files/Certificate-BAM-A001.pdf",
        "../../test_files/Certificate-BAM-S030.pdf", 
        "../../test_files/Certificate-BAM-M375a_Sample.pdf"
    ]
    
    print("🔍 Comparing bounding box extraction across multiple PDFs...")
    
    ocr_processor = OCRDocProcessor(settings)
    results = []
    
    for pdf_path in test_files:
        if not os.path.exists(pdf_path):
            print(f"❌ Skipping missing file: {pdf_path}")
            continue
            
        print(f"\n📄 Processing: {os.path.basename(pdf_path)}")
        
        try:
            text, boxes = ocr_processor.get_text_with_boxes(pdf_path)
            
            results.append({
                'file': os.path.basename(pdf_path),
                'text_length': len(text),
                'word_count': len(boxes),
                'pages': len(set(box['page'] for box in boxes)),
                'avg_words_per_page': len(boxes) / len(set(box['page'] for box in boxes)) if boxes else 0
            })
            
            print(f"   ✅ Text: {len(text)} chars, Words: {len(boxes)}, Pages: {len(set(box['page'] for box in boxes))}")
            
        except Exception as e:
            print(f"   ❌ Error processing {pdf_path}: {e}")
            continue
    
    # Summary table
    print("\n📊 COMPARISON SUMMARY:")
    print("-" * 80)
    print(f"{'File':<30} {'Text Len':<10} {'Words':<8} {'Pages':<6} {'Words/Page':<12}")
    print("-" * 80)
    
    for result in results:
        print(f"{result['file']:<30} {result['text_length']:<10} {result['word_count']:<8} {result['pages']:<6} {result['avg_words_per_page']:<12.1f}")
    
    return results

if __name__ == "__main__":
    print("🚀 Starting OCR bounding box visualization tests...")
    print("=" * 60)
    
    # Test 1: Text extraction only
    print("\n=== TEST 1: TEXT EXTRACTION ===")
    text_result = test_text_extraction_only()
    
    # Test 2: Word-level bounding box visualization  
    print("\n=== TEST 2: WORD BBOX VISUALIZATION ===")
    try:
        output_file, word_data = test_visualize_word_bboxes()
        if output_file and os.path.exists(output_file):
            print(f"✅ Visualization created: {output_file}")
        else:
            print("❌ Visualization failed")
    except Exception as e:
        print(f"❌ Visualization test failed: {e}")
        output_file = None
    
    # Test 3: Compare multiple PDFs
    print("\n=== TEST 3: MULTI-PDF COMPARISON ===")
    try:
        comparison_results = test_compare_pdfs()
    except Exception as e:
        print(f"❌ Comparison test failed: {e}")
    
    print("\n" + "=" * 60)
    print("✨ All tests complete!")
    
    if output_file:
        print(f"📖 Open '{output_file}' to see the word-level bounding boxes!")
    
    print("📂 Test outputs saved in tests/ directory")
