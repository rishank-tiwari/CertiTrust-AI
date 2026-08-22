# CertiTrust AI - Deployment Guide

This document lists environment specifications and production deployment directives for deploying CertiTrust AI.

---

## 1. MongoDB Atlas Setup
1. Create a MongoDB Atlas cluster (M0 free tier).
2. Set network access list to allow connections from `0.0.0.0/0` (allowing serverless access).
3. Retrieve database connection driver string.

---

## 2. Railway Backend Deployment
Deploy the `backend/` application:
*   **Platform**: [Railway](https://railway.app)
*   **Build command**: `pip install -r requirements.txt`
*   **Start command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
*   **Memory Specification**: Minimum **2GB RAM** (CPU Starter Instance) to support model weight loading.
*   **Required Variables**:
    *   `MONGODB_URL`: MongoDB cluster URI.
    *   `DATABASE_NAME`: database catalog name (e.g. `certitrust`).
    *   `JWT_SECRET_KEY`: Bearer signature key.
    *   `JWT_ALGORITHM`: `HS256`
    *   `JWT_EXPIRY_HOURS`: `24`
    *   `ALLOWED_ORIGINS`: JSON array listing hosted frontend URLs (e.g. `["https://certitrust-nexora.vercel.app"]`).

---

## 3. Vercel Frontend Deployment
Deploy the `frontend/` application:
*   **Platform**: [Vercel](https://vercel.com)
*   **Framework Preset**: `Vite`
*   **Build Command**: `tsc -b && vite build`
*   **Output Directory**: `dist`
*   **Required Variables**:
    *   `VITE_API_URL`: Address of Railway backend deployment endpoint (e.g., `https://certitrust-api.up.railway.app`).
