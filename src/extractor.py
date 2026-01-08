import fitz  # PyMuPDF
# import easyocr (Moved to __init__ for performance)
import numpy as np
import os
from PIL import Image
from loguru import logger
from typing import Optional, List, Dict, Any
import io

class PDFExtractor:
    """
    Handles robust extraction of text and spatial data from PDFs.
    """
    
    def __init__(self):
        # Heavy import moved here to speed up UI startup
        import easyocr
        logger.info("Initializing OCR Engine (EasyOCR)...")
        # detail=1 gives us the bounding boxes
        self.reader = easyocr.Reader(['en'], gpu=False)

    def extract_structured_data(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Extracts text along with its bounding boxes (x, y, w, h).
        Returns a list of elements: [{"text": str, "x": float, "y": float, "w": float, "h": float}]
        """
        all_elements = []
        try:
            doc = fitz.open(file_path)
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                # Try digital text first
                words = page.get_text("words") # (x0, y0, x1, y1, "word", block_no, line_no, word_no)
                
                if len(words) > 10:
                    # Digital PDF
                    for w in words:
                        all_elements.append({
                            "text": w[4],
                            "x": w[0],
                            "y": w[1],
                            "w": w[2] - w[0],
                            "h": w[3] - w[1],
                            "page": page_num
                        })
                else:
                    # Scanned PDF - Use OCR
                    logger.info(f"Page {page_num + 1} appears scanned. Using OCR...")
                    ocr_results = self._perform_detailed_ocr(page)
                    for res in ocr_results:
                        box = res[0] # [[x1,y1], [x2,y1], [x2,y2], [x1,y2]]
                        text = res[1]
                        
                        x = box[0][0]
                        y = box[0][1]
                        w = box[1][0] - x
                        h = box[2][1] - y
                        
                        all_elements.append({
                            "text": text,
                            "x": x,
                            "y": y,
                            "w": w,
                            "h": h,
                            "page": page_num
                        })
            
            doc.close()
            return all_elements
            
        except Exception as e:
            logger.error(f"Failed structured extraction from {file_path}: {e}")
            return []

    def _perform_detailed_ocr(self, page) -> List:
        """
        Performs OCR and returns detailed bounding box info.
        """
        try:
            mat = fitz.Matrix(2.0, 2.0) # High res for better box accuracy
            pix = page.get_pixmap(matrix=mat, colorspace=fitz.csGRAY)
            
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            img_array = np.array(img)
            
            # detail=1 returns [[box], text, confidence]
            results = self.reader.readtext(img_array, detail=1)
            return results
        except Exception as e:
            logger.error(f"Detailed OCR failed: {e}")
            return []

    # Keeping legacy method for compatibility if needed, but redirects to structured
    def extract_text(self, file_path: str) -> str:
        elements = self.extract_structured_data(file_path)
        return " ".join([e['text'] for e in elements])
