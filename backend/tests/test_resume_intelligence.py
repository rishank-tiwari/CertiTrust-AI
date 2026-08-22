"""
CertiTrust AI - Resume Intelligence & Credential Verification Test Suite.
Verifies the 12 required test scenarios:
1. TEST 1: Upload valid resume (preferred endpoint /api/v1/employer/resume/analyze).
2. TEST 2: Resume contains skills that exist in Skill Passport (e.g. Python -> SUPPORTED).
3. TEST 3: Resume contains skill not present in Skill Passport (e.g. AWS -> NOT_VERIFIED).
4. TEST 5: Resume project contains valid public GitHub repository (e.g. EcoTwin AI -> ANALYZED).
5. TEST 6: GitHub repository contains claimed technologies (e.g. Python, TensorFlow -> SUPPORTED).
6. TEST 7: Resume claims technology that cannot be found in repository (e.g. Kubernetes -> NOT_VERIFIED).
7. TEST 8: GitHub URL is invalid or unavailable (fails gracefully).
8. TEST 9: Resume has no GitHub URLs (analysis still completes).
9. TEST 10: Invalid file (returns clear validation error).
10. TEST 4: Trusted Skill Passport explicitly conflicts with resume claim (CONTRADICTED).
11. TEST 11: Existing credential verification (POST /api/v1/employer/verify remains functional).
12. TEST 12: Fake credential with changed CGPA (CHANGED parameter behavior remains unchanged).
13. TEST 13 (ADDITIONAL): Selectable Text PDF Resume.
14. TEST 14 (ADDITIONAL): Scanned Image PDF Resume (forces OCR fallback).
"""

import io
import os
os.environ["FLAGS_use_onednn"] = "0"
os.environ["FLAGS_use_mkldnn"] = "0"
os.environ["FLAGS_enable_pir_api"] = "0"

from fastapi.testclient import TestClient
from PIL import Image, ImageDraw, PngImagePlugin
import fitz  # PyMuPDF
from app.main import app
from app.services.registry_service import credential_registry
from tests.test_employer_verification import create_mock_btech_bytes


def create_resume_bytes(
    name: str = "RISHANK TIWARI",
    cgpa: str = "8.5",
    skills: str = "Python, FastAPI, React.js, TensorFlow, PyTorch, Computer Vision, Git & GitHub, AWS",
    projects_section: str = (
        "PROJECTS\n"
        "- EcoTwin AI: Digital twin for ecosystem tracking using Python and TensorFlow. GitHub: https://github.com/rishank/ecotwin-ai\n"
        "- PlantTalk AI: Generative AI for agricultural diagnostics using PyTorch. GitHub: https://github.com/rishank/planttalk-ai\n"
    )
) -> bytes:
    cert = Image.new("RGB", (800, 1100), color=(255, 255, 255))
    draw = ImageDraw.Draw(cert)
    text_content = (
        f"{name}\n"
        f"Email: rishank@example.com | GitHub: github.com/rishank | LinkedIn: linkedin.com/in/rishank\n"
        f"Motivated B.Tech student passionate about Artificial Intelligence, Machine Learning, and Full-Stack Development.\n"
        f"EDUCATION\n"
        f"Bachelor of Technology (B.Tech) - Parul University (CGPA: {cgpa})\n"
        f"TECHNICAL SKILLS\n"
        f"{skills}\n"
        f"{projects_section}\n"
        f"HACKATHONS\n"
        f"Winner of DeepMind Hackathon 2026\n"
        f"ABOUT ME\n"
        f"Hardworking tech enthusiast eager to learn production AI workflows.\n"
    )
    draw.text((40, 40), text_content, fill=(0, 0, 0))
    meta = PngImagePlugin.PngInfo()
    meta.add_text("Comment", text_content)
    buf = io.BytesIO()
    cert.save(buf, format="PNG", pnginfo=meta)
    return buf.getvalue()


def create_selectable_pdf_bytes() -> bytes:
    """
    Generates a PDF containing digital selectable text using fitz (PyMuPDF).
    """
    doc = fitz.open()
    page = doc.new_page()
    rect = fitz.Rect(50, 50, 750, 1050)
    text = (
        "RISHANK TIWARI\n"
        "Email: rishank@example.com | GitHub: github.com/rishank\n"
        "EDUCATION\n"
        "Bachelor of Technology (B.Tech) - Parul University (CGPA: 8.5)\n"
        "TECHNICAL SKILLS\n"
        "Python, FastAPI, TensorFlow, AWS\n"
        "PROJECTS\n"
        "- EcoTwin AI: Digital twin using Python. GitHub: https://github.com/rishank/ecotwin-ai\n"
    )
    page.insert_textbox(rect, text)
    return doc.write()


