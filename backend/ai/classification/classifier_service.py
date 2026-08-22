"""
CertiTrust AI - Document Type Classification Service Module.
Performs Stage 1 preliminary OCR & weighted scoring to validate academic credentials.
Includes detailed diagnostic logging and strict credential gating.
"""

import mimetypes
from typing import Dict, Any
from ai.classification.classifier_utils import (
    extract_native_pdf_text,
    load_image_for_classification,
    inspect_visual_features,
    evaluate_two_stage_classification,
)
from ai.ocr.ocr_service import ocr_service
from app.utils.logger import logger


class DocumentTypeClassifierService:
    """
    Two-Stage Document Type Classification Service enforcing Stage 1 credential validation
    before allowing downstream pipeline execution.
    """

    def classify_document(self, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """
        Stage 1 Classifier:
        Runs OCR first, extracts native PDF text + image OCR text, evaluates positive & negative academic indicators,
        and classifies file into supported academic credential vs unsupported non-document media.
        """
        ext = filename.lower().split(".")[-1] if "." in filename else "unknown"
        mime_type, _ = mimetypes.guess_type(filename)
        mime_type = mime_type or "application/octet-stream"

        logger.info(f"==================================================")
        logger.info(f"STARTING STAGE 1 CLASSIFICATION FOR: '{filename}'")
        logger.info(f"File Extension: '.{ext}' | MIME Type: '{mime_type}' | File Size: {len(file_bytes)} bytes")
        logger.info(f"==================================================")

        try:
            # STEP 1: Execute OCR First (Native PDF Stream Text + PaddleOCR Image Text)
            logger.info("Stage 1: Executing preliminary OCR text extraction...")
            native_pdf_text = extract_native_pdf_text(file_bytes)

            ocr_res = ocr_service.process_document(file_bytes, filename)
            image_ocr_text = ""
            if isinstance(ocr_res, dict):
                pages = ocr_res.get("pages", [])
                if isinstance(pages, list):
                    image_ocr_text = " ".join([str(p.get("text", "")) for p in pages if isinstance(p, dict)])

            # Combine native digital text and image OCR text
            combined_ocr_text = f"{native_pdf_text}\n{image_ocr_text}".strip()
            text_length = len(combined_ocr_text)
            clean_text = "".join(combined_ocr_text.split())
            non_ws_count = len(clean_text)

            # Log OCR Text Diagnostic Results
            if text_length == 0:
                logger.warning(
                    f"Stage 1 OCR DIAGNOSTIC: OCR returned 0 characters for '{filename}'."
                )
            else:
                snippet = combined_ocr_text[:500].replace("\n", " ")
                logger.info(f"Stage 1 OCR DIAGNOSTIC: Extracted Text Length: {text_length} chars ({non_ws_count} non-whitespace chars).")
                logger.info(f"Stage 1 OCR DIAGNOSTIC: First 500 Chars Snippet: '{snippet}'")

            # STEP 2: Decode Visual Features
            image_bgr = load_image_for_classification(file_bytes, filename)
            visual_features = inspect_visual_features(image_bgr)

            # STEP 3: Evaluate Two-Stage Classification Model
            (
                doc_type,
                is_supported,
                confidence,
                rejection_detail,
                matched_positives,
                net_score,
                search_summary,
            ) = evaluate_two_stage_classification(
                visual_features=visual_features,
                combined_ocr_text=combined_ocr_text,
                filename=filename,
                file_bytes=file_bytes,
            )

            logger.info(f"Stage 1 KEYWORD DIAGNOSTIC: {search_summary}")
            logger.info(f"Stage 1 CLASSIFICATION SCORE: Net Score = {net_score} | Matched Positives = {matched_positives[:6]}")

            if not is_supported:
                logger.warning(f"STAGE 1 DECISION for '{filename}': REJECTED ('{doc_type}')")
                logger.warning(f"STAGE 1 REJECTION REASON: {rejection_detail}")
                logger.info(f"==================================================")

                return {
                    "success": False,
                    "document_type": "Not an Educational Credential",
                    "is_supported": False,
                    "confidence": confidence,
                    "reason": rejection_detail,
                    "message": "The uploaded file does not appear to be a supported educational or professional credential.",
                }

            logger.info(f"STAGE 1 DECISION for '{filename}': PASSED ('{doc_type}')")
            logger.info(f"Confidence: {confidence:.2f} | Reason: Valid '{doc_type}' verified.")
            logger.info(f"==================================================")

            # Package combined OCR result for pipeline reuse
            combined_ocr_payload = {
                "success": True,
                "pages": [{"page": 1, "text": combined_ocr_text}],
            }

            return {
                "success": True,
                "document_type": doc_type,
                "is_supported": True,
                "confidence": confidence,
                "reason": f"Uploaded file is a valid '{doc_type}'.",
                "message": "Supported academic credential verified.",
                "ocr_data": combined_ocr_payload,
            }

        except Exception as e:
            logger.error(f"Error during Document Type Classification for '{filename}': {str(e)}")
            return {
                "success": False,
                "document_type": "Not an Educational Credential",
                "is_supported": False,
                "confidence": 0.50,
                "reason": f"Error during classification: {str(e)}",
                "message": "The uploaded file does not appear to be a supported educational or professional credential.",
            }


# Global Singleton Service Instance
document_classifier_service = DocumentTypeClassifierService()
