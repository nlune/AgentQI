import pytest
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.doc_ocr import OCRDocProcessor
from utils.chunking import split_into_chunks
from utils.bbox_mapping import map_header_chunks_to_bboxes
from settings import settings

def test_bbox_chunk_mapping():
    """Test the bounding box mapping for chunks."""
    test_pdf_path = "../test_files/Certificate-BAM-A001.pdf"
    
    # Check if test file exists
    assert os.path.exists(test_pdf_path), f"Test file not found: {test_pdf_path}"
    
    # Initialize OCR processor
    ocr_processor = OCRDocProcessor(settings)
    
    # Extract text with bounding boxes
    extracted_text, word_boxes = ocr_processor.get_text_with_boxes(test_pdf_path)
    
    # Split into chunks using existing chunking function
    chunks, headers = split_into_chunks(extracted_text)
    
    # Map chunks to bounding boxes
    chunk_bboxes = map_header_chunks_to_bboxes(chunks, headers, word_boxes)
    
    # Basic assertions
    assert len(chunk_bboxes) == len(chunks), "Number of chunk bboxes should match number of chunks"
    assert len(chunk_bboxes) == len(headers), "Number of chunk bboxes should match number of headers"
    
    # Check that we have meaningful data
    chunks_with_boxes = [c for c in chunk_bboxes if c['page_bboxes']]
    assert len(chunks_with_boxes) > 0, "At least some chunks should have bounding boxes"
    
    # Print detailed results for manual verification
    print(f"\n=== CHUNK BOUNDING BOX TEST RESULTS ===")
    print(f"Total text length: {len(extracted_text)}")
    print(f"Total word boxes: {len(word_boxes)}")
    print(f"Total chunks: {len(chunks)}")
    print(f"Chunks with bounding boxes: {len(chunks_with_boxes)}")
    
    total_words_matched = sum(chunk['word_count'] for chunk in chunk_bboxes)
    print(f"Total words matched to chunks: {total_words_matched}")
    print(f"Match rate: {total_words_matched/len(word_boxes)*100:.1f}%")
    
    print(f"\n=== CHUNK BREAKDOWN ===")
    for i, chunk_data in enumerate(chunk_bboxes):
        header = chunk_data['header'][:40] + "..." if len(chunk_data['header']) > 40 else chunk_data['header']
        pages = [str(pb['page']) for pb in chunk_data['page_bboxes']]
        pages_str = ",".join(pages) if pages else "None"
        
        print(f"Chunk {i:2d}: {header:<45} | Words: {chunk_data['word_count']:3d} | "
              f"Pages: [{pages_str}] | Lines: {chunk_data['line_count']}")
        
        # Show first few lines of chunk text for verification
        chunk_lines = chunk_data['text'].strip().split('\n')[:3]
        for line in chunk_lines:
            if line.strip():
                print(f"         Text: {line.strip()[:60]}...")
        print()
    
    # Test specific chunk properties
    for chunk_data in chunk_bboxes:
        if chunk_data['page_bboxes']:
            # Each page bbox should have valid coordinates
            for page_bbox in chunk_data['page_bboxes']:
                bbox = page_bbox['bbox']
                assert len(bbox) == 4, "Bounding box should have 4 coordinates"
                assert bbox[0] <= bbox[2], "x1 should be <= x2"
                assert bbox[1] <= bbox[3], "y1 should be <= y2"
                assert all(coord >= 0 for coord in bbox), "All coordinates should be >= 0"

def test_header_detection():
    """Test header detection and bounding box mapping."""
    test_pdf_path = "../test_files/Certificate-BAM-A001.pdf"
    
    assert os.path.exists(test_pdf_path), f"Test file not found: {test_pdf_path}"
    
    # Initialize OCR processor
    ocr_processor = OCRDocProcessor(settings)
    
    # Extract text with bounding boxes
    extracted_text, word_boxes = ocr_processor.get_text_with_boxes(test_pdf_path)
    
    # Split into chunks
    chunks, headers = split_into_chunks(extracted_text)
    
    print(f"\n=== HEADER DETECTION TEST ===")
    print(f"Found {len(headers)} headers:")
    
    for i, header in enumerate(headers):
        if header.strip():
            print(f"Header {i}: '{header.strip()}'")
            
            # Find word boxes that might correspond to this header
            header_words = header.lower().split()
            matching_words = []
            
            for word_box in word_boxes:
                word = word_box['text'].lower()
                if word in header_words:
                    matching_words.append(word_box['text'])
            
            print(f"  Matched words: {matching_words[:5]}...")  # Show first 5 matches
        else:
            print(f"Header {i}: [EMPTY]")
    
    # Check that we detected some meaningful headers
    non_empty_headers = [h for h in headers if h.strip()]
    assert len(non_empty_headers) > 0, "Should detect at least some headers"

def test_save_bbox_data():
    """Test saving bounding box data for external visualization."""
    test_pdf_path = "../test_files/Certificate-BAM-A001.pdf"
    output_path = "bbox_test_data.json"
    
    assert os.path.exists(test_pdf_path), f"Test file not found: {test_pdf_path}"
    
    # Initialize OCR processor
    ocr_processor = OCRDocProcessor(settings)
    
    # Extract text with bounding boxes
    extracted_text, word_boxes = ocr_processor.get_text_with_boxes(test_pdf_path)
    
    # Split into chunks
    chunks, headers = split_into_chunks(extracted_text)
    
    # Map chunks to bounding boxes
    chunk_bboxes = map_header_chunks_to_bboxes(chunks, headers, word_boxes)
    
    # Save data for external visualization
    import json
    
    viz_data = {
        "source_pdf": test_pdf_path,
        "total_text_length": len(extracted_text),
        "total_word_boxes": len(word_boxes),
        "total_chunks": len(chunks),
        "chunk_bboxes": chunk_bboxes,
        "raw_word_boxes": word_boxes[:100]  # First 100 for inspection
    }
    
    with open(output_path, 'w') as f:
        json.dump(viz_data, f, indent=2)
    
    print(f"\n=== SAVED VISUALIZATION DATA ===")
    print(f"Bounding box data saved to: {output_path}")
    print("You can use this data to create custom visualizations")
    
    # Clean up
    if os.path.exists(output_path):
        os.remove(output_path)

if __name__ == "__main__":
    test_bbox_chunk_mapping()
    test_header_detection()
    test_save_bbox_data()
    print("\n✅ All bounding box tests completed!")