def create_scanned_pdf_bytes() -> bytes:
    """
    Generates a scanned/image PDF (no selectable text) using fitz.
    """
    png_bytes = create_resume_bytes()
    img_doc = fitz.open(stream=png_bytes, filetype="png")
    return img_doc.convert_to_pdf()


def create_mock_failed_btech_bytes(name: str = "RISHANK TIWARI") -> bytes:
    cert = Image.new("RGB", (900, 1050), color=(255, 255, 255))
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
        f"Name: {name}\n"
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
        "6 03014602PC01 PYTHON PROGRAMMING F 0 4 0\n"
        "7 03019102BS01 LINEAR ALGEBRA B 6 4 24\n"
        "8 03M10002UE01 PRIVACY AND SECURITY IN ONLINE SOCIAL MEDIA B+ 7 3 21\n"
        "--------------------------------------------------\n"
        "TOTAL Credits: 21 Credit Points: 109\n"
        "SGPA: 5.19 CGPA: 5.19 Percentage: 51.90 RESULT: FAIL\n"
        "Dated: 30/06/2026 Division: FAIL\n"
        "This is a digital certificate. The certificate is electronically generated by DigiLocker - National Academic Depository.\n"
        "Digitally signed on Date: 22/07/2026 20:53:39 IST\n"
    )
    draw.text((40, 40), text_content, fill=(0, 0, 0))
    meta = PngImagePlugin.PngInfo()
    meta.add_text("Comment", text_content)
    buf = io.BytesIO()
    cert.save(buf, format="PNG", pnginfo=meta)
    return buf.getvalue()


