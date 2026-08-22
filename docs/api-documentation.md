# CertiTrust AI - API Documentation

This document describes the critical API endpoints exposed by the FastAPI verification service.

---

## 1. Authentication Router

### 1.1 Signup User
*   **Endpoint**: `POST /auth/signup`
*   **Description**: Creates a new user profile (institution, student, or employer).
*   **Payload**:
    ```json
    {
      "full_name": "Verify Corp",
      "email": "employer@corp.com",
      "password": "securepassword",
      "role": "employer",
      "organization": "Verify Corp"
    }
    ```
*   **Response**: `200 OK`

### 1.2 Login User
*   **Endpoint**: `POST /auth/login`
*   **Description**: Authenticates user credentials and yields a bearer JWT.
*   **Response**:
    ```json
    {
      "access_token": "eyJhbGciOi...",
      "token_type": "bearer",
      "user": {
        "email": "employer@corp.com",
        "role": "employer"
      }
    }
    ```

---

## 2. Issuer Endpoints

### 2.1 Register Credential
*   **Endpoint**: `POST /upload`
*   **Auth**: Required (Bearer Token, Role = `institution`)
*   **Content-Type**: `multipart/form-data`
*   **Parameters**:
    *   `student_name` (form-field string)
    *   `university` (form-field string)
    *   `degree` (form-field string)
    *   `certificate_number` (form-field string)
    *   `file` (file bytes)
*   **Response**:
    ```json
    {
      "id": "cert-uuid-12345",
      "student_name": "Rishank Tiwari",
      "university": "Verification University",
      "degree": "B.Tech",
      "certificate_number": "CERT-2026-999",
      "file_path": "uploads/20260822_original_cert.png",
      "file_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      "status": "pending"
    }
    ```

---

## 3. Employer Endpoints

### 3.1 Verify Uploaded Document
*   **Endpoint**: `POST /employer/verify-certificate`
*   **Auth**: Required (Bearer Token, Role = `employer`)
*   **Content-Type**: `multipart/form-data`
*   **Parameters**:
    *   `file` (file bytes)
*   **Response**:
    ```json
    {
      "status": "flagged",
      "message": "Content discrepancy detected.",
      "risk_level": "high",
      "trust_signals": [
        { "check": "OCR match", "result": "pass" },
        { "check": "Issuer signature", "result": "pass" },
        { "check": "Fraud flags", "result": "fail" },
        { "check": "Blockchain record", "result": "pass" }
      ],
      "field_comparison": {
        "cgpa": {
          "submitted": "8.70",
          "stored": "6.70",
          "match": false,
          "status": "CHANGED",
          "severity": "CRITICAL"
        }
      }
    }
    ```

---

## 4. Student Resume Endpoints

### 4.1 Analyze CV
*   **Endpoint**: `POST /student/analyze-resume`
*   **Auth**: Required (Bearer Token, Role = `student`)
*   **Content-Type**: `multipart/form-data`
*   **Parameters**:
    *   `file` (file bytes)
*   **Response**:
    ```json
    {
      "id": "analysis-uuid-5678",
      "skills": ["Python", "FastAPI", "React"],
      "github_analysis": {
        "projects_found": 3,
        "languages": ["Python", "TypeScript"]
      },
      "ai_summary": "Candidate displays strong proficiency in web engineering..."
    }
    ```
