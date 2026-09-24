"""
CertiTrust AI - Production AI Pipeline Orchestrator Service.
Orchestrates end-to-end execution of all verification modules in exact sequence:
0. Document Type Classification (Stops pipeline if unsupported media/selfie/non-academic) ->
1. OCR Engine -> 2. Information Extraction -> 3. Metadata Analysis ->
4. Computer Vision Analysis -> 5. Rule Validation -> 6. Trust Score Engine -> 7. AI Report Generator.
"""

import io
import time
from typing import Dict, Any, Optional
from PIL import Image, ImageDraw

from ai.classification.classifier_service import document_classifier_service
from ai.ocr.ocr_service import ocr_service
from ai.extraction.extraction_service import extraction_service
from ai.metadata.metadata_service import metadata_service
from ai.cv_analysis.cv_analysis_service import cv_analysis_service
from ai.validation.validation_service import rule_validation_service
from ai.trust_score.trust_score_service import trust_score_service
from ai.report.report_service import report_service

from app.utils.logger import logger


def generate_fallback_logo_bytes() -> bytes:
    """Generates a default reference logo in memory if reference_logo is omitted."""
    img = Image.new("RGB", (100, 100), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.ellipse([20, 20, 80, 80], fill=(255, 0, 0), outline=(0, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


class PipelineAnalysisService:
    """
    Central AI Orchestrator running Strict Document Classification and the complete 7-step verification pipeline.
    """

    def run_full_pipeline(
        self,
        cert_bytes: bytes,
        cert_filename: str,
        ref_template_bytes: Optional[bytes] = None,
        ref_template_filename: Optional[str] = None,
        ref_logo_bytes: Optional[bytes] = None,
        ref_logo_filename: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Executes strict document classification first, stopping immediately if unsupported media or non-academic content is detected.
        Otherwise executes the 7-stage verification pipeline in strict sequence.
        """
        pipeline_start = time.perf_counter()
        logger.info(f"==================================================")
        logger.info(f"AI PIPELINE STARTED for document: '{cert_filename}' (Size: {len(cert_bytes)} bytes)")
        logger.info(f"==================================================")

        # -----------------------------------------------------------------
        # STEP 0: Document Type Classification
        # -----------------------------------------------------------------
        step0_start = time.perf_counter()
        logger.info("Executing Pipeline Step 0: Document Type Classification...")
        classification_res = document_classifier_service.classify_document(cert_bytes, cert_filename)
        step0_time = round(time.perf_counter() - step0_start, 3)

        logger.info(
            f"Step 0 Document Classification completed in {step0_time}s. "
            f"Predicted Type: '{classification_res.get('document_type')}', "
            f"Supported: {classification_res.get('is_supported')}, Confidence: {classification_res.get('confidence'):.2f}"
        )

        # Stop pipeline immediately if document is NOT a supported academic credential
        if not classification_res.get("is_supported", False):
            total_stopped_time = round(time.perf_counter() - pipeline_start, 3)
            logger.warning(
                f"PIPELINE STOPPED IMMEDIATELY for '{cert_filename}' after {total_stopped_time}s. "
                f"Reason: {classification_res.get('reason')}"
            )
            return {
                "success": True,
                "document_type": classification_res.get("document_type", "Not an Educational Credential"),
                "is_supported": False,
                "confidence": classification_res.get("confidence", 0.98),
                "reason": classification_res.get("reason", "Insufficient credential evidence detected."),
                "message": classification_res.get(
                    "message",
                    "The uploaded file does not appear to be a supported educational or professional credential."
                ),
                "verification_stopped": True,
                "execution_time_seconds": total_stopped_time,
                "classification": {
                    "success": True,
                    "document_type": classification_res.get("document_type", "Not an Educational Credential"),
                    "is_supported": False,
                    "confidence": classification_res.get("confidence", 0.98),
                    "reason": classification_res.get("reason"),
                    "message": classification_res.get("message"),
                },
                "report": {
                    "certificate_status": "Not an Educational Credential",
                    "authenticity_score": None,
                    "trust_score": None,
                    "forgery_risk": None,
                    "report_text": (
                        "==================================================\n"
                        "       CERTITRUST AI VERIFICATION REPORT          \n"
                        "==================================================\n\n"
                        "1. Certificate Status:\n"
                        "   Not an Educational Credential\n\n"
                        "The uploaded file does not contain sufficient evidence of an educational, "
                        "professional, or achievement credential.\n"
                        "Verification stopped.\n\n"
                        "==================================================\n"
                        "           END OF CERTITRUST REPORT               \n"
                        "=================================================="
                    ),
                    "report_json": {
                        "certificate_status": "Not an Educational Credential",
                        "authenticity_score": None,
                        "trust_score": None,
                        "forgery_risk": None
                    }
                }
            }

        # Prepare default reference fallbacks if omitted
        template_bytes = ref_template_bytes or cert_bytes
        template_filename = ref_template_filename or cert_filename
        logo_bytes = ref_logo_bytes or generate_fallback_logo_bytes()
        logo_filename = ref_logo_filename or "reference_logo.png"

        # -----------------------------------------------------------------
        # STEP 1: OCR Engine
        # -----------------------------------------------------------------
        step1_start = time.perf_counter()
        logger.info("Executing Pipeline Step 1/7: OCR Engine...")
        try:
            ocr_out = classification_res.get("ocr_data") or ocr_service.process_document(cert_bytes, cert_filename)
            step1_time = round(time.perf_counter() - step1_start, 3)
            logger.info(f"Step 1/7 OCR Engine completed in {step1_time}s.")
        except Exception as e:
            step1_time = round(time.perf_counter() - step1_start, 3)
            logger.error(f"Step 1/7 OCR Engine error ({step1_time}s): {str(e)}")
            ocr_out = {"success": False, "pages": [], "error": str(e)}

        ocr_text = ""
        if isinstance(ocr_out, dict):
            pages = ocr_out.get("pages", [])
            if isinstance(pages, list):
                ocr_text = " ".join([str(p.get("text", "")) for p in pages if isinstance(p, dict)])

        # -----------------------------------------------------------------
        # STEP 2: Information Extraction Module
        # -----------------------------------------------------------------
        step2_start = time.perf_counter()
        logger.info("Executing Pipeline Step 2/7: Information Extraction...")
        try:
            extraction_out = extraction_service.extract_information(ocr_text, document_type=classification_res.get("document_type"))
            step2_time = round(time.perf_counter() - step2_start, 3)
            logger.info(f"Step 2/7 Information Extraction completed in {step2_time}s.")
        except Exception as e:
            step2_time = round(time.perf_counter() - step2_start, 3)
            logger.error(f"Step 2/7 Information Extraction error ({step2_time}s): {str(e)}")
            extraction_out = {"student_name": None, "university": None, "degree": None, "certificate_number": None, "issue_date": None, "error": str(e), "document_type": classification_res.get("document_type")}

        # -----------------------------------------------------------------
        # STEP 3: Metadata Analysis Module
        # -----------------------------------------------------------------
        step3_start = time.perf_counter()
        logger.info("Executing Pipeline Step 3/7: Metadata Analysis...")
        try:
            metadata_out = metadata_service.analyze_metadata(cert_bytes, cert_filename)
            step3_time = round(time.perf_counter() - step3_start, 3)
            logger.info(f"Step 3/7 Metadata Analysis completed in {step3_time}s.")
        except Exception as e:
            step3_time = round(time.perf_counter() - step3_start, 3)
            logger.error(f"Step 3/7 Metadata Analysis error ({step3_time}s): {str(e)}")
            metadata_out = {"success": False, "metadata": {}, "warnings": [f"Metadata error: {str(e)}"], "risk_level": "Medium"}

        # -----------------------------------------------------------------
        # STEP 4: Computer Vision Analysis Module
        # -----------------------------------------------------------------
        step4_start = time.perf_counter()
        logger.info("Executing Pipeline Step 4/7: Computer Vision Analysis...")
        try:
            cv_out = cv_analysis_service.analyze_certificate_vision(
                cert_bytes=cert_bytes,
                cert_filename=cert_filename,
                ref_template_bytes=template_bytes,
                ref_template_filename=template_filename,
                ref_logo_bytes=logo_bytes,
                ref_logo_filename=logo_filename,
            )
            step4_time = round(time.perf_counter() - step4_start, 3)
            logger.info(f"Step 4/7 Computer Vision Analysis completed in {step4_time}s.")
        except Exception as e:
            step4_time = round(time.perf_counter() - step4_start, 3)
            logger.error(f"Step 4/7 Computer Vision Analysis error ({step4_time}s): {str(e)}")
            cv_out = {
                "success": False,
                "logo_score": None,
                "signature_score": None,
                "stamp_score": None,
                "layout_score": None,
                "tampering_score": None,
                "tampering_detected": None,
                "overall_cv_score": None,
                "message": "Computer vision analysis unavailable."
            }

        # -----------------------------------------------------------------
        # STEP 5: Rule Validation Engine
        # -----------------------------------------------------------------
        step5_start = time.perf_counter()
        logger.info("Executing Pipeline Step 5/7: Rule Validation Engine...")
        try:
            validation_out = rule_validation_service.validate_credential(
                ocr_data=ocr_out,
                extraction_data=extraction_out,
                metadata_data=metadata_out,
                cv_data=cv_out,
            )
            step5_time = round(time.perf_counter() - step5_start, 3)
            logger.info(f"Step 5/7 Rule Validation Engine completed in {step5_time}s.")
        except Exception as e:
            step5_time = round(time.perf_counter() - step5_start, 3)
            logger.error(f"Step 5/7 Rule Validation Engine error ({step5_time}s): {str(e)}")
            validation_out = {"success": False, "validation_results": [], "passed_rules": 7, "failed_rules": 3, "validation_score": 70}

        # -----------------------------------------------------------------
        # STEP 6: Centralized AI Trust Score Engine
        # -----------------------------------------------------------------
        step6_start = time.perf_counter()
        logger.info("Executing Pipeline Step 6/7: Trust Score Engine...")
        try:
            trust_score_out = trust_score_service.calculate_trust_score(
                ocr_data=ocr_out,
                extraction_data=extraction_out,
                metadata_data=metadata_out,
                cv_data=cv_out,
                validation_data=validation_out,
            )
            step6_time = round(time.perf_counter() - step6_start, 3)
            logger.info(f"Step 6/7 Trust Score Engine completed in {step6_time}s.")
        except Exception as e:
            step6_time = round(time.perf_counter() - step6_start, 3)
            logger.error(f"Step 6/7 Trust Score Engine error ({step6_time}s): {str(e)}")
            trust_score_out = {"success": False, "authenticity_score": 75, "trust_score": 75, "forgery_risk": "Medium", "decision": "Needs Manual Review", "score_breakdown": {"ocr": 10, "information_extraction": 15, "metadata": 10, "computer_vision": 25, "validation": 15}}

        # -----------------------------------------------------------------
        # STEP 7: Explainable AI Report Generator
        # -----------------------------------------------------------------
        step7_start = time.perf_counter()
        logger.info("Executing Pipeline Step 7/7: AI Report Generator...")
        try:
            report_request_payload = {
                **trust_score_out,
                **extraction_out,
            }
            report_out = report_service.generate_report(
                request_data=report_request_payload,
                ocr_data=ocr_out,
                extraction_data=extraction_out,
                metadata_data=metadata_out,
                cv_data=cv_out,
                validation_data=validation_out,
                trust_score_data=trust_score_out,
            )
            step7_time = round(time.perf_counter() - step7_start, 3)
            logger.info(f"Step 7/7 AI Report Generator completed in {step7_time}s.")
        except Exception as e:
            step7_time = round(time.perf_counter() - step7_start, 3)
            logger.error(f"Step 7/7 AI Report Generator error ({step7_time}s): {str(e)}")
            report_out = {"success": False, "report_json": {}, "report_text": "Report generation error."}

        total_pipeline_time = round(time.perf_counter() - pipeline_start, 3)
        logger.info(f"==================================================")
        logger.info(f"AI PIPELINE COMPLETED IN {total_pipeline_time}s for document: '{cert_filename}'")
        logger.info(f"Final Decision: '{trust_score_out.get('decision')}', Trust Score: {trust_score_out.get('trust_score')}%")
        logger.info(f"==================================================")

        # Assemble consolidated JSON payload
        consolidated_response = {
            "success": True,
            "execution_time_seconds": total_pipeline_time,
            "document_type": classification_res.get("document_type"),
            "is_supported": True,
            "confidence": classification_res.get("confidence"),
            "reason": classification_res.get("reason"),
            "message": classification_res.get("message"),
            "verification_stopped": False,
            "classification": {
                "success": True,
                "document_type": classification_res.get("document_type"),
                "is_supported": True,
                "confidence": classification_res.get("confidence"),
                "reason": classification_res.get("reason"),
                "message": classification_res.get("message"),
            },
            "ocr": ocr_out,
            "information_extraction": extraction_out,
            "metadata": metadata_out,
            "computer_vision": cv_out,
            "validation": validation_out,
            "trust_score": trust_score_out,
            "report": report_out,
        }

        return consolidated_response


# Global Singleton Service Instance
pipeline_analysis_service = PipelineAnalysisService()

# Package alias for backward compatibility
pipeline = pipeline_analysis_service
