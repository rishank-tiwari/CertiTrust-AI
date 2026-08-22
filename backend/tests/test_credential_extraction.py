"""
CertiTrust AI - Credential-Type Aware Extraction Unit and Pipeline Integration Tests.
Verifies parsing of the 10th marksheet OCR text:
- Extraction of student, father, and mother name.
- DOB mapping to date_of_birth and NOT to issue_date.
- Certificate ID / CGPA returning null instead of fallback values.
- Clean formatting in plain text reports.
"""

from ai.extraction.extraction_service import extraction_service
from ai.report.report_service import report_service


def test_10th_marksheet_extraction_details():
    ocr_text = (
        "Board of Secondary Education, Rajasthan\n"
        "Secondary Examination 2022\n"
        "Roll No: 1266778\n"
        "Centre: 05027\n"
        "District: BHARATPUR\n"
        "School: (1050437) SONI ACADEMY SR SEC SCH, NEAR GIRISH RESORT, ATALBAND, BHARATPUR\n"
        "Student Name: RISHANK TIWARI\n"
        "Mother's Name: BHAVNA SHARMA\n"
        "Father's Name: GAJENDRA TIWARI\n"
        "Date of Birth: 29-11-2006\n"
        "Subjects and Marks:\n"
        "HINDI: 58\n"
        "ENGLISH: 83\n"
        "SCIENCE: 63\n"
        "SOCIAL SCIENCE: 60\n"
        "MATHS: 87\n"
        "SANSKRIT: 90\n"
        "Total Maximum Marks: 600\n"
        "Total Marks Obtained: 441\n"
        "Percentage: 73.50%\n"
        "Result: FIRST DIVISION\n"
        "Board/Organization: RBSE, Ajmer\n"
        "Date printed on document: 13-06-2022"
    )

    doc_type = "10th Marksheet / Board Certificate"
    res = extraction_service.extract_information(ocr_text, document_type=doc_type)

    # 1. Verify exact fields
    assert res["student_name"] == "RISHANK TIWARI"
    assert res["mother_name"] == "BHAVNA SHARMA"
    assert res["father_name"] == "GAJENDRA TIWARI"
    assert res["date_of_birth"] == "29-11-2006"
    assert res["board"] == "RBSE, Ajmer"
    assert res["roll_number"] == "1266778"
    assert res["centre_number"] == "05027"
    assert res["district"] == "BHARATPUR"
    assert "SONI ACADEMY" in res["school_name"]
    assert len(res["subjects"]) == 6
    assert res["total_max_marks"] == 600
    assert res["total_marks_obtained"] == 441
    assert res["percentage"] == 73.50
    assert res["result"] == "FIRST DIVISION"
    assert res["issue_date"] == "13-06-2022"

    # 2. Verify negative rule conditions
    assert res["certificate_number"] is None
    assert res["cgpa"] is None

    print("Extraction fields verification passed successfully!")

    # 3. Verify report plain text layout
    report_res = report_service.generate_report(
        request_data={},
        extraction_data=res,
        trust_score_data={"decision": "Verified", "authenticity_score": 92, "trust_score": 92, "forgery_risk": "Low"}
    )

    report_text = report_res["report_text"]
    print("\nPlain Text Verification Report Preview:")
    print(report_text)

    # Asserts for plain text report sections
    assert "Student Name      : RISHANK TIWARI" in report_text
    assert "Board             : RBSE, Ajmer" in report_text
    assert "Date of Birth     : 29-11-2006" in report_text
    assert "Exam              : Secondary Examination 2022" in report_text
    assert "Roll Number       : 1266778" in report_text
    assert "Total Marks       : 441 / 600" in report_text
    assert "Percentage        : 73.5%" in report_text
    assert "Result            : FIRST DIVISION" in report_text

    # Rejection of wrong mappings
    assert "Certificate ID" not in report_text
    assert "CGPA" not in report_text
    assert "29-11-2006" not in report_text.split("Issue Date")[1] if "Issue Date" in report_text else True

    print("\nAll plain text report constraints verified successfully!")
