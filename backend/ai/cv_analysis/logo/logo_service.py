"""
CertiTrust AI - Production Logo Verification Service Module.
Orchestrates OpenCV multi-scale Template Matching and ORB Feature Detection for certificate logo verification.
Supports both image (PNG, JPG, JPEG) and PDF certificates (rendered via PyMuPDF).
"""

from typing import Dict, Any
from ai.cv_analysis.logo.logo_utils import (
    decode_image_bytes,
    perform_template_matching,
    perform_orb_feature_matching,
    calculate_hybrid_similarity,
)
from app.utils.logger import logger


class LogoVerificationService:
    """
    Service layer handling computer vision logo detection and similarity verification against reference templates.
    """

    def verify_logo(
        self,
        certificate_bytes: bytes,
        cert_filename: str,
        reference_logo_bytes: bytes,
        ref_filename: str,
    ) -> Dict[str, Any]:
        """
        Compares certificate image/PDF against reference logo using OpenCV Template Matching & ORB.

        Returns:
            Dict[str, Any]: JSON output with success, logo_detected, similarity_score (%), confidence, and status.
        """
        logger.info(f"Starting Logo Verification: Certificate='{cert_filename}', Reference Logo='{ref_filename}'")

        try:
            # Step 1: Decode certificate (handles PDF rendering or image loading)
            cert_img = decode_image_bytes(certificate_bytes, filename=cert_filename, is_reference_logo=False)

            # Step 2: Decode reference logo with validation
            ref_img = decode_image_bytes(reference_logo_bytes, filename=ref_filename, is_reference_logo=True)

            logger.info(f"Images Loaded successfully. Cert Shape: {cert_img.shape}, Ref Logo Shape: {ref_img.shape}")

            # Step 3: Multi-Scale Template Matching
            template_score, bbox = perform_template_matching(cert_img, ref_img)
            logo_detected = template_score > 0.25
            logger.info(f"Logo Found: {logo_detected} (Template Score: {template_score:.4f}, Bounding Box: {bbox})")

            # Step 4: ORB Keypoint & Descriptor Feature Matching
            feature_score = perform_orb_feature_matching(cert_img, ref_img)
            logger.info(f"ORB Feature Matching Score: {feature_score:.4f}")

            # Step 5: Hybrid Similarity Score, Confidence, and Status Calculation
            similarity_score, confidence, status = calculate_hybrid_similarity(template_score, feature_score)
            logger.info(f"Matching Score: {similarity_score}% | Confidence: '{confidence}' | Status: '{status}'")

            return {
                "success": True,
                "logo_detected": logo_detected,
                "similarity_score": similarity_score,
                "confidence": confidence,
                "status": status,
            }

        except ValueError as ve:
            logger.warning(f"Validation Error during Logo Verification for '{cert_filename}': {str(ve)}")
            raise ve
        except Exception as e:
            logger.error(f"Error during Logo Verification for '{cert_filename}': {str(e)}")
            raise RuntimeError(f"Logo Verification failed: {str(e)}")


# Global Singleton Service Instance
logo_verification_service = LogoVerificationService()
