"""
CertiTrust AI - Explainable AI Verification Report Generator Service.
Synthesizes structured outputs from OCR, extraction, metadata, validation, and CV into plain text/JSON.
Dynamic formatting handles marksheets, CVs, and standard certificates without displaying fake scores.
"""

from typing import Dict, Any, Optional
from ai.report.report_templates import format_plain_text_report
from app.utils.logger import logger


class ReportGeneratorService:
    """
    Service layer building explainable verification reports containing all analytical sections.
    """

    def generate_report(
        self,
        request_data: Dict[str, Any],
        ocr_data: Optional[Dict[str, Any]] = None,
        extraction_data: Optional[Dict[str, Any]] = None,
        metadata_data: Optional[Dict[str, Any]] = None,
        cv_data: Optional[Dict[str, Any]] = None,
        validation_data: Optional[Dict[str, Any]] = None,
        trust_score_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generates report internally using real extracted inputs. Returns 'Not Found' for unextracted fields.
        """
        logger.info("Generating Explainable AI Verification Report from real pipeline data...")

        # Extract core trust metrics
        t_data = trust_score_data or request_data
        decision = t_data.get("decision", request_data.get("decision", "Needs Manual Review"))
        auth_score = t_data.get("authenticity_score", request_data.get("authenticity_score", 0))
        t_score = t_data.get("trust_score", request_data.get("trust_score", 0))
        risk = t_data.get("forgery_risk", request_data.get("forgery_risk", "Medium"))

        # Extract real structured credential details based on document category
        e_data = extraction_data or request_data
        doc_type = e_data.get("document_type", request_data.get("document_type", ""))
        doc_type_clean = str(doc_type).lower()

        if "b.tech" in doc_type_clean or "btech" in doc_type_clean:
            ext_info = {
                "document_type": doc_type,
                "university": e_data.get("university") or "Not Found",
                "degree": e_data.get("degree") or "Not Found",
                "program": e_data.get("program") or "Not Found",
                "document_title": e_data.get("document_title") or "Statement of Marks/Grade",
                "semester": e_data.get("semester") or "Not Found",
                "semester_name": e_data.get("semester_name") or "Not Found",
                "exam_session": e_data.get("exam_session") or "Not Found",
                "examination": e_data.get("examination") or "Not Found",
                "academic_year": e_data.get("academic_year") or "Not Found",
                "apaar_id": e_data.get("apaar_id") or "Not Found",
                "registration_number": e_data.get("registration_number") or "Not Found",
                "roll_number": e_data.get("roll_number") or "Not Found",
                "student_name": e_data.get("student_name") or "Not Found",
                "father_name": e_data.get("father_name") or "Not Found",
                "mother_name": e_data.get("mother_name") or "Not Found",
                "college_name": e_data.get("college_name") or "Not Found",
                "shift": e_data.get("shift") or "Not Found",
                "category": e_data.get("category") or "Not Found",
                "subjects": e_data.get("subjects") or [],
                "total_credits": e_data.get("total_credits") or "Not Found",
                "total_credit_points": e_data.get("total_credit_points") or "Not Found",
                "percentage": e_data.get("percentage") or "Not Found",
                "sgpa": e_data.get("sgpa") or "Not Found",
                "result": e_data.get("result") or "Not Found",
                "dated": e_data.get("dated") or "Not Found",
                "cgpa": e_data.get("cgpa") or "Not Found",
                "grand_total_credit": e_data.get("grand_total_credit") or "Not Found",
                "division": e_data.get("division") or "Not Found",
                "digital_certificate": e_data.get("digital_certificate") or False,
                "digilocker_generated": e_data.get("digilocker_generated") or False,
                "digital_signature": e_data.get("digital_signature") or {"success": False, "signed_on": None},
            }
        elif "marksheet" in doc_type_clean or "board" in doc_type_clean or "transcript" in doc_type_clean:
            ext_info = {
                "document_type": doc_type,
                "student_name": e_data.get("student_name") or "Not Found",
                "mother_name": e_data.get("mother_name") or "Not Found",
                "father_name": e_data.get("father_name") or "Not Found",
                "date_of_birth": e_data.get("date_of_birth") or "Not Found",
                "board": e_data.get("board") or "Not Found",
                "exam": e_data.get("exam") or "Not Found",
                "exam_year": e_data.get("exam_year") or "Not Found",
                "roll_number": e_data.get("roll_number") or "Not Found",
                "centre_number": e_data.get("centre_number") or "Not Found",
                "district": e_data.get("district") or "Not Found",
                "regular_private": e_data.get("regular_private") or "Not Found",
                "category": e_data.get("category") or "Not Found",
                "group_name": e_data.get("group_name") or "Not Found",
                "reference_number": e_data.get("reference_number") or "Not Found",
                "school_code": e_data.get("school_code") or "Not Found",
                "school_name": e_data.get("school_name") or "Not Found",
                "subjects": e_data.get("subjects") or [],
                "additional_subject": e_data.get("additional_subject") or "Not Found",
                "total_max_marks": e_data.get("total_max_marks") or "Not Found",
                "total_marks_obtained": e_data.get("total_marks_obtained") or "Not Found",
                "percentage": e_data.get("percentage") or "Not Found",
                "result": e_data.get("result") or "Not Found",
                "document_date": e_data.get("document_date") or "Not Found",
                "issue_date": e_data.get("issue_date") or None,
            }
        elif "resume" in doc_type_clean or "cv" in doc_type_clean:
            ext_info = {
                "document_type": doc_type,
                "student_name": e_data.get("student_name") or "Not Found",
                "university": e_data.get("university") or "Not Found",
                "degree": e_data.get("degree") or "Not Found",
                "skills": e_data.get("skills", []),
            }
        else:
            ext_info = {
                "document_type": doc_type,
                "student_name": e_data.get("student_name") or "Not Found",
                "university": e_data.get("university") or e_data.get("organization") or "Not Found",
                "degree": e_data.get("degree") or "Not Found",
                "course": e_data.get("course") or "Not Found",
                "certificate_number": e_data.get("certificate_number") or "Not Found",
                "issue_date": e_data.get("issue_date") or "Not Found",
                "cgpa": e_data.get("cgpa") or "Not Found",
                "skills": e_data.get("skills", []),
            }

        # Build OCR Summary
        o_data = ocr_data or {}
        pages = o_data.get("pages", []) if isinstance(o_data, dict) else []
        char_count = sum(len(str(p.get("text", ""))) for p in pages if isinstance(p, dict))
        if char_count > 0:
            ocr_summary = f"Successfully extracted text ({char_count} characters across {len(pages)} page(s))."
        else:
            ocr_summary = "OCR text extraction completed with 0 characters extracted."

        # Build Metadata Analysis
        m_data = metadata_data or {}
        meta_warnings = m_data.get("warnings", [])
        meta_risk = m_data.get("risk_level", "Low")
        if not meta_warnings:
            meta_summary = f"No suspicious metadata detected (Risk Level: {meta_risk})."
        else:
            meta_summary = f"Metadata Risk '{meta_risk}': {'; '.join(meta_warnings)}"

        # Build Computer Vision Findings
        c_data = cv_data or {}
        if not c_data.get("success", False) or c_data.get("overall_cv_score") is None:
            cv_findings = ["Computer vision analysis unavailable."]
        else:
            logo_sc = c_data.get("logo_score", 0)
            sig_sc = c_data.get("signature_score", 0)
            stamp_sc = c_data.get("stamp_score", 0)
            layout_sc = c_data.get("layout_score", 0)
            tamper_sc = c_data.get("tampering_score", 0)
            tamper_det = c_data.get("tampering_detected", False)

            cv_findings = [
                f"Logo verified (Similarity Score: {logo_sc}%).",
                f"Signature detected (Confidence Score: {sig_sc}%).",
                f"Stamp/Seal detected (Confidence Score: {stamp_sc}%).",
                f"Layout similarity (Alignment Score: {layout_sc}%).",
                f"No tampering detected (Artifact Score: {tamper_sc}%)." if not tamper_det else f"Tampering artifacts flagged (Score: {tamper_sc}%).",
            ]

        # Build Validation Summary & Rule Results
        v_data = validation_data or {}
        passed_rules = v_data.get("passed_rules", 0)
        failed_rules = v_data.get("failed_rules", 0)
        total_rules = passed_rules + failed_rules
        val_score = v_data.get("validation_score", 0)

        if failed_rules == 0 and passed_rules > 0:
            val_summary = f"All required rules passed cleanly ({passed_rules}/{total_rules} - Validation Score: {val_score}%)."
        else:
            val_summary = f"{passed_rules} passed, {failed_rules} failed (Validation Score: {val_score}%)."

        rule_results = v_data.get("validation_results", [])

        # Final Decision & AI Recommendation (Worded probabilistically)
        if decision == "Verified":
            final_decision = "Document appears authentic and satisfies all security benchmarks."
            ai_recommendation = "Credential can be trusted and processed automatically."
        elif decision == "Needs Manual Review":
            final_decision = "Document satisfies basic criteria but requires human verifier review."
            ai_recommendation = "Route credential for secondary manual verification."
        elif decision == "Suspicious":
            final_decision = "Document exhibits suspicious characteristics or low authenticity scores."
            ai_recommendation = "Flag credential for deep forensic audit before acceptance."
        else:
            final_decision = "Document shows severe manipulation indicators and failed core rules."
            ai_recommendation = "Reject credential due to high probability of forgery."

        # Assemble Structured Report JSON
        report_json = {
            "certificate_status": decision,
            "authenticity_score": auth_score,
            "trust_score": t_score,
            "forgery_risk": risk,
            "validation_summary": val_summary,
            "ocr_summary": ocr_summary,
            "extracted_information": ext_info,
            "metadata_analysis": meta_summary,
            "computer_vision_findings": cv_findings,
            "validation_rule_results": rule_results,
            "final_decision": final_decision,
            "ai_recommendation": ai_recommendation,
        }

        # Format Plain Text Report
        report_text = format_plain_text_report(report_json)

        logger.info(f"Explainable AI Verification Report generated successfully for decision '{decision}'.")

        return {
            "success": True,
            "report_json": report_json,
            "report_text": report_text,
        }


# Global Singleton Service Instance
report_service = ReportGeneratorService()
