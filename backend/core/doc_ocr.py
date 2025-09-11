import pytesseract
from PIL import Image, ImageEnhance
import cv2
import pymupdf
import numpy as np
from utils import crop_right_rect
from utils.process_text import process_text


class OCRDocProcessor():
    """
    OCR Document Processor for extracting text from images.
    """
    
    def __init__(self, settings):
        self.settings = settings
    
    def get_text_with_boxes(self, document_path: str) -> tuple[str, list]:
        """
        Extract text and word-level bounding boxes from PDF.
        Returns: (text, word_boxes) where word_boxes is list of dicts with 'text', 'bbox', 'page'
        """
        doc = pymupdf.open(document_path)
        result_text = ""
        all_word_boxes = []

        
        for page_idx, page in enumerate(doc):
            page_rect = page.rect
            print(f"Processing page {page_idx + 1}/{doc.page_count}")
            
            # Try text extraction first
            text = page.get_text(sort=True)
            if text.strip():
                # Get word-level bounding boxes from PyMuPDF
                words = page.get_text("words")  # Returns list of (x0, y0, x1, y1, "word", block_no, line_no, word_no)
                for word_info in words:
                    x0, y0, x1, y1, word_text, block_no, line_no, word_no = word_info
                    all_word_boxes.append({
                        'text': word_text,
                        'bbox': [x0, y0, x1, y1],
                        'page': page_idx,
                        'position_in_text': len(result_text) + text.find(word_text) if word_text in text else len(result_text)
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
                
                # Get OCR data with bounding boxes
                ocr_data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
                
                n_boxes = len(ocr_data['level'])
                print(f"  OCR detected {n_boxes} text elements")
                print(f"  Image size: {img_width}x{img_height}, PDF size: {page_rect.width:.1f}x{page_rect.height:.1f}")
                print(f"  Scale factors: x={scale_x:.3f}, y={scale_y:.3f}")
                
                page_text = ""
                for i in range(len(ocr_data['text'])):
                    if int(ocr_data['conf'][i]) > 30:  # Filter low confidence
                        word = ocr_data['text'][i].strip()
                        if word:
                            # Get image coordinates
                            x, y, w, h = ocr_data['left'][i], ocr_data['top'][i], ocr_data['width'][i], ocr_data['height'][i]
                            
                            # Scale to PDF coordinates
                            pdf_x0 = x * scale_x
                            pdf_y0 = y * scale_y
                            pdf_x1 = (x + w) * scale_x
                            pdf_y1 = (y + h) * scale_y
                            
                            all_word_boxes.append({
                                'text': word,
                                'bbox': [pdf_x0, pdf_y0, pdf_x1, pdf_y1],
                                'page': page_idx,
                                'position_in_text': len(result_text) + len(page_text)
                            })
                            page_text += word + " "
                
                result_text += page_text + "\n"
        
        return result_text, all_word_boxes
    
    def get_text(self, document_path: str, out_path: str = None, save_text: bool = False) -> str:
        """Backward compatibility - just return text."""
        text, boxes = self.get_text_with_boxes(document_path)
    
    
        if save_text and out_path:
            with open(out_path, "w") as f:
                f.write(text)
                
            
        
        return text, boxes
