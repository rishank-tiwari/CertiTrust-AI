# CertiTrust AI

CertiTrust AI is a secure, AI-powered system designed to verify academic credentials, student records, and skills. It bridges the trust gap between credential issuers, students, and employers using an in-process document intelligence pipeline and automated ledger audits.

---

## 1. Project Overview
CertiTrust AI automates the verification of certificates, diplomas, and marksheets. By pairing optical character recognition (OCR) with semantic field-matching and tamper audits, the system isolates anomalies and GPA inflation in real time, preventing credentials fraud.

## 2. Problem Statement
Manual academic background verification is slow, expensive, and error-prone. Students can easily inflate GPA scores or alter certificates in PDF editors, leading to false hires. Typical blockchain verification fails if the uploaded scanned copies differ from the original file hash, even when the content is completely genuine.

## 3. Solution
CertiTrust AI solves this by:
*   Establishing a **Source of Truth** registry directly populated by academic institutions.
*   Evaluating scans using content normalizers, matching credentials by name or roll number even if the file format or hash changes.
*   Generating a structured mismatch audit that detects exactly which parameters (like CGPA) were modified.

## 4. Key Features
*   **AI Credential Verification**: Real-time document parsing and layout classification.
*   **Issuer Source of Truth**: Secure portal for universities to register student credentials.
*   **Employer Verification**: Automated document checks mapping OCR output to registered records.
*   **Fraud Detection**: Isolated anomaly analysis flag alerts on altered values.
*   **SHA-256 Document Hashing**: Verification check on exact matching documents.
*   **Blockchain Verification**: Immutable proof checks on verification hashes.
*   **Resume Intelligence**: Skill matching and automated capability reports.
*   **Skill Passport Verification**: Dynamic QR share cards mapping validated courses.
*   **GitHub Project Analysis**: Scrapes and analyzes repo structures to confirm coding skills.
*   **AI Resume Summary**: Automatically summarizes the candidate's professional profile.

## 5. System Architecture
```
[User Browser]
       │ (HTTPS Requests)
       ▼
[Frontend: React/Vite App]
       │ (Rest HTTP: VITE_API_URL)
       ▼
[Backend: FastAPI Service] <───► [AI Pipeline: OCR, spaCy, Classifiers]
       │
       ▼ (Connection String)
[MongoDB Atlas Cloud Cluster]
```

## 6. Technology Stack
*   **Frontend**: React, Vite, TypeScript, Vanilla CSS.
*   **Backend**: FastAPI, Python.
*   **AI**: PaddleOCR (image text extraction), spaCy (NLP parsing), document layout classifiers.
*   **Database**: MongoDB Atlas.

## 7. Installation Guide

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Backend & AI Pipeline
```bash
cd backend
python -m venv venv
# Activate virtualenv (e.g. source venv/bin/activate or venv\Scripts\activate)
pip install -r requirements.txt
uvicorn main:app --reload
```

## 8. Environment Setup
Rename `.env.example` in both directories to `.env` and fill in:
*   `VITE_API_URL` (Frontend)
*   `MONGODB_URL`, `JWT_SECRET_KEY`, `ALLOWED_ORIGINS` (Backend)

## 9. API Documentation
Detailed descriptions of the authentication and upload routes can be reviewed in [docs/api-documentation.md](file:///E:/hackathon%20f/docs/api-documentation.md).

## 10. Deployment Guide
Review step-by-step instructions for hosting on Vercel, Railway, and configuring network filters in [docs/deployment-guide.md](file:///E:/hackathon%20f/docs/deployment-guide.md).
