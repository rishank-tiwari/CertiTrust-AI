from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import connect_db, close_db
from routes import auth, upload, analyze, verify, employer, student, institution
import os

from config import get_settings
import json

app = FastAPI(
    title="CertiTrust AI",
    description="AI-Powered Verifiable Academic & Skill Credential Ledger API",
    version="1.0.0"
)

settings = get_settings()
origins = ["http://localhost:3000", "http://localhost:5173", "http://localhost:5174", "http://localhost:5175"]
if settings.ALLOWED_ORIGINS:
    try:
        if settings.ALLOWED_ORIGINS.strip().startswith("["):
            origins = json.loads(settings.ALLOWED_ORIGINS)
        else:
            origins = [o.strip() for o in settings.ALLOWED_ORIGINS.split(",") if o.strip()]
    except Exception:
        pass

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(upload.router)
app.include_router(analyze.router)
app.include_router(verify.router)
app.include_router(employer.router)
app.include_router(student.router)
app.include_router(institution.router)

@app.on_event("startup")
async def startup_event():
    os.makedirs("uploads", exist_ok=True)
    await connect_db()

@app.on_event("shutdown")
async def shutdown_event():
    await close_db()

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "CertiTrust AI API", "version": "1.0.0"}

@app.get("/")
async def root():
    return {
        "message": "Welcome to CertiTrust AI API",
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "auth": "/auth",
            "upload": "/upload",
            "analyze": "/analyze",
            "verify": "/verify/{certificate_id}"
        }
    }
