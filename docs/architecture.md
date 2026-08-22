# CertiTrust AI - System Architecture

This document describes the design, system workflow, and multi-portal interactions within the CertiTrust AI application.

---

## 1. System Design

CertiTrust AI is built as a modular monorepo system containing three distinct portals sharing a unified validation engine:

```
[Issuer Portal] ───► Register Credentials ───┐
                                              ├─► [FastAPI Verification Engine] ──► [MongoDB / Blockchain]
[Employer Portal] ──► Upload & Verify ────────┘
                                              ▲
[Student Portal] ───► Skill Passport / CV ────┘
```

---

## 2. Multi-Portal Workflows

### 2.1 Issuer Portal Workflow
1. **Upload Request**: The academic institution logs in and enters credential parameters (Student Name, University, Degree, Certificate/Roll Number, GPA/Percentage).
2. **File Registration**: The system saves the PDF/image document temporarily, computes its SHA-256 hash, and inserts the record into MongoDB Atlas.
3. **Ledger Integrity**: The certificate status is initialized as `verified` (if matched) or `pending` (awaiting evaluation).

### 2.2 Employer Verification Workflow
1. **Verification Request**: The employer uploads a candidate's marksheet (as a scanned PDF or image).
2. **AI Document Extraction**:
   *   **Stage 1**: The in-process classification service determines if the document is an educational credential.
   *   **Stage 2**: The PaddleOCR engine extracts all visible characters and coordinates from the page.
   *   **Stage 3**: The Natural Language Processing (NLP) model extracts entities (student name, CGPA, degree).
3. **Source of Truth Check**: The engine queries MongoDB Atlas to check if a credential matching the student name or certificate number exists.
4. **Validation checks**:
   *   **Hash Check**: Verifies if the file hash matches the issuer's registered file hash.
   *   **Parameter Check**: Compares extracted parameters (CGPA, degree, student name) against the stored source-of-truth values. Mismatches (e.g. GPA inflated from 6.70 to 8.70) trigger a `CHANGED` status.
   *   **Tampering Anomaly Check**: Runs forensic audits for structural alterations or image manipulations.
5. **Score Generation**: A composite Trust Score and Risk Assessment (LOW/MEDIUM/HIGH) are constructed, and verification results are written to the verification ledger.

### 2.3 Student Skill Passport Workflow
1. **Passport Sync**: The student logs in, views their verified academic credentials, and generates a public **Skill Passport** QR card.
2. **Resume Analysis**: The student uploads their PDF resume.
3. **Semantic Matching**: The Resume Intelligence engine extracts skills, evaluates matching academic courses from the verified passport ledger, extracts GitHub repository profiles, and generates an automated AI summary of candidate capabilities.
