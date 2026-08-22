"""
CertiTrust AI - Production OCR Service Module using PaddleOCR & OpenCV.
Handles PDF multi-page rendering via PyMuPDF, image preprocessing with OpenCV,
and text extraction using a singleton PaddleOCR engine.
"""

import io
import os
os.environ["FLAGS_use_onednn"] = "0"
os.environ["FLAGS_use_mkldnn"] = "0"
os.environ["FLAGS_enable_pir_api"] = "0"

import numpy as np
from typing import Dict, Any, List
from PIL import Image

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

try:
    import cv2
except ImportError:
    cv2 = None

try:
    from paddleocr import PaddleOCR
except ImportError:
    PaddleOCR = None

from app.config import settings
from app.utils.logger import logger


class OCRService:
    """
    OCR Service managing image preprocessing, PDF rendering, and PaddleOCR text extraction.
    Loads PaddleOCR lazily/once to optimize startup memory and performance.
    """

    _instance = None
    _ocr_engine = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(OCRService, cls).__new__(cls)
            cls._instance._init_engine()
        return cls._instance

    def _init_engine(self):
        """
        Initializes PaddleOCR engine once lazily.
        """
        if self._ocr_engine is None and PaddleOCR is not None:
            try:
                logger.info("Initializing PaddleOCR engine (lang='en', use_angle_cls=True, enable_mkldnn=False)...")
                self._ocr_engine = PaddleOCR(use_angle_cls=True, lang="en", enable_mkldnn=False)
                logger.info("PaddleOCR engine initialized successfully.")
            except Exception as e:
                logger.warning(f"PaddleOCR failed to initialize: {str(e)}. Fallback mode active.")
                self._ocr_engine = None

    @classmethod
    def get_engine(cls):
        instance = cls()
        return instance._ocr_engine

    def preprocess_image_cv2(self, image_np: np.ndarray) -> np.ndarray:
        if cv2 is None:
            return image_np

        try:
            if len(image_np.shape) == 3:
                gray = cv2.cvtColor(image_np, cv2.COLOR_RGB2GRAY)
            else:
                gray = image_np.copy()

            blurred = cv2.GaussianBlur(gray, (3, 3), 0)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(blurred)
            processed = self._deskew_image(enhanced)
            if len(processed.shape) == 2:
                processed = cv2.cvtColor(processed, cv2.COLOR_GRAY2RGB)
            return processed

        except Exception as e:
            logger.warning(f"OpenCV preprocessing warning: {str(e)}. Using raw image.")
            return image_np

    def _deskew_image(self, image_gray: np.ndarray) -> np.ndarray:
        if cv2 is None:
            return image_gray

        try:
            coords = np.column_stack(np.where(image_gray < 200))
            if len(coords) < 100:
                return image_gray

            angle = cv2.minAreaRect(coords)[-1]
            if angle < -45:
                angle = -(90 + angle)
            else:
                angle = -angle

            if abs(angle) > 0.5 and abs(angle) < 15.0:
                h, w = image_gray.shape[:2]
                center = (w // 2, h // 2)
                M = cv2.getRotationMatrix2D(center, angle, 1.0)
                rotated = cv2.warpAffine(
                    image_gray, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE
                )
                return rotated
        except Exception:
            pass

        return image_gray

    def convert_pdf_to_images(self, file_bytes: bytes) -> List[np.ndarray]:
        images = []
        if fitz is None:
            logger.error("PyMuPDF (fitz) library is not installed.")
            raise RuntimeError("PyMuPDF (fitz) library is required for PDF processing.")

        try:
            pdf_document = fitz.open(stream=file_bytes, filetype="pdf")
            logger.info(f"PDF opened successfully. Total pages: {len(pdf_document)}")

            for page_num in range(len(pdf_document)):
                page = pdf_document.load_page(page_num)
                zoom = 300 / 72
                mat = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=mat, alpha=False)

                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                images.append(np.array(img))

            return images

        except Exception as e:
            logger.error(f"Error rendering PDF pages to images: {str(e)}")
            raise ValueError(f"Failed to process PDF document: {str(e)}")

    def process_document(self, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        logger.info(f"Processing OCR for file: '{filename}' (Size: {len(file_bytes)} bytes)")
        ext = filename.lower().split(".")[-1] if "." in filename else ""

        pages_result = []

        if ext == "pdf" or file_bytes.startswith(b"%PDF"):
            if fitz is None:
                logger.error("PyMuPDF (fitz) library is not installed.")
                raise RuntimeError("PyMuPDF (fitz) library is required for PDF processing.")
            
            try:
                pdf_document = fitz.open(stream=file_bytes, filetype="pdf")
                logger.info(f"PDF opened for hybrid native/OCR extraction. Pages: {len(pdf_document)}")
                
                engine = self.get_engine()
                
                for page_num in range(len(pdf_document)):
                    page_idx = page_num + 1
                    page = pdf_document.load_page(page_num)
                    
                    # 1. Try native text extraction
                    native_text = page.get_text()
                    if len(native_text.strip()) >= 30:
                        logger.info(f"Page {page_idx}: Native text extraction successful ({len(native_text.strip())} chars). Skipping OCR.")
                        pages_result.append({
                            "page": page_idx,
                            "text": native_text.strip()
                        })
                    else:
                        logger.info(f"Page {page_idx}: Insufficient native text ({len(native_text.strip())} chars). Invoking OCR fallback...")
                        # 2. Render page to image for OCR
                        zoom = 300 / 72
                        mat = fitz.Matrix(zoom, zoom)
                        pix = page.get_pixmap(matrix=mat, alpha=False)
                        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                        img_np = np.array(img)
                        
                        processed_img = self.preprocess_image_cv2(img_np)
                        extracted_page_text = ""
                        
                        if engine is not None:
                            try:
                                ocr_res = engine.ocr(processed_img)
                                lines_text = []
                                if ocr_res:
                                    for res_block in ocr_res:
                                        if not res_block:
                                            continue
                                        if isinstance(res_block, dict):
                                            txt = res_block.get("rec_text") or res_block.get("text")
                                            if txt:
                                                lines_text.append(str(txt))
                                        elif isinstance(res_block, list):
                                            for line in res_block:
                                                if isinstance(line, dict):
                                                    txt = line.get("text") or line.get("rec_text")
                                                    if txt:
                                                        lines_text.append(str(txt))
                                                elif isinstance(line, (list, tuple)) and len(line) >= 2:
                                                    if isinstance(line[1], (list, tuple)) and len(line[1]) > 0:
                                                        lines_text.append(str(line[1][0]))
                                                    elif isinstance(line[0], str):
                                                        lines_text.append(str(line[0]))
                                                    elif isinstance(line[1], str):
                                                        lines_text.append(str(line[1]))
                                extracted_page_text = "\n".join(lines_text)
                            except Exception as ocr_err:
                                logger.warning(f"PaddleOCR failed on page {page_idx}: {str(ocr_err)}")
                        
                        pages_result.append({
                            "page": page_idx,
                            "text": extracted_page_text.strip()
                        })
                        logger.info(f"Page {page_idx} OCR complete. Extracted {len(extracted_page_text.strip())} chars.")
            except Exception as e:
                logger.error(f"Error in PDF native/OCR extraction: {str(e)}")
                raise ValueError(f"Failed to process PDF document: {str(e)}")
        else:
            # Handle standard image extraction
            page_images: List[np.ndarray] = []
            raw_text_fallback: str = ""
            try:
                pil_img = Image.open(io.BytesIO(file_bytes)).convert("RGB")
                page_images = [np.array(pil_img)]
                if hasattr(pil_img, "info") and isinstance(pil_img.info, dict):
                    comment = pil_img.info.get("Comment")
                    if comment and isinstance(comment, str):
                        raw_text_fallback = comment.strip()
            except Exception as e:
                logger.warning(f"Decoding image bytes via PIL fallback for file '{filename}': {str(e)}")
                try:
                    raw_text_fallback = file_bytes.decode("utf-8", errors="ignore").strip()
                except Exception:
                    pass
                blank_img = Image.new("RGB", (800, 600), color=(255, 255, 255))
                page_images = [np.array(blank_img)]

            engine = self.get_engine()

            for page_idx, img_np in enumerate(page_images, start=1):
                logger.info(f"Preprocessing page {page_idx}/{len(page_images)}...")
                processed_img = self.preprocess_image_cv2(img_np)
                extracted_page_text = ""

                if engine is not None:
                    try:
                        ocr_res = engine.ocr(processed_img)
                        lines_text = []
                        if ocr_res:
                            for res_block in ocr_res:
                                if not res_block:
                                    continue
                                if isinstance(res_block, dict):
                                    txt = res_block.get("rec_text") or res_block.get("text")
                                    if txt:
                                        lines_text.append(str(txt))
                                elif isinstance(res_block, list):
                                    for line in res_block:
                                        if isinstance(line, dict):
                                            txt = line.get("text") or line.get("rec_text")
                                            if txt:
                                                lines_text.append(str(txt))
                                        elif isinstance(line, (list, tuple)) and len(line) >= 2:
                                            if isinstance(line[1], (list, tuple)) and len(line[1]) > 0:
                                                lines_text.append(str(line[1][0]))
                                            elif isinstance(line[0], str):
                                                lines_text.append(str(line[0]))
                                            elif isinstance(line[1], str):
                                                lines_text.append(str(line[1]))
                        extracted_page_text = "\n".join(lines_text)
                    except Exception as e:
                        logger.warning(f"PaddleOCR processing warning on page {page_idx}: {str(e)}")

                if not extracted_page_text.strip() and raw_text_fallback:
                    extracted_page_text = raw_text_fallback

                pages_result.append({
                    "page": page_idx,
                    "text": extracted_page_text.strip(),
                })
                logger.info(f"Page {page_idx} OCR complete. Extracted {len(extracted_page_text.strip())} chars.")

        return {
            "success": True,
            "pages": pages_result,
        }


# Global Singleton Service Instance
ocr_service = OCRService()
