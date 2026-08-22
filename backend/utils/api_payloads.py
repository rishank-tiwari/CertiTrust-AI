from datetime import datetime


def _iso(value):
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def build_trust_signals(verification: dict | None):
    verification = verification or {}
    fraud_flags = verification.get("fraud_flags") or []
    score = verification.get("authenticity_score", 0)
    blockchain = verification.get("blockchain_proof") or {}

    is_fraud_pass = True
    if isinstance(fraud_flags, dict):
        is_fraud_pass = (fraud_flags.get("status") == "PASS")
    elif isinstance(fraud_flags, str):
        is_fraud_pass = (fraud_flags.lower() == "pass" or not fraud_flags)
    else:
        # list or other type
        is_fraud_pass = not fraud_flags

    signals = [
        {
            "check": "OCR match",
            "result": "pass" if verification.get("extracted_data") else "fail",
        },
        {
            "check": "Issuer signature",
            "result": "pass" if score >= 80 else "fail",
        },
        {
            "check": "Fraud flags",
            "result": "pass" if is_fraud_pass else "fail",
        },
        {
            "check": "Blockchain record",
            "result": "pass" if blockchain.get("tx_hash") else "fail",
        },
    ]
    return signals


def build_verification_payload(
    certificate: dict | None,
    verification: dict | None,
    *,
    fallback_certificate_id: str | None = None,
    verified_by: str | None = None,
    status: str | None = None,
):
    certificate = certificate or {}
    verification = verification or {}
    extracted = verification.get("extracted_data") or {}
    blockchain = verification.get("blockchain_proof") or {}

    certificate_id = (
        str(certificate.get("_id") or "")
        or certificate.get("id")
        or verification.get("certificate_id")
        or fallback_certificate_id
    )
    final_status = status or verification.get("status") or certificate.get("status") or "pending"

    return {
        "certificate_id": certificate_id,
        "status": final_status,
        "identity": {
            "name": extracted.get("student_name") or certificate.get("student_name"),
            "institution": extracted.get("university") or certificate.get("university"),
            "course": extracted.get("degree") or certificate.get("degree"),
            "issue_date": extracted.get("date") or _iso(certificate.get("created_at")),
            "ocr_confidence": verification.get("authenticity_score", 0),
        },
        "trust_signals": build_trust_signals(verification),
        "blockchain_proof": {
            "tx_hash": blockchain.get("tx_hash") or verification.get("blockchain_tx_hash"),
            "block_number": blockchain.get("block_number"),
            "timestamp": blockchain.get("timestamp") or _iso(verification.get("verified_at")),
            "verified_by": verified_by,
            "network": blockchain.get("network"),
            "certificate_hash": verification.get("certificate_hash") or blockchain.get("certificate_hash"),
            "issuer": blockchain.get("issuer"),
            "status": blockchain.get("status"),
        },
    }
