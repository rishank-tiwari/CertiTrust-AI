"""
CertiTrust AI - Rule Validation Definitions.
Defines modular, credential-specific validation rules evaluating inputs from OCR, Extraction, Metadata, and Computer Vision modules.
Credential-type aware to handle 10th/12th marksheets, CVs, and B.Tech semester marksheets without failing core validation checks.
Treats placeholder extraction values like 'Not Found', 'unknown', 'n/a', 'none', 'null' as missing (FAILED).
"""

from typing import Dict, Any, List, Tuple


class RuleResult:
    """
    Data structure representing the outcome of a single validation rule check.
    """

    def __init__(self, rule: str, passed: bool, reason: str):
        self.rule = rule
        self.passed = passed
        self.reason = reason

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule": self.rule,
            "passed": self.passed,
            "reason": self.reason,
        }


# Configurable default threshold constants
DEFAULT_LOGO_THRESHOLD = 70
DEFAULT_SIGNATURE_THRESHOLD = 70
DEFAULT_LAYOUT_THRESHOLD = 70


def is_valid_value(val: Any) -> bool:
    """
    Returns True if the value is extracted and is NOT a missing/placeholder value.
    """
    if val is None:
        return False
    val_str = str(val).strip().lower()
    if val_str in ["", "not found", "unknown", "n/a", "none", "null", "empty string", "placeholder"]:
        return False
    return True


