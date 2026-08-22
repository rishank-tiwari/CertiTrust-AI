"""
CertiTrust AI - Comprehensive Credential Gating & Classification Test Suite.
Verifies Stage 1 Gating Rules across 8 scenarios:
1. Real 10th Marksheet (Supported -> Verification continues)
2. Internship Certificate (Supported -> Verification continues)
3. Hackathon Certificate (Supported -> Verification continues)
4. Random Unrelated Screenshot (Rejected -> Verification stopped early)
5. Random Non-Credential PDF (Rejected -> Verification stopped early)
6. Real 12th Marksheet (Supported -> Verification continues with detailed extraction)
7. Resume / CV (Rejected -> Verification stopped early)
8. B.Tech Semester Marksheet (Supported -> Detailed extraction and university verification)
"""

import io
from PIL import Image, ImageDraw, PngImagePlugin
from fastapi.testclient import TestClient
from app.main import app


def create_10th_marksheet_bytes() -> bytes:
    cert = Image.new("RGB", (800, 600), color=(250, 250, 250))
    draw = ImageDraw.Draw(cert)
    draw.rectangle([20, 20, 780, 580], outline=(0, 0, 0), width=3)
    text_content = (
        "Board of Secondary Education, Rajasthan\n"
        "Secondary Examination 2022\n"
        "Roll No: 1266778\n"
        "Centre: 05027\n"
        "District: BHARATPUR\n"
        "School: SONI ACADEMY\n"
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
    draw.text((40, 50), text_content, fill=(0, 0, 0))
    meta = PngImagePlugin.PngInfo()
    meta.add_text("Comment", text_content)
    buf = io.BytesIO()
    cert.save(buf, format="PNG", pnginfo=meta)
    return buf.getvalue()


def create_12th_marksheet_bytes() -> bytes:
    cert = Image.new("RGB", (800, 700), color=(250, 250, 250))
    draw = ImageDraw.Draw(cert)
    draw.rectangle([20, 20, 780, 680], outline=(0, 0, 0), width=3)
    text_content = (
        "BOARD OF SECONDARY EDUCATION, RAJASTHAN\n"
        "Certificate With Mark-Sheet\n"
        "Senior Secondary Examination 2024\n"
        "Roll No. 2535980\n"
        "Centre 05004\n"
        "District BHARATPUR\n"
        "Regular/Private REGULAR\n"
        "Category 1\n"
        "Group Name SCIENCE\n"
        "Ref. No. 0085974\n"
        "This is to certify that RISHANK TIWARI\n"
        "Mother's Name BHAVNA SHARMA\n"
        "Father's Name GAJENDRA TIWARI\n"
        "School: (1050247) JASWANT V.B.S. SR SEC SCH,JASWANT NAGAR,BHARATPUR\n"
        "Subjects and Marks:\n"
        "HINDI(COMP.) 69\n"
        "ENGLISH(COMP.) 80\n"
        "PHYSICS 65\n"
        "CHEMISTRY 62\n"
        "MATHEMATICS 59\n"
        "Additional Subject: SOC.SER.PLAN.\n"
        "Total Maximum Marks: 500\n"
        "Total Marks Obtained: 335\n"
        "Percentage: 67.00%\n"
        "Result: FIRST DIVISION\n"
        "DATE 20-05-24"
    )
    draw.text((40, 40), text_content, fill=(0, 0, 0))
    meta = PngImagePlugin.PngInfo()
    meta.add_text("Comment", text_content)
    buf = io.BytesIO()
    cert.save(buf, format="PNG", pnginfo=meta)
    return buf.getvalue()


def create_btech_marksheet_bytes() -> bytes:
    cert = Image.new("RGB", (900, 1000), color=(255, 255, 255))
    draw = ImageDraw.Draw(cert)
    text_content = (
        "Parul University\n"
        "Statement of Marks/Grade\n"
        "Bachelor of Technology\n"
        "Bachelor of Technology in Computer Science and Engineering - Artificial Intelligence and Machine Learning\n"
        "II SEMESTER\n"
        "MAY 2026 Examination 2025-26\n"
        "APAAR ID: 676402918047\n"
        "Reg No.: 2503031460770\n"
        "Roll No.: AF21650\n"
        "Name: RISHANK TIWARI\n"
        "Father's Name: GAJENDRA TIWARI\n"
        "Mother's Name: BHAVNA SHARMA\n"
        "College/Department: PARUL INSTITUTE OF ENGINEERING & TECHNOLOGY (FIRST SHIFT)\n"
        "Category: REGULAR\n"
        "--------------------------------------------------\n"
        "S.No. Course ID Subject Grade GradePoints Credits CreditPoints\n"
        "1 03010002HM01 ADVANCED COMMUNICATION AND INTERPERSONAL SKILLS B 6 2 12\n"
        "2 03010002MC01 ENVIRONMENTAL SCIENCE B+ 7 0 0\n"
        "3 03010502ES01 OBJECTED ORIENTED PROGRAMMING B+ 7 3 21\n"
        "4 03010601ES02 ELECTRICAL AND ELECTRONICS ENGINEERING B 6 4 24\n"
        "5 03010702ES01 ICT WORKSHOP B+ 7 1 7\n"
        "6 03014602PC01 PYTHON PROGRAMMING B+ 7 4 28\n"
        "7 03019102BS01 LINEAR ALGEBRA B 6 4 24\n"
        "8 03M10002UE01 PRIVACY AND SECURITY IN ONLINE SOCIAL MEDIA B+ 7 3 21\n"
        "--------------------------------------------------\n"
        "TOTAL Credits: 21 Credit Points: 137\n"
        "SGPA: 6.52 CGPA: 6.76 Percentage: 61.44 RESULT: PASS\n"
        "Dated: 30/06/2026 Division: FIRST CLASS\n"
        "This is a digital certificate. The certificate is electronically generated by DigiLocker - National Academic Depository.\n"
        "Digitally signed on Date: 22/07/2026 20:53:39 IST\n"
    )
    draw.text((40, 40), text_content, fill=(0, 0, 0))
    meta = PngImagePlugin.PngInfo()
    meta.add_text("Comment", text_content)
    buf = io.BytesIO()
    cert.save(buf, format="PNG", pnginfo=meta)
    return buf.getvalue()


def create_resume_bytes() -> bytes:
    cert = Image.new("RGB", (800, 900), color=(255, 255, 255))
    draw = ImageDraw.Draw(cert)
    text_content = (
        "RISHANK TIWARI\n"
        "Email: rishank@example.com | GitHub: github.com/rishank | LinkedIn: linkedin.com/in/rishank\n"
        "Motivated B.Tech student passionate about Artificial Intelligence, Machine Learning, and Full-Stack Development.\n"
        "EDUCATION\n"
        "Bachelor of Technology (B.Tech) - Parul University (CGPA: 8.5)\n"
        "TECHNICAL SKILLS\n"
        "Python, FastAPI, React.js, TensorFlow, PyTorch, Computer Vision, Git & GitHub\n"
        "PROJECTS\n"
        "- EcoTwin AI: Digital twin for ecosystem tracking.\n"
        "- PlantTalk AI: Generative AI for agricultural diagnostics.\n"
        "HACKATHONS\n"
        "Winner of DeepMind Hackathon 2026\n"
        "ABOUT ME\n"
        "Hardworking tech enthusiast eager to learn production AI workflows."
    )
    draw.text((40, 40), text_content, fill=(0, 0, 0))
    meta = PngImagePlugin.PngInfo()
    meta.add_text("Comment", text_content)
    buf = io.BytesIO()
    cert.save(buf, format="PNG", pnginfo=meta)
    return buf.getvalue()


def create_internship_certificate_bytes() -> bytes:
    cert = Image.new("RGB", (800, 600), color=(250, 250, 250))
    draw = ImageDraw.Draw(cert)
    draw.rectangle([20, 20, 780, 580], outline=(0, 0, 0), width=3)
    text_content = (
        "CERTIFICATE OF INTERNSHIP COMPLETION\n"
        "This is to certify that Rishank Tiwari has successfully completed\n"
        "his Software Development Internship at Google Cloud AI from 2026-06-01 to 2026-08-01.\n"
        "He worked on production NLP parsers and spaCy extraction modules.\n"
        "Reference ID: INT-998241 | Issued Date: 2026-08-15"
    )
    draw.text((40, 50), text_content, fill=(0, 0, 0))
    meta = PngImagePlugin.PngInfo()
    meta.add_text("Comment", text_content)
    buf = io.BytesIO()
    cert.save(buf, format="PNG", pnginfo=meta)
    return buf.getvalue()


def create_hackathon_certificate_bytes() -> bytes:
    cert = Image.new("RGB", (800, 600), color=(250, 250, 250))
    draw = ImageDraw.Draw(cert)
    draw.rectangle([20, 20, 780, 580], outline=(0, 0, 0), width=3)
    text_content = (
        "CERTIFICATE OF ACHIEVEMENT\n"
        "This is awarded to Team Antigravity for winning 1st Prize in the\n"
        "Global AI Hackathon 2026 organized by Google DeepMind and Devpost.\n"
        "Award ID: HACK-2026-10 | Issued Date: 2026-07-31"
    )
    draw.text((40, 50), text_content, fill=(0, 0, 0))
    meta = PngImagePlugin.PngInfo()
    meta.add_text("Comment", text_content)
    buf = io.BytesIO()
    cert.save(buf, format="PNG", pnginfo=meta)
    return buf.getvalue()


def create_random_screenshot_bytes() -> bytes:
    cert = Image.new("RGB", (800, 600), color=(255, 255, 255))
    draw = ImageDraw.Draw(cert)
    text_content = (
        "Google Search - Search Results\n"
        "Shopping Cart - Checkout Page\n"
        "1. Laptop Charger - $25.00\n"
        "2. Wireless Mouse - $15.00\n"
        "Subtotal: $40.00 | Tax: $4.00 | Total Amount Paid: $44.00\n"
        "Click here to print invoice or view transaction details."
    )
    draw.text((40, 50), text_content, fill=(0, 0, 0))
    meta = PngImagePlugin.PngInfo()
    meta.add_text("Comment", text_content)
    buf = io.BytesIO()
    cert.save(buf, format="PNG", pnginfo=meta)
    return buf.getvalue()


def create_random_pdf_bytes() -> bytes:
    try:
        import fitz
        doc = fitz.open()
        page = doc.new_page(width=600, height=800)
        page.insert_text(
            (50, 50),
            "USER MANUAL - INSTALLATION GUIDE\n"
            "Step 1: Download the installer package from website.\n"
            "Step 2: Double click setup.exe and follow screen instructions.\n"
            "For troubleshooting, contact our support team or email help@example.com.",
            fontsize=11,
        )
        return doc.write()
    except Exception:
        return b"%PDF-1.4\n%Unrelated text doc\n"


def test_credential_gating_scenarios():
    client = TestClient(app)

    # Scenario 1: Real 10th Marksheet (Supported -> Continue)
    print("\n---------------------------------------------")
    print("Scenario 1: Real 10th Marksheet")
    res1 = client.post(
        "/api/v1/analyze",
        files={"certificate": ("marksheet_10th.png", create_10th_marksheet_bytes(), "image/png")}
    )
    assert res1.status_code == 200
    data1 = res1.json()
    print("is_supported:", data1["is_supported"])
    print("verification_stopped:", data1.get("verification_stopped"))
    print("document_type:", data1["document_type"])
    assert data1["is_supported"] is True
    assert data1.get("verification_stopped") is False
    assert data1["ocr"] is not None

    # Scenario 2: Internship Certificate (Supported -> Continue)
    print("\n---------------------------------------------")
    print("Scenario 2: Internship Certificate")
    res2 = client.post(
        "/api/v1/analyze",
        files={"certificate": ("internship.png", create_internship_certificate_bytes(), "image/png")}
    )
    assert res2.status_code == 200
    data2 = res2.json()
    print("is_supported:", data2["is_supported"])
    print("verification_stopped:", data2.get("verification_stopped"))
    print("document_type:", data2["document_type"])
    assert data2["is_supported"] is True
    assert data2.get("verification_stopped") is False

    # Scenario 3: Hackathon Certificate (Supported -> Continue)
    print("\n---------------------------------------------")
    print("Scenario 3: Hackathon Certificate")
    res3 = client.post(
        "/api/v1/analyze",
        files={"certificate": ("hackathon.png", create_hackathon_certificate_bytes(), "image/png")}
    )
    assert res3.status_code == 200
    data3 = res3.json()
    print("is_supported:", data3["is_supported"])
    print("verification_stopped:", data3.get("verification_stopped"))
    print("document_type:", data3["document_type"])
    assert data3["is_supported"] is True
    assert data3.get("verification_stopped") is False

    # Scenario 4: Random Screenshot (Rejected -> STOP)
    print("\n---------------------------------------------")
    print("Scenario 4: Random Web Screenshot")
    res4 = client.post(
        "/api/v1/analyze",
        files={"certificate": ("screenshot.png", create_random_screenshot_bytes(), "image/png")}
    )
    assert res4.status_code == 200
    data4 = res4.json()
    print("is_supported:", data4["is_supported"])
    print("verification_stopped:", data4.get("verification_stopped"))
    print("document_type:", data4["document_type"])
    assert data4["is_supported"] is False
    assert data4.get("verification_stopped") is True
    assert data4["report"]["certificate_status"] == "Not an Educational Credential"
    assert data4["ocr"] is None

    # Scenario 5: Random Non-Credential PDF (Rejected -> STOP)
    print("\n---------------------------------------------")
    print("Scenario 5: Random Non-Credential PDF")
    res5 = client.post(
        "/api/v1/analyze",
        files={"certificate": ("manual.pdf", create_random_pdf_bytes(), "application/pdf")}
    )
    assert res5.status_code == 200
    data5 = res5.json()
    print("is_supported:", data5["is_supported"])
    print("verification_stopped:", data5.get("verification_stopped"))
    print("document_type:", data5["document_type"])
    assert data5["is_supported"] is False
    assert data5.get("verification_stopped") is True
    assert data5["ocr"] is None

    # Scenario 6: Real 12th Marksheet (Supported -> Detailed validation)
    print("\n---------------------------------------------")
    print("Scenario 6: Real 12th Marksheet")
    res6 = client.post(
        "/api/v1/analyze",
        files={"certificate": ("marksheet_12th.png", create_12th_marksheet_bytes(), "image/png")}
    )
    assert res6.status_code == 200
    data6 = res6.json()
    print("is_supported:", data6["is_supported"])
    print("verification_stopped:", data6.get("verification_stopped"))
    print("document_type:", data6["document_type"])
    assert data6["is_supported"] is True
    assert data6["document_type"] == "12th Marksheet"

    ext_res = data6["information_extraction"]
    print("Student Name Extracted:", ext_res["student_name"])
    print("Roll Number Extracted:", ext_res["roll_number"])
    print("Centre Number Extracted:", ext_res["centre_number"])
    print("District Extracted:", ext_res["district"])
    print("School Name Extracted:", ext_res["school_name"])
    print("Total Marks Extracted:", ext_res["total_marks_obtained"])
    print("Percentage Extracted:", ext_res["percentage"])

    # Core extractions verification
    assert ext_res["student_name"] == "RISHANK TIWARI"
    assert ext_res["roll_number"] == "2535980"
    assert ext_res["centre_number"] == "05004"
    assert ext_res["district"] == "BHARATPUR"
    assert ext_res["school_name"] == "JASWANT V.B.S. SR SEC SCH,JASWANT NAGAR,BHARATPUR"
    assert int(ext_res["total_marks_obtained"]) == 335
    assert float(ext_res["percentage"]) == 67.0
    assert len(ext_res["subjects"]) == 5

    # Scenario 7: Resume/CV (Rejected -> STOP)
    print("\n---------------------------------------------")
    print("Scenario 7: CV / Resume")
    res7 = client.post(
        "/api/v1/analyze",
        files={"certificate": ("resume.png", create_resume_bytes(), "image/png")}
    )
    assert res7.status_code == 200
    data7 = res7.json()
    print("is_supported:", data7["is_supported"])
    print("verification_stopped:", data7.get("verification_stopped"))
    print("document_type:", data7["document_type"])
    print("Reason:", data7["reason"])
    assert data7["is_supported"] is False
    assert data7.get("verification_stopped") is True
    assert data7["report"]["certificate_status"] == "Not an Educational Credential"

    # Scenario 8: B.Tech Semester Marksheet (Supported -> Verification continues)
    print("\n---------------------------------------------")
    print("Scenario 8: B.Tech Semester Marksheet")
    res8 = client.post(
        "/api/v1/analyze",
        files={"certificate": ("btech_marksheet.png", create_btech_marksheet_bytes(), "image/png")}
    )
    assert res8.status_code == 200
    data8 = res8.json()
    print("is_supported:", data8["is_supported"])
    print("verification_stopped:", data8.get("verification_stopped"))
    print("document_type:", data8["document_type"])
    assert data8["is_supported"] is True
    assert data8.get("verification_stopped") is False

    ext_btech = data8["information_extraction"]
    print("Student Name Extracted:", ext_btech["student_name"])
    print("Roll Number Extracted:", ext_btech["roll_number"])
    print("Registration No Extracted:", ext_btech["registration_number"])
    print("University Extracted:", ext_btech["university"])
    print("Semester Extracted:", ext_btech["semester"])
    print("SGPA Extracted:", ext_btech["sgpa"])
    print("CGPA Extracted:", ext_btech["cgpa"])
    print("Percentage Extracted:", ext_btech["percentage"])
    print("Result Extracted:", ext_btech["result"])
    print("Division Extracted:", ext_btech["division"])
    print("Digitally Signed Verified:", ext_btech["digital_signature"]["success"])
    print("Signed Date:", ext_btech["digital_signature"]["signed_on"])
    print("APAAR ID Extracted:", ext_btech["apaar_id"])
    print("Subjects Extracted count:", len(ext_btech["subjects"]))

    # Core assertions for B.Tech
    assert ext_btech["student_name"] == "RISHANK TIWARI"
    assert ext_btech["roll_number"] == "AF21650"
    assert ext_btech["registration_number"] == "2503031460770"
    assert ext_btech["university"] == "Parul University"
    assert ext_btech["semester"] == "II"
    assert float(ext_btech["sgpa"]) == 6.52
    assert float(ext_btech["cgpa"]) == 6.76
    assert float(ext_btech["percentage"]) == 61.44
    assert ext_btech["result"] == "PASS"
    assert ext_btech["division"] == "FIRST CLASS"
    assert ext_btech["digital_signature"]["success"] is True
    assert ext_btech["digital_signature"]["signed_on"] == "22/07/2026 20:53:39 IST"
    assert ext_btech["apaar_id"] == "676402918047"
    assert len(ext_btech["subjects"]) == 8

    print("\nALL 8 CREDENTIAL GATING SCENARIOS VERIFIED SUCCESSFULLY!")
