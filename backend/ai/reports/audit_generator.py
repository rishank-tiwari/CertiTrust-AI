"""
CertiTrust AI - Audit Trail & Report Generator.
Generates audit summary JSON reports and verification credentials.
"""

from typing import Dict, Any
from datetime import datetime
from app.utils.logger import logger


class AuditReportGenerator:
    """
    Generates structured audit trail reports for verified certificates.
    """

    def generate_report(
        self,
        document_id: str,
        filename: str,
        document_hash: str,
        entities: Dict[str, Any],
        scoring_result: Dict[str, Any],
        fraud_result: Dict[str, Any],
        metadata_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Builds audit log package ready for export or frontend viewing.
        """
        logger.info(f"Generating full audit report for document ID: {document_id}")

        report = {
            "audit_id": f"AUDIT-{document_id[:8].upper()}",
            "document_id": document_id,
            "filename": filename,
            "document_sha256_hash": document_hash,
            "verification_timestamp": datetime.utcnow().isoformat(),
            "verdict": {
                "is_authentic": scoring_result["is_authentic"],
                "trust_score": scoring_result["trust_score"],
                "risk_level": scoring_result["risk_level"],
            },
            "extracted_certificate_details": entities,
            "fraud_analysis": {
                "tamper_probability": fraud_result["tamper_probability"],
                "fraud_flags": fraud_result["fraud_flags"],
            },
            "technical_breakdown": scoring_result["score_breakdown"],
            "blockchain_ready_payload": {
                "doc_hash": document_hash,
                "cert_id": str(entities.get("certificate_id") or ""),
                "issuer": str(entities.get("issuer_name") or ""),
                "recipient": str(entities.get("recipient_name") or ""),
                "trust_score_scaled": int(scoring_result["trust_score"] * 100),
                "timestamp": int(datetime.utcnow().timestamp()),
                "is_valid": bool(scoring_result["is_authentic"]),
            },
        }

        return report
