"""
CertiTrust AI - Trust Score Engine Configuration.
Defines weight ratios and decision thresholds for document authenticity classification.
"""

from pydantic import BaseModel


class TrustScoreConfig(BaseModel):
    """
    Configurable weight parameters for the AI Trust Score Engine.
    Total weights sum up to 1.0 (100%).
    """

    ocr_weight: float = 0.15            # 15% OCR text completeness
    extraction_weight: float = 0.20     # 20% Structured Field Extraction completeness
    metadata_weight: float = 0.15       # 15% File & EXIF metadata integrity
    cv_weight: float = 0.35             # 35% Computer Vision overall score
    validation_weight: float = 0.15     # 15% Authenticity Rule Validation score

    # Decision Thresholds
    verified_threshold: int = 90        # Trust Score >= 90 -> Verified
    review_threshold: int = 75          # Trust Score 75-89 -> Needs Manual Review
    suspicious_threshold: int = 50      # Trust Score 50-74 -> Suspicious
                                        # Trust Score < 50  -> Likely Forged


# Global default configuration instance
trust_score_config = TrustScoreConfig()
