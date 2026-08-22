"""
CertiTrust AI - Employer Portal Endpoint Router.
Provides POST /api/v1/employer/verify endpoint to verify submitted credentials against issuer registry.
Implements granular change detection, comparison states, and risk engine algorithms.
"""

import hashlib
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from ai.pipeline.analysis_service import pipeline_analysis_service
from app.services.registry_service import credential_registry
from app.config import settings
from app.utils.logger import logger

router = APIRouter(prefix="/employer", tags=["Employer Portal Management"])

ALLOWED_DOC_EXTENSIONS = {"png", "jpg", "jpeg", "pdf"}


def compare_values(val1: Any, val2: Any) -> bool:
    """
    Compares two values, handling string normalization and float conversions safely.
    """
    if val1 is None or val2 is None:
        return val1 == val2

    # Try numeric float comparison
    try:
        return abs(float(val1) - float(val2)) < 0.01
    except (ValueError, TypeError):
        pass

    # Normalize and compare string representations
    return str(val1).strip().upper() == str(val2).strip().upper()


def is_valid_val(val: Any) -> bool:
    """
    Returns True if the value is extracted and is NOT a missing/placeholder value.
    """
    if val is None:
        return False
    val_str = str(val).strip().lower()
    if val_str in ["", "not found", "unknown", "n/a", "none", "null", "empty string", "placeholder"]:
        return False
    return True