def get_credential_validation_rules(
    ocr_data: Dict[str, Any],
    extraction_data: Dict[str, Any],
    metadata_data: Dict[str, Any],
    cv_data: Dict[str, Any],
    logo_threshold: int = DEFAULT_LOGO_THRESHOLD,
    signature_threshold: int = DEFAULT_SIGNATURE_THRESHOLD,
    layout_threshold: int = DEFAULT_LAYOUT_THRESHOLD,
) -> List[RuleResult]:
    """
    Returns a dynamic, custom list of validation rules tailored to the credential category.
    """
    doc_type = extraction_data.get("document_type", "")
    doc_type_clean = str(doc_type).lower()
    is_marksheet = "marksheet" in doc_type_clean or "board" in doc_type_clean or "transcript" in doc_type_clean
    is_btech = "b.tech" in doc_type_clean

    rules = []

    # 1. OCR Text Existence
    text_content = ""
    if isinstance(ocr_data, dict):
        pages = ocr_data.get("pages", [])
        if isinstance(pages, list):
            text_content = " ".join([str(p.get("text", "")) for p in pages if isinstance(p, dict)])
    ocr_passed = len(text_content.strip()) > 10
    ocr_reason = "Readable OCR text was extracted." if ocr_passed else "OCR failed to extract readable text."
    rules.append(RuleResult("OCR Text Existence", ocr_passed, ocr_reason))

    # 2. Student Name Extraction
    name_val = extraction_data.get("student_name")
    name_passed = is_valid_value(name_val)
    name_reason = f"Student name extracted: '{name_val}'." if name_passed else "Student name field is missing or invalid."
    rules.append(RuleResult("Student Name Extraction", name_passed, name_reason))

    # Category routing for dynamic rules
    if is_btech:
        # B.Tech Semester Marksheet Rules
        # 3. University Extraction
        uni_val = extraction_data.get("university")
        uni_passed = is_valid_value(uni_val)
        uni_reason = f"University extracted: '{uni_val}'." if uni_passed else "University field is missing."
        rules.append(RuleResult("University Extraction", uni_passed, uni_reason))

        # 4. Degree & Program Extraction
        deg_val = extraction_data.get("degree")
        prog_val = extraction_data.get("program")
        deg_passed = is_valid_value(deg_val) and is_valid_value(prog_val)
        deg_reason = f"Degree and program extracted: '{deg_val} - {prog_val}'." if deg_passed else "Degree or Program fields are missing."
        rules.append(RuleResult("Degree & Program Extraction", deg_passed, deg_reason))

        # 5. Semester Extraction
        sem_val = extraction_data.get("semester_name")
        sem_passed = is_valid_value(sem_val)
        sem_reason = f"Semester name extracted: '{sem_val}'." if sem_passed else "Semester name field is missing."
        rules.append(RuleResult("Semester Extraction", sem_passed, sem_reason))

        # 6. Examination & Academic Year
        exam_val = extraction_data.get("examination")
        ay_val = extraction_data.get("academic_year")
        exam_passed = is_valid_value(exam_val) and is_valid_value(ay_val)
        exam_reason = f"Examination session extracted: '{exam_val} ({ay_val})'." if exam_passed else "Examination session or academic year missing."
        rules.append(RuleResult("Examination Session Extraction", exam_passed, exam_reason))

        # 7. Registration Number
        reg_val = extraction_data.get("registration_number")
        reg_passed = is_valid_value(reg_val)
        reg_reason = f"Registration number extracted: '{reg_val}'." if reg_passed else "Registration number field is missing."
        rules.append(RuleResult("Registration Number Extraction", reg_passed, reg_reason))

        # 8. Roll Number Extraction
        roll_val = extraction_data.get("roll_number")
        roll_passed = is_valid_value(roll_val)
        roll_reason = f"Roll number extracted: '{roll_val}'." if roll_passed else "Roll number field is missing."
        rules.append(RuleResult("Roll Number Extraction", roll_passed, roll_reason))

        # 9. Parent Names
        f_name = extraction_data.get("father_name")
        m_name = extraction_data.get("mother_name")
        parent_passed = is_valid_value(f_name) and is_valid_value(m_name)
        parent_reason = f"Parent names extracted: Mother: '{m_name}', Father: '{f_name}'." if parent_passed else "Parent names are missing."
        rules.append(RuleResult("Parent Names Extraction", parent_passed, parent_reason))

        # 10. College Name & Shift
        col_val = extraction_data.get("college_name")
        col_passed = is_valid_value(col_val)
        col_reason = f"College department extracted: '{col_val}'." if col_passed else "College department is missing."
        rules.append(RuleResult("College Extraction", col_passed, col_reason))

        # 11. Category Extraction
        cat_val = extraction_data.get("category")
        cat_passed = is_valid_value(cat_val)
        cat_reason = f"Category extracted: '{cat_val}'." if cat_passed else "Category code field is missing."
        rules.append(RuleResult("Category Extraction", cat_passed, cat_reason))

        # 12. Subjects & Grades Extraction
        subjects = extraction_data.get("subjects", [])
        sub_passed = isinstance(subjects, list) and len(subjects) >= 4
        sub_reason = f"Extracted {len(subjects)} university course rows." if sub_passed else "Insufficient subjects extracted (minimum 4 required)."
        rules.append(RuleResult("Subjects & Grades Extraction", sub_passed, sub_reason))

        # 13. SGPA & CGPA Extraction
        sgpa_val = extraction_data.get("sgpa")
        cgpa_val = extraction_data.get("cgpa")
        gpa_passed = is_valid_value(sgpa_val) and is_valid_value(cgpa_val)
        gpa_reason = f"Extracted academic scores: SGPA: {sgpa_val}, CGPA: {cgpa_val}." if gpa_passed else "SGPA or CGPA academic scores are missing."
        rules.append(RuleResult("SGPA & CGPA Extraction", gpa_passed, gpa_reason))

        # 14. Total Credits Consistency Check
        tot_cred = extraction_data.get("total_credits")
        if sub_passed and is_valid_value(tot_cred):
            sum_credits = sum(s.get("credits", 0) for s in subjects)
            cred_passed = sum_credits == int(tot_cred)
            cred_reason = f"Sum of subject credits ({sum_credits}) matches total credits ({tot_cred})." if cred_passed else f"Credits sum ({sum_credits}) mismatch against total ({tot_cred})."
            rules.append(RuleResult("Total Credits Consistency Check", cred_passed, cred_reason))

        # 15. Total Credit Points Consistency Check
        tot_pts = extraction_data.get("total_credit_points")
        if sub_passed and is_valid_value(tot_pts):
            sum_pts = sum(s.get("credit_points", 0) for s in subjects)
            pts_passed = sum_pts == int(tot_pts)
            pts_reason = f"Sum of subject credit points ({sum_pts}) matches total credit points ({tot_pts})." if pts_passed else f"Credit points sum ({sum_pts}) mismatch against total ({tot_pts})."
            rules.append(RuleResult("Credit Points Consistency Check", pts_passed, pts_reason))

        # 16. Result & Division Extraction
        res_val = extraction_data.get("result")
        div_val = extraction_data.get("division")
        res_passed = is_valid_value(res_val) and is_valid_value(div_val)
        res_reason = f"Result status: '{res_val}', Division: '{div_val}'." if res_passed else "Result or division values missing."
        rules.append(RuleResult("Result Status Extraction", res_passed, res_reason))

        # 17. Digital Certificate Verification Indicators
        digi_cert = extraction_data.get("digital_certificate")
        digi_locker = extraction_data.get("digilocker_generated")
        indicator_passed = bool(digi_cert or digi_locker)
        indicator_reason = "DigiLocker / electronically generated certificate verified." if indicator_passed else "Digital certificate signature headers not found."
        rules.append(RuleResult("Digital Certificate Verification", indicator_passed, indicator_reason))

    elif is_marksheet:
        # 10th/12th Board Marksheet Rules
        # 3. Board Extraction
        board_val = extraction_data.get("board")
        board_passed = is_valid_value(board_val)
        board_reason = f"Board extracted: '{board_val}'." if board_passed else "Board field is missing."
        rules.append(RuleResult("Board Extraction", board_passed, board_reason))

        # 4. Exam Title Extraction
        exam_val = extraction_data.get("exam")
        exam_passed = is_valid_value(exam_val)
        exam_reason = f"Exam title extracted: '{exam_val}'." if exam_passed else "Exam title field is missing."
        rules.append(RuleResult("Exam Title Extraction", exam_passed, exam_reason))

        # 5. Exam Year Extraction
        year_val = extraction_data.get("exam_year")
        year_passed = is_valid_value(year_val)
        year_reason = f"Exam year extracted: '{year_val}'." if year_passed else "Exam year field is missing."
        rules.append(RuleResult("Exam Year Extraction", year_passed, year_reason))

        # 6. Roll Number Extraction
        roll_val = extraction_data.get("roll_number")
        roll_passed = is_valid_value(roll_val)
        roll_reason = f"Roll number extracted: '{roll_val}'." if roll_passed else "Roll number field is missing."
        rules.append(RuleResult("Roll Number Extraction", roll_passed, roll_reason))

        # 7. Centre Number Extraction
        centre_val = extraction_data.get("centre_number")
        centre_passed = is_valid_value(centre_val)
        centre_reason = f"Centre number extracted: '{centre_val}'." if centre_passed else "Centre number is missing."
        rules.append(RuleResult("Centre Number Extraction", centre_passed, centre_reason))

        # 8. District Extraction
        dist_val = extraction_data.get("district")
        dist_passed = is_valid_value(dist_val)
        dist_reason = f"District extracted: '{dist_val}'." if dist_passed else "District field is missing."
        rules.append(RuleResult("District Extraction", dist_passed, dist_reason))

        # 9. School Name Extraction
        school_val = extraction_data.get("school_name")
        school_passed = is_valid_value(school_val)
        school_reason = f"School name extracted: '{school_val}'." if school_passed else "School name field is missing."
        rules.append(RuleResult("School Name Extraction", school_passed, school_reason))

        # 10. Regular / Private Extraction
        rp_val = extraction_data.get("regular_private")
        rp_passed = is_valid_value(rp_val) and str(rp_val).upper() in ["REGULAR", "PRIVATE"]
        rp_reason = f"Enrollment type extracted: '{rp_val}'." if rp_passed else "Enrollment type (Regular/Private) is missing or invalid."
        rules.append(RuleResult("Enrollment Type Extraction", rp_passed, rp_reason))

        # 11. Category Extraction
        cat_val = extraction_data.get("category")
        cat_passed = is_valid_value(cat_val)
        cat_reason = f"Category code extracted: '{cat_val}'." if cat_passed else "Category code field is missing."
        rules.append(RuleResult("Category Extraction", cat_passed, cat_reason))

        # 12. Group Name Extraction
        grp_val = extraction_data.get("group_name")
        grp_passed = is_valid_value(grp_val)
        grp_reason = f"Group/Stream extracted: '{grp_val}'." if grp_passed else "Group/Stream field is missing."
        rules.append(RuleResult("Group Name Extraction", grp_passed, grp_reason))

        # 13. Reference Number Extraction
        ref_val = extraction_data.get("reference_number")
        ref_passed = is_valid_value(ref_val)
        ref_reason = f"Reference number extracted: '{ref_val}'." if ref_passed else "Reference number field is missing."
        rules.append(RuleResult("Reference Number Extraction", ref_passed, ref_reason))

        # 14. Subjects Extraction
        subjects = extraction_data.get("subjects", [])
        sub_passed = isinstance(subjects, list) and len(subjects) >= 3
        sub_reason = f"Extracted {len(subjects)} main subjects." if sub_passed else "Insufficient subjects extracted (minimum 3 required)."
        rules.append(RuleResult("Subjects Extraction", sub_passed, sub_reason))

        # 15. Marks & Percentage Extraction
        pct_val = extraction_data.get("percentage")
        tot_val = extraction_data.get("total_marks_obtained")
        pct_passed = is_valid_value(pct_val) and is_valid_value(tot_val)
        pct_reason = f"Extracted score: {tot_val} marks ({pct_val}%)." if pct_passed else "Total marks or percentage could not be parsed."
        rules.append(RuleResult("Marks & Percentage Extraction", pct_passed, pct_reason))

        # 16. Result Extraction
        res_val = extraction_data.get("result")
        res_passed = is_valid_value(res_val)
        res_reason = f"Result/Division extracted: '{res_val}'." if res_passed else "Result field is missing."
        rules.append(RuleResult("Result Extraction", res_passed, res_reason))

        # 17. Marks Consistency Check
        if sub_passed and is_valid_value(tot_val):
            sum_marks = sum(s.get("marks_obtained", 0) for s in subjects)
            marks_consistent = sum_marks == int(tot_val)
            marks_reason = f"Subject marks sum ({sum_marks}) matches total marks obtained ({tot_val})." if marks_consistent else f"Subject marks sum ({sum_marks}) does not match total marks obtained ({tot_val})."
            rules.append(RuleResult("Marks Consistency Check", marks_consistent, marks_reason))

        # 18. Percentage Consistency Check
        if is_valid_value(tot_val) and is_valid_value(pct_val) and is_valid_value(extraction_data.get("total_max_marks")):
            max_marks = int(extraction_data.get("total_max_marks"))
            obtained = int(tot_val)
            calc_pct = round((obtained / max_marks) * 100, 2)
            pct_consistent = abs(calc_pct - float(pct_val)) < 0.5
            pct_reason = f"Calculated percentage ({calc_pct}%) matches extracted percentage ({pct_val}%)." if pct_consistent else f"Calculated percentage ({calc_pct}%) does not match extracted percentage ({pct_val}%)."
            rules.append(RuleResult("Percentage Consistency Check", pct_consistent, pct_reason))

    else:
        # Standard Academic Certificate rules
        # 3. University Extraction
        uni_val = extraction_data.get("university") or extraction_data.get("organization")
        uni_passed = is_valid_value(uni_val)
        uni_reason = f"University/Institution extracted: '{uni_val}'." if uni_passed else "University/Institution field is missing."
        rules.append(RuleResult("University Extraction", uni_passed, uni_reason))

        # 4. Certificate Number Extraction
        cert_val = extraction_data.get("certificate_number")
        cert_passed = is_valid_value(cert_val)
        cert_reason = f"Certificate ID/Serial extracted: '{cert_val}'." if cert_passed else "Certificate number is missing."
        rules.append(RuleResult("Certificate Number Extraction", cert_passed, cert_reason))

        # 5. Issue Date Extraction
        date_val = extraction_data.get("issue_date")
        date_passed = is_valid_value(date_val)
        date_reason = f"Issue date extracted: '{date_val}'." if date_passed else "Issue date is missing."
        rules.append(RuleResult("Issue Date Extraction", date_passed, date_reason))

    # 19. Metadata Security Check (Applies to all)
    risk_level = str(metadata_data.get("risk_level", "Low")).lower()
    meta_passed = risk_level in ["low", "medium"]
    meta_reason = f"Metadata risk level is acceptable ({risk_level.capitalize()})." if meta_passed else f"High metadata risk: {metadata_data.get('warnings', [])}"
    rules.append(RuleResult("Metadata Security Check", meta_passed, meta_reason))

    # 20. Computer Vision Rules (ONLY added if CV analysis executed successfully)
    if cv_data.get("success", False) and cv_data.get("overall_cv_score") is not None:
        logo_score = int(cv_data.get("logo_score", 0))
        logo_passed = logo_score >= logo_threshold
        logo_reason = f"Logo score ({logo_score}%) satisfies minimum threshold ({logo_threshold}%)." if logo_passed else f"Logo score ({logo_score}%) is below threshold."
        rules.append(RuleResult("Logo Verification Check", logo_passed, logo_reason))

        sig_score = int(cv_data.get("signature_score", 0))
        sig_passed = sig_score >= signature_threshold
        sig_reason = f"Signature score ({sig_score}%) satisfies minimum threshold ({signature_threshold}%)." if sig_passed else f"Signature score ({sig_score}%) is below threshold."
        rules.append(RuleResult("Signature Confidence Check", sig_passed, sig_reason))

        lay_score = int(cv_data.get("layout_score", 0))
        lay_passed = lay_score >= layout_threshold
        lay_reason = f"Layout similarity score ({lay_score}%) satisfies minimum threshold ({layout_threshold}%)." if lay_passed else f"Layout similarity score ({lay_score}%) is below threshold."
        rules.append(RuleResult("Layout Alignment Check", lay_passed, lay_reason))

    # 21. Tampering Artifact Check (Only if CV data exists)
    if cv_data.get("success", False) and cv_data.get("tampering_score") is not None:
        tamper_detected = bool(cv_data.get("tampering_detected", False))
        tamper_score = int(cv_data.get("tampering_score", 0))
        tamper_passed = not tamper_detected and tamper_score < 40
        tamper_reason = "No tampering artifacts detected." if tamper_passed else f"Tampering artifacts detected (score: {tamper_score})."
        rules.append(RuleResult("Tampering Artifact Check", tamper_passed, tamper_reason))

    return rules
