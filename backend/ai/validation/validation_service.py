"""
CertiTrust AI - Production Rule Validation Engine Service Module.
Aggregates and evaluates rules across OCR, Information Extraction, Metadata, and Computer Vision modules.
"""

from typing import Dict, Any, List
from ai.validation.validation_rules import (
    get_credential_validation_rules,
    DEFAULT_LOGO_THRESHOLD,
    DEFAULT_SIGNATURE_THRESHOLD,
    DEFAULT_LAYOUT_THRESHOLD,
)
from app.utils.logger import logger


class RuleValidationService:
    """
    Rule Validation Engine executing authenticity verification rules against combined AI module outputs.
    Credential-type aware and dynamically scales validations.
    """

    def validate_credential(
        self,
        ocr_data: Dict[str, Any],
        extraction_data: Dict[str, Any],
        metadata_data: Dict[str, Any],
        cv_data: Dict[str, Any],
        logo_threshold: int = DEFAULT_LOGO_THRESHOLD,
        signature_threshold: int = DEFAULT_SIGNATURE_THRESHOLD,
        layout_threshold: int = DEFAULT_LAYOUT_THRESHOLD,
    ) -> Dict[str, Any]:
        """
        Runs authenticity rules and calculates passed_rules, failed_rules, and validation_score.
        """
        logger.info("Starting Rule Validation Engine on combined AI module outputs...")

        # Load credential-specific rule set dynamically
        rules = get_credential_validation_rules(
            ocr_data=ocr_data,
            extraction_data=extraction_data,
            metadata_data=metadata_data,
            cv_data=cv_data,
            logo_threshold=logo_threshold,
            signature_threshold=signature_threshold,
            layout_threshold=layout_threshold,
        )

        validation_results: List[Dict[str, Any]] = []
        passed_count = 0
        failed_count = 0

        for r in rules:
            res_dict = r.to_dict()
            validation_results.append(res_dict)
            if r.passed:
                passed_count += 1
                logger.info(f"Rule PASSED: '{r.rule}' - {r.reason}")
            else:
                failed_count += 1
                logger.warning(f"Rule FAILED: '{r.rule}' - {r.reason}")

        total_rules = len(rules)
        validation_score = int(round((passed_count / total_rules) * 100)) if total_rules > 0 else 0

        logger.info(
            f"Rule Validation Complete. Total Rules: {total_rules}, "
            f"Passed: {passed_count}, Failed: {failed_count}, Validation Score: {validation_score}%"
        )

        return {
            "success": True,
            "validation_results": validation_results,
            "passed_rules": passed_count,
            "failed_rules": failed_count,
            "validation_score": validation_score,
        }


# Global Singleton Service Instance
rule_validation_service = RuleValidationService()
