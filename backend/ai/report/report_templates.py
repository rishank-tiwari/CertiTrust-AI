"""
CertiTrust AI - Explainable AI Report Templates & Formatting Utilities.
Generates human-readable plain text reports from structured AI module outputs.
Credential-type aware to cleanly format marksheets and CVs without displaying incorrect fields.
"""

from typing import Dict, Any, List


def format_plain_text_report(report_json: Dict[str, Any]) -> str:
    """
    Renders a formatted, human-readable plain text verification report from structured JSON payload.
    """
    sections = []

    sections.append("==================================================")
    sections.append("       CERTITRUST AI VERIFICATION REPORT          ")
    sections.append("==================================================\n")

    # 1. Certificate Status
    sections.append(f"1. Certificate Status:\n   {report_json.get('certificate_status', 'N/A')}\n")

    # 2. Authenticity Score
    auth_score = report_json.get('authenticity_score')
    auth_str = f"{auth_score}%" if auth_score is not None else "N/A"
    sections.append(f"2. Authenticity Score:\n   {auth_str}\n")

    # 3. Trust Score
    t_score = report_json.get('trust_score')
    t_str = f"{t_score}%" if t_score is not None else "N/A"
    sections.append(f"3. Trust Score:\n   {t_str}\n")

    # 4. Forgery Risk
    sections.append(f"4. Forgery Risk:\n   {report_json.get('forgery_risk') or 'N/A'}\n")

    # 5. Validation Summary
    sections.append(f"5. Validation Summary:\n   {report_json.get('validation_summary', 'N/A')}\n")

    # 6. OCR Summary
    sections.append(f"6. OCR Summary:\n   {report_json.get('ocr_summary', 'N/A')}\n")

    # 7. Extracted Information (Credential-type aware)
    ext_info = report_json.get("extracted_information", {})
    doc_type = ext_info.get("document_type", "")
    doc_type_clean = str(doc_type).lower()

    sections.append("7. Extracted Information:")
    if "b.tech" in doc_type_clean or "btech" in doc_type_clean:
        sections.append(f"   - Student Name      : {ext_info.get('student_name', 'N/A')}")
        sections.append(f"   - University        : {ext_info.get('university', 'N/A')}")
        sections.append(f"   - College Name      : {ext_info.get('college_name', 'N/A')}")
        sections.append(f"   - Degree            : {ext_info.get('degree', 'N/A')}")
        sections.append(f"   - Program           : {ext_info.get('program', 'N/A')}")
        sections.append(f"   - Semester          : {ext_info.get('semester_name', 'N/A')}")
        sections.append(f"   - Registration No   : {ext_info.get('registration_number', 'N/A')}")
        sections.append(f"   - Roll Number       : {ext_info.get('roll_number', 'N/A')}")
        sections.append(f"   - Category          : {ext_info.get('category', 'N/A')}")
        sections.append(f"   - Examination       : {ext_info.get('examination', 'N/A')}")

        subjects = ext_info.get('subjects', [])
        if subjects:
            sections.append("   - Subjects & Grades :")
            for s in subjects:
                sections.append(f"       * [{s.get('course_code')}]: {s.get('subject'):<30} (Grade: {s.get('grade')}, Credits: {s.get('credits')}, Credit Points: {s.get('credit_points')})")

        sections.append(f"   - Total Credits     : {ext_info.get('total_credits', 'N/A')}")
        sections.append(f"   - Total Credit Pts  : {ext_info.get('total_credit_points', 'N/A')}")
        sections.append(f"   - SGPA / CGPA       : {ext_info.get('sgpa', 'N/A')} / {ext_info.get('cgpa', 'N/A')}")
        sections.append(f"   - Percentage        : {ext_info.get('percentage', 'N/A')}%")
        sections.append(f"   - Result / Division : {ext_info.get('result', 'N/A')} / {ext_info.get('division', 'N/A')}")
        sections.append(f"   - Document Date     : {ext_info.get('dated', 'N/A')}")

        sig = ext_info.get('digital_signature', {})
        if sig.get('success'):
            sections.append(f"   - Digital Signature : Signed on {sig.get('signed_on')}")
        else:
            sections.append(f"   - Digital Signature : N/A")
        sections.append("")
    elif "marksheet" in doc_type_clean or "board" in doc_type_clean or "transcript" in doc_type_clean:
        sections.append(f"   - Student Name      : {ext_info.get('student_name', 'N/A')}")
        sections.append(f"   - Mother's Name     : {ext_info.get('mother_name', 'N/A')}")
        sections.append(f"   - Father's Name     : {ext_info.get('father_name', 'N/A')}")
        if ext_info.get('date_of_birth') and ext_info.get('date_of_birth') != "Not Found":
            sections.append(f"   - Date of Birth     : {ext_info.get('date_of_birth')}")
        sections.append(f"   - Board             : {ext_info.get('board', 'N/A')}")
        sections.append(f"   - Exam              : {ext_info.get('exam', 'N/A')}")
        sections.append(f"   - Exam Year         : {ext_info.get('exam_year', 'N/A')}")
        sections.append(f"   - Roll Number       : {ext_info.get('roll_number', 'N/A')}")
        if ext_info.get('centre_number') and ext_info.get('centre_number') != "Not Found":
            sections.append(f"   - Centre Number     : {ext_info.get('centre_number')}")
        if ext_info.get('district') and ext_info.get('district') != "Not Found":
            sections.append(f"   - District          : {ext_info.get('district')}")
        if ext_info.get('regular_private') and ext_info.get('regular_private') != "Not Found":
            sections.append(f"   - Regular/Private   : {ext_info.get('regular_private')}")
        if ext_info.get('group_name') and ext_info.get('group_name') != "Not Found":
            sections.append(f"   - Group Name        : {ext_info.get('group_name')}")
        if ext_info.get('reference_number') and ext_info.get('reference_number') != "Not Found":
            sections.append(f"   - Reference Number  : {ext_info.get('reference_number')}")
        if ext_info.get('school_code') and ext_info.get('school_code') != "Not Found":
            sections.append(f"   - School Code       : {ext_info.get('school_code')}")
        if ext_info.get('school_name') and ext_info.get('school_name') != "Not Found":
            sections.append(f"   - School Name       : {ext_info.get('school_name')}")

        # List individual subjects dynamically
        subjects = ext_info.get('subjects', [])
        if subjects:
            sections.append("   - Subjects & Marks  :")
            for s in subjects:
                sections.append(f"       * {s.get('name'):<20}: {s.get('marks_obtained')}")
        if ext_info.get('additional_subject') and ext_info.get('additional_subject') != "Not Found":
            sections.append(f"   - Additional Sub    : {ext_info.get('additional_subject')}")

        total_obt = ext_info.get('total_marks_obtained')
        total_max = ext_info.get('total_max_marks')
        if total_obt is not None and total_max is not None:
            sections.append(f"   - Total Marks       : {total_obt} / {total_max}")
        else:
            sections.append(f"   - Total Marks       : N/A")

        pct = ext_info.get('percentage')
        sections.append(f"   - Percentage        : {f'{pct}%' if pct is not None else 'N/A'}")
        sections.append(f"   - Result            : {ext_info.get('result', 'N/A')}")
        if ext_info.get('document_date') and ext_info.get('document_date') != "Not Found":
            sections.append(f"   - Document Date     : {ext_info.get('document_date')}")
        if ext_info.get('issue_date'):
            sections.append(f"   - Issue Date        : {ext_info.get('issue_date')}")
        sections.append("")
    elif "resume" in doc_type_clean or "cv" in doc_type_clean:
        sections.append(f"   - Student Name      : {ext_info.get('student_name', 'N/A')}")
        sections.append(f"   - University        : {ext_info.get('university', 'N/A')}")
        sections.append(f"   - Degree            : {ext_info.get('degree', 'N/A')}")
        skills = ext_info.get('skills', [])
        sections.append(f"   - Skills            : {', '.join(skills) if skills else 'N/A'}\n")
    else:
        sections.append(f"   - Student Name      : {ext_info.get('student_name', 'N/A')}")
        sections.append(f"   - University        : {ext_info.get('university', 'N/A')}")
        sections.append(f"   - Degree            : {ext_info.get('degree', 'N/A')}")
        sections.append(f"   - Course / Branch   : {ext_info.get('course', 'N/A')}")
        sections.append(f"   - Certificate ID    : {ext_info.get('certificate_number', 'N/A')}")
        sections.append(f"   - Issue Date        : {ext_info.get('issue_date', 'N/A')}")
        sections.append(f"   - CGPA / Marks      : {ext_info.get('cgpa', 'N/A')}\n")

    # 8. Metadata Analysis
    sections.append(f"8. Metadata Analysis:\n   {report_json.get('metadata_analysis', 'N/A')}\n")

    # 9. Computer Vision Findings
    cv_findings = report_json.get("computer_vision_findings", [])
    sections.append("9. Computer Vision Findings:")
    for finding in cv_findings:
        sections.append(f"   - {finding}")
    sections.append("")

    # 10. Validation Rule Results
    rule_results = report_json.get("validation_rule_results", [])
    sections.append("10. Validation Rule Results:")
    for r in rule_results:
        status_symbol = "[PASSED]" if r.get("passed") else "[FAILED]"
        sections.append(f"   {status_symbol} {r.get('rule')}: {r.get('reason')}")
    sections.append("")

    # 11. AI Authenticity Assessment
    sections.append(f"11. AI Authenticity Assessment:\n    {report_json.get('final_decision', 'N/A')}\n")

    # 12. AI Recommendation
    sections.append(f"12. AI Recommendation:\n    {report_json.get('ai_recommendation', 'N/A')}\n")

    sections.append("==================================================")
    sections.append("           END OF CERTITRUST REPORT               ")
    sections.append("==================================================")

    return "\n".join(sections)
