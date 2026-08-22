"""
CertiTrust AI - Centralized AI Trust Score Engine Service.
Combines sub-scores from OCR, Information Extraction, Metadata Analysis, Computer Vision, and Rule Validation into a weighted trust score.
Dynamically handles unavailable Computer Vision scores to prevent penalty.
"""

from typing import Dict, Any, Optional
from ai.trust_score.trust_score_config import TrustScoreConfig, trust_score_config
from app.utils.logger import logger


class TrustScoreService:
    """
    Centralized Trust Score Engine applying configurable weighted scoring algorithms.
    """

    def calculate_trust_score(
        self,
        ocr_data: Dict[str, Any],
        extraction_data: Dict[str, Any],
        metadata_data: Dict[str, Any],
        cv_data: Dict[str, Any],
        validation_data: Dict[str, Any],
        config: Optional[TrustScoreConfig] = None,
    ) -> Dict[str, Any]:
        """
        Calculates final authenticity_score, trust_score, forgery_risk, decision, and score_breakdown.
        """
        cfg = config or trust_score_config
        logger.info("Calculating Centralized AI Trust Score across 5 module outputs...")

        # 1. Compute Sub-scores (0 - 100)
        ocr_subscore = self._compute_ocr_subscore(ocr_data)
        extraction_subscore = self._compute_extraction_subscore(extraction_data)
        metadata_subscore = self._compute_metadata_subscore(metadata_data)
        
        cv_available = bool(cv_data.get("success", False) and cv_data.get("overall_cv_score") is not None)
        if cv_available:
            cv_subscore = float(cv_data["overall_cv_score"])
        else:
            cv_subscore = 0.0

        validation_subscore = self._compute_validation_subscore(validation_data)

        # 2. Compute Weighted Contributions
        if cv_available:
            ocr_contrib = round(ocr_subscore * cfg.ocr_weight)
            extraction_contrib = round(extraction_subscore * cfg.extraction_weight)
            metadata_contrib = round(metadata_subscore * cfg.metadata_weight)
            cv_contrib = round(cv_subscore * cfg.cv_weight)
            validation_contrib = round(validation_subscore * cfg.validation_weight)
            total_weighted = ocr_contrib + extraction_contrib + metadata_contrib + cv_contrib + validation_contrib
        else:
            # Dynamic Weight Redistribution when CV is unavailable
            remaining_sum = cfg.ocr_weight + cfg.extraction_weight + cfg.metadata_weight + cfg.validation_weight
            scale = 1.0 / remaining_sum if remaining_sum > 0 else 1.0
            
            ocr_contrib = round(ocr_subscore * (cfg.ocr_weight * scale))
            extraction_contrib = round(extraction_subscore * (cfg.extraction_weight * scale))
            metadata_contrib = round(metadata_subscore * (cfg.metadata_weight * scale))
            cv_contrib = 0
            validation_contrib = round(validation_subscore * (cfg.validation_weight * scale))
            total_weighted = ocr_contrib + extraction_contrib + metadata_contrib + validation_contrib

        score_breakdown = {
            "ocr": int(ocr_contrib),
            "information_extraction": int(extraction_contrib),
            "metadata": int(metadata_contrib),
            "computer_vision": int(cv_contrib) if cv_available else None,
            "validation": int(validation_contrib),
        }

        # 3. Calculate Composite Scores (0 - 100)
        authenticity_score = int(round(min(100, max(0, total_weighted))))
        trust_score = authenticity_score

        # 4. Map Decision & Forgery Risk
        decision, forgery_risk = self._classify_decision_and_risk(trust_score, cfg)

        logger.info(
            f"Trust Score Engine Complete. Trust Score: {trust_score}, Authenticity Score: {authenticity_score}, "
            f"Forgery Risk: '{forgery_risk}', Decision: '{decision}'"
        )

        return {
            "success": True,
            "authenticity_score": authenticity_score,
            "trust_score": trust_score,
            "forgery_risk": forgery_risk,
            "decision": decision,
            "score_breakdown": score_breakdown,
        }

    def _compute_ocr_subscore(self, ocr_data: Dict[str, Any]) -> float:
        text_len = 0
        if isinstance(ocr_data, dict):
            pages = ocr_data.get("pages", [])
            if isinstance(pages, list):
                text_len = sum([len(str(p.get("text", ""))) for p in pages if isinstance(p, dict)])

        if text_len > 80:
            return 100.0
        elif text_len > 30:
            return 80.0
        elif text_len > 5:
            return 50.0
        return 0.0

    def _compute_extraction_subscore(self, extraction_data: Dict[str, Any]) -> float:
        doc_type = extraction_data.get("document_type", "")
        doc_type_clean = doc_type.lower()

        if "b.tech" in doc_type_clean or "btech" in doc_type_clean:
            critical_fields = ["student_name", "university", "roll_number", "sgpa", "cgpa"]
            extracted_count = sum(1 for field in critical_fields if extraction_data.get(field) is not None)
            ratio = extracted_count / float(len(critical_fields))
        elif "marksheet" in doc_type_clean or "board" in doc_type_clean or "transcript" in doc_type_clean:
            critical_fields = ["student_name", "board", "roll_number", "percentage"]
            extracted_count = sum(1 for field in critical_fields if extraction_data.get(field) is not None)
            ratio = extracted_count / float(len(critical_fields))
        elif "resume" in doc_type_clean or "cv" in doc_type_clean:
            critical_fields = ["student_name", "skills"]
            extracted_count = 0
            if extraction_data.get("student_name"):
                extracted_count += 1
            if extraction_data.get("skills"):
                extracted_count += 1
            ratio = extracted_count / float(len(critical_fields))
        else:
            critical_fields = ["student_name", "university", "degree", "certificate_number", "issue_date"]
            extracted_count = sum(1 for field in critical_fields if extraction_data.get(field))
            ratio = extracted_count / float(len(critical_fields))

        return round(ratio * 100.0, 1)

    def _compute_metadata_subscore(self, metadata_data: Dict[str, Any]) -> float:
        risk_level = str(metadata_data.get("risk_level", "Low")).lower()
        warnings_count = len(metadata_data.get("warnings", []))

        if risk_level == "low":
            base = 100.0
        elif risk_level == "medium":
            base = 75.0
        elif risk_level == "high":
            base = 30.0
        else:
            base = 0.0

        penalty = warnings_count * 5.0
        return max(0.0, round(base - penalty, 1))

    def _compute_cv_subscore(self, cv_data: Dict[str, Any]) -> float:
        if not cv_data.get("success", False):
            return 0.0
        score = cv_data.get("overall_cv_score")
        if score is None:
            return 0.0
        return float(score)

    def _compute_validation_subscore(self, validation_data: Dict[str, Any]) -> float:
        score = validation_data.get("validation_score")
        if score is not None:
            return float(score)

        passed = validation_data.get("passed_rules", 10)
        failed = validation_data.get("failed_rules", 0)
        total = passed + failed
        return round((passed / total) * 100.0, 1) if total > 0 else 100.0

    def _classify_decision_and_risk(self, trust_score: int, cfg: TrustScoreConfig) -> tuple[str, str]:
        if trust_score >= cfg.verified_threshold:  # >= 90
            decision = "Verified"
            forgery_risk = "Very Low" if trust_score >= 95 else "Low"
        elif trust_score >= cfg.review_threshold:  # 75 - 89
            decision = "Needs Manual Review"
            forgery_risk = "Low" if trust_score >= 82 else "Medium"
        elif trust_score >= cfg.suspicious_threshold:  # 50 - 74
            decision = "Suspicious"
            forgery_risk = "Medium" if trust_score >= 62 else "High"
        else:
            decision = "Likely Forged"
            forgery_risk = "Critical"

        return decision, forgery_risk


# Global Singleton Service Instance
trust_score_service = TrustScoreService()
