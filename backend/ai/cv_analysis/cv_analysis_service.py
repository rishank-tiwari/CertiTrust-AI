"""
CertiTrust AI - Production Integrated Computer Vision Analysis Engine.
Combines Logo Verification, Signature Detection, Stamp/Seal Detection,
Layout Similarity (SSIM + ORB), and Tampering Detection into a single weighted score engine.
"""

from typing import Dict, Any
from ai.cv_analysis.cv_analysis_utils import (
    load_image_or_pdf,
    detect_signature,
    detect_stamp,
    evaluate_layout_similarity,
    detect_tampering_artifacts,
)
from ai.cv_analysis.logo.logo_utils import (
    perform_template_matching,
    perform_orb_feature_matching,
    calculate_hybrid_similarity,
)
from app.utils.logger import logger


class IntegratedCVAnalysisService:
    """
    Unified Computer Vision Analysis Engine executing all 5 visual document verification stages.
    """

    def analyze_certificate_vision(
        self,
        cert_bytes: bytes,
        cert_filename: str,
        ref_template_bytes: bytes,
        ref_template_filename: str,
        ref_logo_bytes: bytes,
        ref_logo_filename: str,
    ) -> Dict[str, Any]:
        """
        Executes end-to-end Computer Vision analysis:
        1. Logo Verification (logo_score)
        2. Signature Detection (signature_detected, signature_score)
        3. Stamp Detection (stamp_detected, stamp_score)
        4. Layout Similarity (layout_score)
        5. Tampering Detection (tampering_score, tampering_detected)
        6. Overall CV Score calculation
        """
        logger.info(f"Starting Integrated CV Analysis: Cert='{cert_filename}', Ref Template='{ref_template_filename}', Ref Logo='{ref_logo_filename}'")

        try:
            # Step 0: Load and Decode all documents into OpenCV BGR images (handles PDF rendering)
            cert_img = load_image_or_pdf(cert_bytes, cert_filename)
            ref_template_img = load_image_or_pdf(ref_template_bytes, ref_template_filename)
            ref_logo_img = load_image_or_pdf(ref_logo_bytes, ref_logo_filename)

            logger.info("Decoded all certificate, template, and logo images successfully.")

            # 1. Logo Verification (Reuse existing logo matching logic)
            template_score, _ = perform_template_matching(cert_img, ref_logo_img)
            feature_score = perform_orb_feature_matching(cert_img, ref_logo_img)
            logo_score_pct, _, _ = calculate_hybrid_similarity(template_score, feature_score)
            logo_score = int(round(logo_score_pct))
            logger.info(f"CV Stage 1 - Logo Score: {logo_score}")

            # 2. Signature Detection
            signature_detected, signature_score = detect_signature(cert_img)
            logger.info(f"CV Stage 2 - Signature Detected: {signature_detected}, Score: {signature_score}")

            # 3. Stamp Detection
            stamp_detected, stamp_score = detect_stamp(cert_img)
            logger.info(f"CV Stage 3 - Stamp Detected: {stamp_detected}, Score: {stamp_score}")

            # 4. Layout Similarity (SSIM + ORB Homography)
            layout_score = evaluate_layout_similarity(cert_img, ref_template_img)
            logger.info(f"CV Stage 4 - Layout Similarity Score: {layout_score}")

            # 5. Tampering Detection (Blur, Compression & Artifacts)
            tampering_score, tampering_detected = detect_tampering_artifacts(cert_img)
            logger.info(f"CV Stage 5 - Tampering Score: {tampering_score}, Tampering Detected: {tampering_detected}")

            # 6. Overall Weighted CV Score Calculation
            # Weights: 25% Logo + 25% Signature + 20% Stamp + 20% Layout + 10% (100 - Tampering)
            tamper_safety = max(0, 100 - tampering_score)
            weighted_overall = (
                (logo_score * 0.25)
                + (signature_score * 0.25)
                + (stamp_score * 0.20)
                + (layout_score * 0.20)
                + (tamper_safety * 0.10)
            )
            overall_cv_score = int(round(min(100, max(0, weighted_overall))))

            logger.info(f"Integrated CV Analysis Complete. Overall CV Score: {overall_cv_score}")

            return {
                "success": True,
                "logo_score": logo_score,
                "signature_score": signature_score,
                "stamp_score": stamp_score,
                "layout_score": layout_score,
                "tampering_score": tampering_score,
                "tampering_detected": tampering_detected,
                "overall_cv_score": overall_cv_score,
            }

        except Exception as e:
            logger.error(f"Error executing Integrated CV Analysis Engine for '{cert_filename}': {str(e)}")
            raise RuntimeError(f"Integrated CV Analysis failed: {str(e)}")


# Global Singleton Service Instance
cv_analysis_service = IntegratedCVAnalysisService()
