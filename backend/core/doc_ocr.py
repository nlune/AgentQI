import pytesseract
from PIL import Image, ImageEnhance
import cv2
import pymupdf
import numpy as np
from utils import crop_right_rect
from utils.process_text import process_text


class OCRDocProcessor:
    """
    OCR Document Processor for extracting text from images.
    """
    
    def __init__(self, settings):
        self.settings = settings
    
    def get_text_with_boxes(self, document_path: str) -> tuple[str, list]:
        """
        Extract text and line-level bounding boxes from PDF.
        Returns: (text, line_boxes) where line_boxes is list of dicts with 'text', 'bbox', 'page'
        """
        doc = pymupdf.open(document_path)
        result_text = ""
        all_line_boxes = []

        
        for page_idx, page in enumerate(doc):
            page_rect = page.rect
            print(f"Processing page {page_idx + 1}/{doc.page_count}")
            
            # Try text extraction first
            text = page.get_text(sort=True)
            if text.strip():
                # Get line-level bounding boxes from PyMuPDF using dict format
                text_dict = page.get_text("dict")
                
                for block in text_dict.get('blocks', []):
                    if block.get('type') == 0:  # Text block (not image)
                        for line in block.get('lines', []):
                            line_bbox = line.get('bbox', [])
                            if line_bbox:
                                # Extract text from all spans in this line
                                line_text = ""
                                for span in line.get('spans', []):
                                    span_text = span.get('text', '')
                                    line_text += span_text
                                
                                if line_text.strip():  # Only add non-empty lines
                                    all_line_boxes.append({
                                        'text': line_text.strip(),
                                        'bbox': list(line_bbox),
                                        'page': page_idx,
                                        'position_in_text': len(result_text) + text.find(line_text.strip()) if line_text.strip() in text else len(result_text),
                                        'line_no': len(all_line_boxes)  # Sequential line number
                                    })
                
                result_text += text + "\n"
            else:
                # OCR fallback
                pix = page.get_pixmap(dpi=600)
                img_arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
                    pix.height, pix.width, pix.n
                )
                if page_idx == 0:
                    img_arr = crop_right_rect(img_arr)
                    
                gray = cv2.cvtColor(img_arr, cv2.COLOR_BGR2GRAY)
                denoised = cv2.fastNlMeansDenoising(gray, None, h=5, templateWindowSize=7, searchWindowSize=21)
                _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                
                img = Image.fromarray(binary)
                
                # Calculate scaling factors from image space to PDF space
                img_height, img_width = binary.shape
                scale_x = page_rect.width / img_width
                scale_y = page_rect.height / img_height
                
                # Get OCR data with bounding boxes for line-level extraction
                ocr_data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
                
                n_boxes = len(ocr_data['level'])
                print(f"  OCR detected {n_boxes} text elements")
                print(f"  Image size: {img_width}x{img_height}, PDF size: {page_rect.width:.1f}x{page_rect.height:.1f}")
                print(f"  Scale factors: x={scale_x:.3f}, y={scale_y:.3f}")
                
                # Group words by lines (level 4 in tesseract hierarchy)
                current_line = None
                current_line_words = []
                page_text = ""
                
                for i in range(len(ocr_data['text'])):
                    level = ocr_data['level'][i]
                    conf = int(ocr_data['conf'][i])
                    text = ocr_data['text'][i].strip()
                    
                    if level == 4:  # Line level
                        # Save previous line if exists
                        if current_line is not None and current_line_words:
                            line_text = " ".join(current_line_words)
                            if line_text.strip():
                                all_line_boxes.append({
                                    'text': line_text.strip(),
                                    'bbox': current_line['bbox'],
                                    'page': page_idx,
                                    'position_in_text': len(result_text) + len(page_text),
                                    'line_no': len(all_line_boxes)
                                })
                                page_text += line_text + "\n"
                        
                        # Start new line
                        x, y, w, h = ocr_data['left'][i], ocr_data['top'][i], ocr_data['width'][i], ocr_data['height'][i]
                        pdf_x0 = x * scale_x
                        pdf_y0 = y * scale_y
                        pdf_x1 = (x + w) * scale_x
                        pdf_y1 = (y + h) * scale_y
                        
                        current_line = {
                            'bbox': [pdf_x0, pdf_y0, pdf_x1, pdf_y1]
                        }
                        current_line_words = []
                        
                    elif level == 5 and conf > 30:  # Word level with good confidence
                        if text and current_line is not None:
                            current_line_words.append(text)
                
                # Don't forget the last line
                if current_line is not None and current_line_words:
                    line_text = " ".join(current_line_words)
                    if line_text.strip():
                        all_line_boxes.append({
                            'text': line_text.strip(),
                            'bbox': current_line['bbox'],
                            'page': page_idx,
                            'position_in_text': len(result_text) + len(page_text),
                            'line_no': len(all_line_boxes)
                        })
                        page_text += line_text + "\n"
                
                result_text += page_text
        
        return result_text, all_line_boxes
    
    def get_text(self, document_path: str, out_path: str = None, save_text: bool = False) -> str:
        """Backward compatibility - just return text."""
        text, boxes = self.get_text_with_boxes(document_path)
    
    
        if save_text and out_path:
            with open(out_path, "w") as f:
                f.write(text)
                
            
        
        return text, boxes