def run_all_resume_intelligence_tests():
    client = TestClient(app)

    print("\n" + "="*60)
    print("STARTING 12+ RESUME INTELLIGENCE & VERIFICATION TESTS")
    print("="*60)

    # =========================================================================
    # SETUP: Register B.Tech marksheet (CGPA = 6.76)
    # =========================================================================
    credential_registry.clear()
    original_btech = create_mock_btech_bytes()
    reg_res = client.post(
        "/api/v1/issuer/credentials",
        files={"certificate": ("original_btech.png", original_btech, "image/png")}
    )
    assert reg_res.status_code == 201
    cred_id = reg_res.json()["credential_id"]
    print(f"Setup OK: Registered B.Tech credential '{cred_id}' (CGPA: 6.76)")

    # =========================================================================
    # TEST 1: Upload valid resume (preferred endpoint)
    # =========================================================================
    print("\nTEST 1: Upload valid resume (preferred endpoint)")
    resume_bytes = create_resume_bytes()
    res1 = client.post(
        "/api/v1/employer/resume/analyze",
        files={"resume": ("resume.png", resume_bytes, "image/png")}
    )
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["success"] is True
    assert data1["document_type"] == "RESUME"
    assert data1["analysis_status"] == "COMPLETED"
    print("[OK] TEST 1 PASSED: Resume successfully uploaded and parsed.")

    # =========================================================================
    # TEST 2: Resume contains skills that exist in Skill Passport
    # =========================================================================
    print("\nTEST 2: Skill exists in Skill Passport (Python -> SUPPORTED)")
    python_verif = next((s for s in data1["skill_analysis"] if s["skill"] == "Python"), None)
    assert python_verif is not None
    assert python_verif["status"] == "SUPPORTED"
    assert python_verif["skill_passport"] is True
    print("[OK] TEST 2 PASSED: Skill verified via Skill Passport returned status: SUPPORTED.")

    # =========================================================================
    # TEST 3: Resume contains skill not present in Skill Passport
    # =========================================================================
    print("\nTEST 3: Skill not in Skill Passport (AWS -> NOT_VERIFIED)")
    aws_verif = next((s for s in data1["skill_analysis"] if s["skill"] == "AWS"), None)
    assert aws_verif is not None
    assert aws_verif["status"] == "NOT_VERIFIED"
    assert aws_verif["skill_passport"] is False
    print("[OK] TEST 3 PASSED: Skill absent from Skill Passport returned status: NOT_VERIFIED.")

    # =========================================================================
    # TEST 5: Resume project contains valid public GitHub repository
    # =========================================================================
    print("\nTEST 5: Project contains valid public GitHub repo")
    proj_eco = next((p for p in data1["project_analysis"] if p["project_name"] == "EcoTwin AI"), None)
    assert proj_eco is not None
    assert proj_eco["github_analysis_status"] == "ANALYZED"
    assert proj_eco["github_url"] == "https://github.com/rishank/ecotwin-ai"
    print("[OK] TEST 5 PASSED: Public repository status is: ANALYZED.")

    # =========================================================================
    # TEST 6: GitHub repository contains claimed technologies
    # =========================================================================
    print("\nTEST 6: GitHub repository contains claimed technologies (Python, TensorFlow)")
    tech_claims = proj_eco["claim_comparisons"]
    py_claim = next((c for c in tech_claims if "Python" in c["claim"]), None)
    tf_claim = next((c for c in tech_claims if "TensorFlow" in c["claim"]), None)
    assert py_claim is not None and py_claim["status"] == "SUPPORTED"
    assert tf_claim is not None and tf_claim["status"] == "SUPPORTED"
    assert proj_eco["project_status"] == "SUPPORTED"
    print("[OK] TEST 6 PASSED: Claims match detected files returning status: SUPPORTED.")

    # =========================================================================
    # TEST 7: Resume claims technology that cannot be found in repository
    # =========================================================================
    print("\nTEST 7: Project claims technology not in repo (Kubernetes -> NOT_VERIFIED)")
    resume_k8s = create_resume_bytes(
        projects_section=(
            "PROJECTS\n"
            "- EcoTwin AI: Project using Python and Kubernetes. GitHub: https://github.com/rishank/ecotwin-ai\n"
        )
    )
    res7 = client.post(
        "/api/v1/employer/resume/analyze",
        files={"resume": ("resume_k8s.png", resume_k8s, "image/png")}
    )
    assert res7.status_code == 200
    data7 = res7.json()
    proj_eco_k8s = next((p for p in data7["project_analysis"] if p["project_name"] == "EcoTwin AI"), None)
    assert proj_eco_k8s is not None
    k8s_claim = next((c for c in proj_eco_k8s["claim_comparisons"] if "Kubernetes" in c["claim"]), None)
    assert k8s_claim is not None
    assert k8s_claim["status"] == "NOT_VERIFIED"
    print("[OK] TEST 7 PASSED: Technology absent from repo returns status: NOT_VERIFIED.")

    # =========================================================================
    # TEST 8: GitHub URL is invalid / unavailable (graceful failure)
    # =========================================================================
    print("\nTEST 8: GitHub URL is invalid or deleted (deleted-repo -> UNAVAILABLE)")
    resume_del_gh = create_resume_bytes(
        projects_section=(
            "PROJECTS\n"
            "- EcoTwin AI: Digital twin. GitHub: https://github.com/rishank/deleted-repo\n"
        )
    )
    res8 = client.post(
        "/api/v1/employer/resume/analyze",
        files={"resume": ("resume_del.png", resume_del_gh, "image/png")}
    )
    assert res8.status_code == 200
    data8 = res8.json()
    proj_del = next((p for p in data8["project_analysis"] if p["project_name"] == "EcoTwin AI"), None)
    assert proj_del is not None
    assert proj_del["github_analysis_status"] == "UNAVAILABLE"
    assert proj_del["project_status"] == "NOT_ANALYZABLE"
    print("[OK] TEST 8 PASSED: Invalid/deleted repository handled gracefully with status: UNAVAILABLE.")

    # =========================================================================
    # TEST 9: Resume has no GitHub URLs
    # =========================================================================
    print("\nTEST 9: Resume has no GitHub URLs")
    resume_no_gh = create_resume_bytes(
        projects_section=(
            "PROJECTS\n"
            "- EcoTwin AI: Digital twin for ecosystem tracking.\n"
        )
    )
    res9 = client.post(
        "/api/v1/employer/resume/analyze",
        files={"resume": ("resume_no_gh.png", resume_no_gh, "image/png")}
    )
    assert res9.status_code == 200
    data9 = res9.json()
    proj_no_gh = next((p for p in data9["project_analysis"] if p["project_name"] == "EcoTwin AI"), None)
    assert proj_no_gh is not None
    assert proj_no_gh["github_analysis_status"] == "NOT_AVAILABLE"
    assert proj_no_gh["project_status"] == "NOT_ANALYZABLE"
    print("[OK] TEST 9 PASSED: Resume without project links processed successfully.")

    # =========================================================================
    # TEST 10: Invalid file type
    # =========================================================================
    print("\nTEST 10: Invalid file type (.exe)")
    res10 = client.post(
        "/api/v1/employer/resume/analyze",
        files={"resume": ("malicious.exe", b"binarycontent", "application/octet-stream")}
    )
    assert res10.status_code == 400
    assert "Unsupported file format" in res10.json()["detail"]
    print("[OK] TEST 10 PASSED: Gated and returned clear HTTP 400 validation error.")

    # =========================================================================
    # TEST 4: Trusted Skill Passport explicitly conflicts with resume claim
    # =========================================================================
    print("\nTEST 4: Trusted Skill Passport conflicts (Failed course Python -> CONTRADICTED)")
    # Clear registry, register B.Tech with F grade in Python
    credential_registry.clear()
    failed_btech = create_mock_failed_btech_bytes()
    reg_res_fail = client.post(
        "/api/v1/issuer/credentials",
        files={"certificate": ("failed_btech.png", failed_btech, "image/png")}
    )
    assert reg_res_fail.status_code == 201
    
    # Run analysis again
    res4 = client.post(
        "/api/v1/employer/resume/analyze",
        files={"resume": ("resume.png", resume_bytes, "image/png")}
    )
    assert res4.status_code == 200
    data4 = res4.json()
    python_fail = next((s for s in data4["skill_analysis"] if s["skill"] == "Python"), None)
    assert python_fail is not None
    assert python_fail["status"] == "CONTRADICTED"
    assert python_fail["skill_passport"] is False
    print("[OK] TEST 4 PASSED: Explicit subject failure in Skill Passport returned status: CONTRADICTED.")

    # Re-register original for compatibility tests
    credential_registry.clear()
    client.post(
        "/api/v1/issuer/credentials",
        files={"certificate": ("original_btech.png", original_btech, "image/png")}
    )

    # =========================================================================
    # TEST 11: Existing credential verification remains unchanged
    # =========================================================================
    print("\nTEST 11: Existing credential verification (POST /api/v1/employer/verify)")
    res11 = client.post(
        "/api/v1/employer/verify",
        files={"certificate": ("candidate_btech.png", original_btech, "image/png")},
        data={"credential_id": cred_id}
    )
    assert res11.status_code == 200
    data11 = res11.json()
    assert data11["verification_status"] == "VERIFIED"
    assert data11["risk_level"] == "LOW"
    assert data11["hash_match"] is True
    print("[OK] TEST 11 PASSED: Original credential verification workflow is intact.")

    # =========================================================================
    # TEST 12: Fake credential with changed CGPA
    # =========================================================================
    print("\nTEST 12: Fake credential with changed CGPA (mismatch / changed parameters)")
    forged_cgpa_bytes = create_mock_btech_bytes(cgpa="9.76")
    res12 = client.post(
        "/api/v1/employer/verify",
        files={"certificate": ("forged_cgpa.png", forged_cgpa_bytes, "image/png")},
        data={"credential_id": cred_id}
    )
    assert res12.status_code == 200
    data12 = res12.json()
    assert data12["verification_status"] == "MISMATCH"
    assert data12["risk_level"] == "HIGH"
    
    change = data12["changed_parameters"][0]
    assert change["field"] == "cgpa"
    assert change["status"] == "CHANGED"
    assert float(change["original_value"]) == 6.76
    assert float(change["submitted_value"]) == 9.76
    assert float(change["difference"]) == 3.0
    print("[OK] TEST 12 PASSED: CGPA mismatch detected as CHANGED with correct difference and risk level.")

    # =========================================================================
    # TEST 13 (ADDITIONAL): Selectable Text PDF Resume
    # =========================================================================
    print("\nTEST 13: Selectable Text PDF Resume (Fast Native Path)")
    selectable_pdf = create_selectable_pdf_bytes()
    res13 = client.post(
        "/api/v1/employer/resume/analyze",
        files={"resume": ("resume_selectable.pdf", selectable_pdf, "application/pdf")}
    )
    assert res13.status_code == 200
    data13 = res13.json()
    assert data13["success"] is True
    assert data13["document_type"] == "RESUME"
    assert data13["analysis_status"] == "COMPLETED"
    print("[OK] TEST 13 PASSED: Selectable text PDF parsed quickly via native extraction path.")

    # =========================================================================
    # TEST 14 (ADDITIONAL): Scanned Image PDF Resume (forces OCR fallback)
    # =========================================================================
    print("\nTEST 14: Scanned Image PDF Resume (Forces OCR Fallback Path)")
    scanned_pdf = create_scanned_pdf_bytes()
    res14 = client.post(
        "/api/v1/employer/resume/analyze",
        files={"resume": ("resume_scanned.pdf", scanned_pdf, "application/pdf")}
    )
    assert res14.status_code == 200
    data14 = res14.json()
    assert data14["success"] is True
    assert data14["document_type"] == "RESUME"
    assert data14["analysis_status"] == "COMPLETED"
    print("[OK] TEST 14 PASSED: Scanned PDF fell back to image-rendering and OCR processing successfully.")

    print("\n" + "="*60)
    print("ALL TEST SCENARIOS PASSED SUCCESSFULLY [OK]")
    print("="*60)


if __name__ == "__main__":
    run_all_resume_intelligence_tests()
