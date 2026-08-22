"""
CertiTrust AI - Multi-Factor Authenticity & Trust Scoring Engine.
Computes composite trust score (0-100) and categorizes risk levels.
"""

from typing import Dict, Any
from app.utils.logger import logger


class TrustScoringEngine:
    """
    Weighted scoring algorithm combining OCR confidence, CV features, metadata integrity, and fraud signals.
    """

    WEIGHTS = {
        "metadata_integrity": 0.25,
        "ocr_confidence": 0.25,
        "visual_authenticity": 0.25,
        "tamper_safety": 0.25,
    }

    def compute_trust_score(
        self,
        ocr_result: Dict[str, Any],
        cv_result: Dict[str, Any],
        metadata_result: Dict[str, Any],
        fraud_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Calculates final composite trust score and risk assessment.
        """
        logger.info("Computing composite trust score...")

        ocr_score = float(ocr_result.get("confidence", 80.0))
        cv_score = float(cv_result.get("visual_authenticity_score", 85.0))
        meta_score = float(metadata_result.get("metadata_integrity_score", 90.0))
        tamper_safety = max(0.0, 100.0 - float(fraud_result.get("tamper_probability", 0.0)))

        composite_score = (
            (ocr_score * self.WEIGHTS["ocr_confidence"])
            + (cv_score * self.WEIGHTS["visual_authenticity"])
            + (meta_score * self.WEIGHTS["metadata_integrity"])
            + (tamper_safety * self.WEIGHTS["tamper_safety"])
        )

        # Normalize score
        final_score = round(max(0.0, min(100.0, composite_score)), 2)

        # Classify risk level
        if final_score >= 85.0:
            risk_level = "LOW"
            is_authentic = True
        elif final_score >= 65.0:
            risk_level = "MEDIUM"
            is_authentic = True
        elif final_score >= 45.0:
            risk_level = "HIGH"
            is_authentic = False
        else:
            risk_level = "CRITICAL"
            is_authentic = False

        result = {
            "trust_score": final_score,
            "is_authentic": is_authentic,
            "risk_level": risk_level,
            "score_breakdown": {
                "ocr_confidence_score": ocr_score,
                "visual_authenticity_score": cv_score,
                "metadata_integrity_score": meta_score,
                "tamper_safety_score": tamper_safety,
            },
        }

        logger.info(f"Composite Trust Score computed: {final_score}/100 (Risk: {risk_level})")
        return result