@router.post(
    "/verify",
    status_code=status.HTTP_200_OK,
    summary="Verify Candidate Credential Against Issuer Record",
    description="Employer uploads a candidate's credential and compares it field-by-field against the registered source of truth.",
)
async def verify_employer_credential(
    certificate: UploadFile = File(..., description="Uploaded Candidate Certificate/Marksheet File (PDF/PNG/JPG/JPEG)"),
    credential_id: Optional[str] = Form(None, description="Optional Registered Credential ID")
):
    """
    Ingests candidate credential, hashes it, runs analysis, matches against issuer registry,
    and performs a detailed field comparison and risk engine evaluation.
    """
    logger.info(f"Employer verification request received for file: '{certificate.filename}'")

    # Clean/normalize credential_id from form placeholders
    if credential_id:
        c_id_clean = credential_id.strip()
        if c_id_clean.lower() in ["string", "null", "none", "undefined", "", "unknown", "n/a", "na"]:
            credential_id = None
        else:
            credential_id = c_id_clean

    if not certificate.filename or "." not in certificate.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded certificate must have a valid filename with an extension.",
        )

    cert_ext = certificate.filename.lower().split(".")[-1]
    if cert_ext not in ALLOWED_DOC_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '.{cert_ext}'. Allowed formats: {', '.join(ALLOWED_DOC_EXTENSIONS)}",
        )

    cert_bytes = await certificate.read()
    if len(cert_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty (0 bytes).",
        )

    # 1. Run full pipeline to extract details
    try:
        pipeline_res = pipeline_analysis_service.run_full_pipeline(
            cert_bytes=cert_bytes,
            cert_filename=certificate.filename,
            ref_template_bytes=None,
            ref_template_filename=None,
            ref_logo_bytes=None,
            ref_logo_filename=None,
        )
    except Exception as e:
        logger.error(f"Error during AI pipeline extraction for employer verification: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI pipeline analysis failed during employer processing: {str(e)}",
        )

    # Gating check: Must be supported
    if not pipeline_res.get("is_supported", False):
        return {
            "success": False,
            "verification_status": "REJECTED",
            "is_supported": False,
            "verification_stopped": True,
            "document_type": "Not an Educational Credential",
            "message": "Uploaded file is not a supported educational credential."
        }

    # 2. Hash submitted document
    submitted_hash = hashlib.sha256(cert_bytes).hexdigest()

    # 3. Locate Registered Trusted Record
    registered_record = None
    if credential_id:
        registered_record = credential_registry.get_by_id(credential_id.strip())

    if not registered_record:
        # Search by file hash
        registered_record = credential_registry.get_by_hash(submitted_hash)

    # Multi-field fallback matching
    ext_data = pipeline_res.get("information_extraction") or {}
    roll = ext_data.get("roll_number")
    reg = ext_data.get("registration_number")
    name = ext_data.get("student_name")
    sem = ext_data.get("semester")
    doc_type = pipeline_res.get("document_type", "Academic Certificate")
    university_extracted = ext_data.get("university") or ext_data.get("board") or ext_data.get("organization")
    if university_extracted == "Not Found":
        university_extracted = None

    if not registered_record:
        candidate_matches = []
        for record in credential_registry._db.values():
            rec_recipient = record.get("recipient", {})
            rec_data = record.get("credential_data", {})
            
            match_signals = 0
            total_signals = 0
            
            # 1. Registration check
            reg_reg = rec_data.get("registration_number") or record.get("recipient", {}).get("registration_number")
            if reg and reg_reg:
                total_signals += 1
                if compare_values(reg, reg_reg):
                    match_signals += 1
            
            # 2. Roll check
            reg_roll = rec_recipient.get("student_identifier") or rec_data.get("roll_number") or record.get("recipient", {}).get("roll_number")
            if roll and reg_roll:
                total_signals += 1
                if compare_values(roll, reg_roll):
                    match_signals += 1

            # 3. Student Name check
            reg_name = rec_recipient.get("student_name")
            if name and reg_name:
                total_signals += 1
                if compare_values(name, reg_name):
                    match_signals += 1

            # 4. Semester check
            reg_sem = rec_data.get("semester")
            if sem and reg_sem:
                total_signals += 1
                if compare_values(sem, reg_sem):
                    match_signals += 1

            # 5. Credential type check
            reg_type = record.get("credential_type")
            if doc_type and reg_type:
                total_signals += 1
                if compare_values(doc_type, reg_type):
                    match_signals += 1

            is_match = False
            if reg and reg_reg and compare_values(reg, reg_reg) and roll and reg_roll and compare_values(roll, reg_roll):
                is_match = True
            elif match_signals >= 3:
                is_match = True
                
            if is_match:
                candidate_matches.append(record)

        if len(candidate_matches) == 1:
            registered_record = candidate_matches[0]
            logger.info(f"Successfully matched candidate registry record via multi-field lookup: {registered_record['credential_id']}")
        elif len(candidate_matches) > 1:
            logger.warning(f"Multiple records matched: {[r['credential_id'] for r in candidate_matches]}")
            return {
                "success": True,
                "verification_status": "AMBIGUOUS_MATCH",
                "risk_level": "HIGH",
                "issuer_record_found": True,
                "message": "Multiple registered credentials matched the candidate details. Please provide a unique Credential ID.",
                "candidate_matches": [r["credential_id"] for r in candidate_matches]
            }

    # Define fields schema for fallback unverified parameters mapping
    doc_type_clean = doc_type.lower()
    is_btech = "b.tech" in doc_type_clean or "btech" in doc_type_clean
    is_marksheet = "marksheet" in doc_type_clean or "board" in doc_type_clean or "transcript" in doc_type_clean

    fields_schema = []
    if is_btech:
        fields_schema = [
            ("student_name", "Student Name", "student_name", "CRITICAL"),
            ("university", "University Name", "university", "CRITICAL"),
            ("degree", "Degree", "degree", "HIGH"),
            ("program", "Program / Stream", "program", "HIGH"),
            ("semester", "Semester", "semester", "HIGH"),
            ("sgpa", "SGPA Score", "sgpa", "CRITICAL"),
            ("cgpa", "CGPA Score", "cgpa", "CRITICAL"),
            ("percentage", "Percentage Score", "percentage", "CRITICAL"),
            ("result", "Result Status", "result", "CRITICAL"),
            ("division", "Division", "division", "MEDIUM"),
        ]
    elif is_marksheet:
        fields_schema = [
            ("student_name", "Student Name", "student_name", "CRITICAL"),
            ("board", "Board Name", "board", "CRITICAL"),
            ("exam", "Exam Title", "exam", "CRITICAL"),
            ("exam_year", "Exam Year", "exam_year", "HIGH"),
            ("roll_number", "Roll Number", "roll_number", "CRITICAL"),
            ("total_max_marks", "Maximum Marks", "total_max_marks", "HIGH"),
            ("total_marks_obtained", "Obtained Marks", "total_marks_obtained", "CRITICAL"),
            ("percentage", "Percentage Score", "percentage", "CRITICAL"),
            ("result", "Result Status", "result", "CRITICAL"),
        ]
    else:
        fields_schema = [
            ("student_name", "Student Name", "student_name", "CRITICAL"),
            ("university", "University Name", "university", "CRITICAL"),
            ("degree", "Degree", "degree", "HIGH"),
            ("course", "Course / Major", "course", "HIGH"),
            ("certificate_number", "Certificate Number", "certificate_number", "CRITICAL"),
            ("cgpa", "CGPA Score", "cgpa", "CRITICAL"),
        ]

    # 4. Initialize Comparison parameters
    changed_parameters = []
    total_parameters_checked = 0
    matched_parameters = 0
    changed_parameters_count = 0
    missing_parameters_count = 0
    unverified_parameters_count = 0

    cv_tamper = pipeline_res.get("computer_vision", {}).get("tampering_detected", False) if pipeline_res.get("computer_vision") else False

    # CASE A: UNREGISTERED / NOT_VERIFIED (No issuer record exists)
    if not registered_record:
        unverified_parameters = []
        for field_key, display_name, reg_key, severity in fields_schema:
            total_parameters_checked += 1
            unverified_parameters_count += 1
            unverified_parameters.append({
                "field": field_key,
                "display_name": display_name,
                "original_value": None,
                "submitted_value": ext_data.get(field_key),
                "status": "NOT_VERIFIED",
                "severity": severity,
                "message": f"{display_name} could not be verified because no registered reference was found."
            })

        indicators = ["❌"] * total_parameters_checked
        report_lines = [
            "Parameter Verification",
            "",
            f"{total_parameters_checked} Parameters Checked",
            ""
        ]
        for ind in indicators:
            report_lines.append(ind)
        report_lines.append("")
        report_lines.append(f"{matched_parameters} ✅ MATCHED")
        report_lines.append(f"{total_parameters_checked - matched_parameters} ❌ NOT MATCHED")
        parameter_verification_report = "\n".join(report_lines)

        return {
            "success": True,
            "verification_status": "UNREGISTERED",
            "risk_level": "HIGH",
            "issuer_record_found": False,
            "issuer": university_extracted or "Unknown Issuer",
            "credential_type": doc_type,
            "credential_match": False,
            "hash_match": False,
            "total_parameters_checked": total_parameters_checked,
            "matched_parameters": matched_parameters,
            "changed_parameters_count": changed_parameters_count,
            "missing_parameters_count": missing_parameters_count,
            "unverified_parameters_count": unverified_parameters_count,
            "changed_parameters": [],
            "unverified_parameters": unverified_parameters,
            "parameter_indicators": indicators,
            "parameter_verification_report": parameter_verification_report,
            "message": "No matching credential was found in the CertiTrust issuer registry.",
            "recommendation": "Perform manual verification steps with the issuing institution."
        }

    # CASE B: REGISTERED (Issuer Record Found)
    registered_data = registered_record.get("credential_data", {})
    registered_subs = registered_data.get("subjects", [])
    submitted_subs = ext_data.get("subjects", [])

    # Map the 30 verification schema parameters dynamically
    hash_match = (submitted_hash == registered_record["document"]["sha256"])
    sub_cred_id_clean = credential_id
    if hash_match and not sub_cred_id_clean:
        sub_cred_id_clean = registered_record["credential_id"]

    properties = []
    properties.append(("issuer", "Issuer Name", registered_record["issuer"]["name"], university_extracted, "CRITICAL"))
    properties.append(("issuer_auth", "Issuer Authorization", registered_record["issuer"]["issuer_status"], "AUTHORIZED" if university_extracted else "UNAUTHORIZED", "CRITICAL"))
    properties.append(("credential_id", "Credential ID", registered_record["credential_id"], sub_cred_id_clean, "CRITICAL"))
    properties.append(("status", "Credential Status", registered_record["status"], "ACTIVE", "CRITICAL"))
    properties.append(("student_name", "Student Name", registered_record["recipient"]["student_name"], ext_data.get("student_name"), "CRITICAL"))
    properties.append(("roll_number", "Roll Number", registered_record["recipient"]["student_identifier"], ext_data.get("roll_number") or ext_data.get("student_identifier"), "CRITICAL"))
    properties.append(("credential_type", "Credential Type", registered_record["credential_type"], doc_type, "CRITICAL"))

    if is_btech:
        properties.append(("registration_number", "Registration Number", registered_data.get("registration_number"), ext_data.get("registration_number"), "CRITICAL"))
        properties.append(("degree", "Degree", registered_data.get("degree"), ext_data.get("degree"), "HIGH"))
        properties.append(("program", "Program / Stream", registered_data.get("program"), ext_data.get("program"), "HIGH"))
        properties.append(("college", "College", registered_data.get("college_name") or registered_data.get("college"), ext_data.get("college_name") or ext_data.get("college"), "MEDIUM"))
        properties.append(("semester", "Semester", registered_data.get("semester"), ext_data.get("semester"), "HIGH"))
        properties.append(("academic_year", "Academic Year", registered_data.get("academic_year"), ext_data.get("academic_year"), "MEDIUM"))
        properties.append(("exam_session", "Exam Session", registered_data.get("exam_session"), ext_data.get("exam_session"), "MEDIUM"))
        properties.append(("sgpa", "SGPA Score", registered_data.get("sgpa"), ext_data.get("sgpa"), "CRITICAL"))
        properties.append(("cgpa", "CGPA Score", registered_data.get("cgpa"), ext_data.get("cgpa"), "CRITICAL"))
        properties.append(("percentage", "Percentage Score", registered_data.get("percentage"), ext_data.get("percentage"), "CRITICAL"))
        properties.append(("result", "Result Status", registered_data.get("result"), ext_data.get("result"), "CRITICAL"))
        properties.append(("division", "Division", registered_data.get("division"), ext_data.get("division"), "MEDIUM"))
        
    elif is_marksheet:
        properties.append(("board", "Board Name", registered_data.get("board"), ext_data.get("board"), "CRITICAL"))
        properties.append(("exam", "Exam Title", registered_data.get("exam"), ext_data.get("exam"), "CRITICAL"))
        properties.append(("exam_year", "Exam Year", registered_data.get("exam_year"), ext_data.get("exam_year"), "HIGH"))
        properties.append(("total_max_marks", "Maximum Marks", registered_data.get("total_max_marks"), ext_data.get("total_max_marks"), "HIGH"))
        properties.append(("total_marks_obtained", "Obtained Marks", registered_data.get("total_marks_obtained"), ext_data.get("total_marks_obtained"), "CRITICAL"))
        properties.append(("percentage", "Percentage Score", registered_data.get("percentage"), ext_data.get("percentage"), "CRITICAL"))
        properties.append(("result", "Result Status", registered_data.get("result"), ext_data.get("result"), "CRITICAL"))
        
    else:
        properties.append(("degree", "Degree", registered_data.get("degree"), ext_data.get("degree"), "HIGH"))
        properties.append(("course", "Course / Major", registered_data.get("course"), ext_data.get("course"), "HIGH"))
        properties.append(("certificate_number", "Certificate Number", registered_data.get("certificate_number"), ext_data.get("certificate_number"), "CRITICAL"))
        properties.append(("cgpa", "CGPA Score", registered_data.get("cgpa"), ext_data.get("cgpa"), "CRITICAL"))

    # Common document properties
    properties.append(("issued_date", "Issue Date", registered_record["document"]["issued_date"], ext_data.get("dated") or ext_data.get("document_date") or ext_data.get("issue_date"), "MEDIUM"))
    properties.append(("digilocker_generated", "QR / Barcode Presence", registered_record["credential_data"].get("digilocker_generated") if is_btech else False, ext_data.get("digilocker_generated") if is_btech else False, "MEDIUM"))
    
    reg_sig_success = registered_record["credential_data"].get("digital_signature", {}).get("success") if is_btech else False
    properties.append(("digital_signature", "Digital Signature Status", reg_sig_success, ext_data.get("digital_signature", {}).get("success") if is_btech else False, "HIGH"))


    # Loop through properties and check matches/changes
    for field_key, display_name, registered_val, submitted_val, severity in properties:
        total_parameters_checked += 1

        sub_exists = is_valid_val(submitted_val)
        reg_exists = is_valid_val(registered_val)

        if not reg_exists:
            matched_parameters += 1
            continue

        if not sub_exists:
            if field_key == "credential_id":
                changed_parameters.append({
                    "field": "credential_id",
                    "display_name": "Credential ID",
                    "original_value": registered_val,
                    "submitted_value": None,
                    "status": "NOT_VERIFIED",
                    "severity": "MEDIUM",
                    "message": "Credential ID not verified."
                })
                continue

            missing_parameters_count += 1
            changed_parameters.append({
                "field": field_key,
                "display_name": display_name,
                "original_value": registered_val,
                "submitted_value": None,
                "status": "MISSING",
                "severity": severity,
                "message": f"Expected {display_name} is missing from the submitted document."
            })
            continue

        if compare_values(submitted_val, registered_val):
            matched_parameters += 1
        else:
            changed_parameters_count += 1
            difference = None
            try:
                difference = round(float(submitted_val) - float(registered_val), 2)
            except (ValueError, TypeError):
                difference = f"{registered_val} → {submitted_val}"

            changed_parameters.append({
                "field": field_key,
                "display_name": display_name,
                "original_value": registered_val,
                "submitted_value": submitted_val,
                "difference": difference,
                "status": "CHANGED",
                "severity": severity,
                "message": f"{display_name} changed from {registered_val} to {submitted_val}"
            })

    # Compare subject lists
    if is_btech or is_marksheet:
        for i, reg_sub in enumerate(registered_subs):
            total_parameters_checked += 1
            sub_name = reg_sub.get("subject") or reg_sub.get("name")
            sub_code = reg_sub.get("course_code")

            # Match candidate subject entry
            matched_sub = None
            for s in submitted_subs:
                s_name = s.get("subject") or s.get("name")
                s_code = s.get("course_code")
                if sub_code and s_code and compare_values(sub_code, s_code):
                    matched_sub = s
                    break
                if s_name and compare_values(sub_name, s_name):
                    matched_sub = s
                    break

            if not matched_sub:
                missing_parameters_count += 1
                changed_parameters.append({
                    "field": f"subjects[{sub_name}]",
                    "display_name": f"Subject ({sub_name})",
                    "original_value": sub_name,
                    "submitted_value": None,
                    "status": "MISSING",
                    "severity": "HIGH",
                    "message": f"Subject '{sub_name}' is missing from the submitted document."
                })
                continue

            # Subject matched successfully
            matched_parameters += 1

            # Compare individual grades/marks/credits inside matched subject row
            fields_sub = []
            if is_btech:
                fields_sub = ["grade", "grade_points", "credits", "credit_points"]
            else:
                fields_sub = ["marks_obtained"]

            for f_name in fields_sub:
                reg_val = reg_sub.get(f_name)
                sub_val = matched_sub.get(f_name)

                total_parameters_checked += 1
                sub_exists = is_valid_val(sub_val)
                reg_exists = is_valid_val(reg_val)

                if not reg_exists:
                    matched_parameters += 1
                    continue

                if not sub_exists:
                    missing_parameters_count += 1
                    changed_parameters.append({
                        "field": f"subjects[{sub_name}].{f_name}",
                        "display_name": f"{f_name.replace('_', ' ').capitalize()} ({sub_name})",
                        "original_value": reg_val,
                        "submitted_value": None,
                        "status": "MISSING",
                        "severity": "HIGH",
                        "message": f"Subject field {f_name} is missing from '{sub_name}'."
                    })
                    continue

                if compare_values(sub_val, reg_val):
                    matched_parameters += 1
                else:
                    changed_parameters_count += 1
                    difference = None
                    try:
                        difference = round(float(sub_val) - float(reg_val), 2)
                    except (ValueError, TypeError):
                        difference = f"{reg_val} → {sub_val}"

                    changed_parameters.append({
                        "field": f"subjects[{sub_name}].{f_name}",
                        "display_name": f"{f_name.replace('_', ' ').capitalize()} ({sub_name})",
                        "original_value": reg_val,
                        "submitted_value": sub_val,
                        "difference": difference,
                        "status": "CHANGED",
                        "severity": "HIGH",
                        "message": f"Subject '{sub_name}' {f_name} changed from {reg_val} to {sub_val}"
                    })

    # Calculate Comparison Scores
    hash_match = submitted_hash == registered_record["document"]["sha256"]
    field_match_percentage = round((matched_parameters / total_parameters_checked) * 100.0, 1) if total_parameters_checked > 0 else 100.0

    # Risk Engine Determination
    has_critical_change = any(c["status"] == "CHANGED" and c["severity"] == "CRITICAL" for c in changed_parameters)
    has_high_change = any(c["status"] == "CHANGED" and c["severity"] == "HIGH" for c in changed_parameters)
    has_medium_change = any(c["status"] == "CHANGED" and c["severity"] == "MEDIUM" for c in changed_parameters)

    if cv_tamper:
        risk_level = "CRITICAL"
        verification_status = "TAMPERED"
    elif has_critical_change or has_high_change:
        risk_level = "HIGH"
        verification_status = "MISMATCH"
    elif has_medium_change or missing_parameters_count > 0:
        risk_level = "MEDIUM"
        verification_status = "DISCREPANCY"
    else:
        risk_level = "LOW"
        verification_status = "VERIFIED"

    # Set Recommendation & explanation of Risk
    if verification_status == "VERIFIED":
        if hash_match:
            recommendation = "Credential matches registered issuer record and is authentic."
        else:
            recommendation = "Content matches issuer record, but file hash differs. Legitimate re-download/re-render."
    elif verification_status == "TAMPERED" or risk_level == "CRITICAL":
        recommendation = "CRITICAL: Suspicious visual edits or digital manipulation detected. Reject credential."
    else:
        # Explain why this is high risk
        summary_mismatches = [f"{c['display_name']} (Issuer: {c['original_value']}, Submitted: {c['submitted_value']})" for c in changed_parameters if c["status"] == "CHANGED"]
        recommendation = f"Do not rely on this credential. Discrepancies detected: {', '.join(summary_mismatches)}."

    indicators = []
    # Loop over properties in the exact order checked
    for field_key, display_name, registered_val, submitted_val, severity in properties:
        reg_exists = is_valid_val(registered_val)
        if not reg_exists:
            indicators.append((display_name, "✅"))
            continue
        
        # Check if this field exists in changed_parameters
        is_changed = any(c["field"] == field_key for c in changed_parameters)
        if is_changed:
            indicators.append((display_name, "❌"))
        else:
            indicators.append((display_name, "✅"))

    # Loop over subjects in the exact order checked
    if is_btech or is_marksheet:
        for i, reg_sub in enumerate(registered_subs):
            sub_name = reg_sub.get("subject") or reg_sub.get("name")
            
            # Check if whole subject is missing
            is_sub_missing = any(c["field"] == f"subjects[{sub_name}]" for c in changed_parameters)
            if is_sub_missing:
                indicators.append((f"Subject ({sub_name})", "❌"))
                continue
                
            indicators.append((f"Subject ({sub_name})", "✅"))
            
            fields_sub = []
            if is_btech:
                fields_sub = ["grade", "grade_points", "credits", "credit_points"]
            else:
                fields_sub = ["marks_obtained"]

            for f_name in fields_sub:
                reg_val = reg_sub.get(f_name)
                reg_exists = is_valid_val(reg_val)
                if not reg_exists:
                    indicators.append((f"{f_name.replace('_', ' ').capitalize()} ({sub_name})", "✅"))
                    continue
                
                # Check if this specific field is in changed_parameters
                is_field_changed = any(c["field"] == f"subjects[{sub_name}].{f_name}" for c in changed_parameters)
                if is_field_changed:
                    indicators.append((f"{f_name.replace('_', ' ').capitalize()} ({sub_name})", "❌"))
                else:
                    indicators.append((f"{f_name.replace('_', ' ').capitalize()} ({sub_name})", "✅"))

    # Build the report string
    report_lines = [
        "Parameter Verification",
        "",
        f"{total_parameters_checked} Parameters Checked",
        ""
    ]
    for display_name, ind in indicators:
        report_lines.append(f"{display_name:<30} {ind}")
    report_lines.append("")
    report_lines.append(f"{matched_parameters} ✅ MATCHED")
    report_lines.append(f"{total_parameters_checked - matched_parameters} ❌ NOT MATCHED")
    parameter_verification_report = "\n".join(report_lines)

    flat_indicators = [ind for name, ind in indicators]

    return {
        "success": True,
        "verification_status": verification_status,
        "risk_level": risk_level,
        "issuer_record_found": True,
        "issuer": registered_record["issuer"]["name"],
        "credential_type": doc_type,
        "credential_match": (verification_status == "VERIFIED"),
        "hash_match": hash_match,
        "field_match_percentage": field_match_percentage,
        "file_identity": {
            "hash_match": hash_match
        },
        "credential_identity": {
            "match": (verification_status == "VERIFIED")
        },
        "total_parameters_checked": total_parameters_checked,
        "matched_parameters": matched_parameters,
        "changed_parameters_count": changed_parameters_count,
        "missing_parameters_count": missing_parameters_count,
        "unverified_parameters_count": unverified_parameters_count,
        "changed_parameters": changed_parameters,
        "parameter_indicators": flat_indicators,
        "parameter_verification_report": parameter_verification_report,
        "recommendation": recommendation
    }
