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

from fastapi import APIRouter
api_router = APIRouter(prefix="/api")
api_router.include_router(auth.router)
api_router.include_router(upload.router)
api_router.include_router(analyze.router)
api_router.include_router(verify.router)
api_router.include_router(employer.router)
api_router.include_router(student.router)
api_router.include_router(institution.router)
app.include_router(api_router)

import logging
logger = logging.getLogger("certitrust")

@app.on_event("startup")
async def startup_event():
    import tempfile
    upload_dir = os.getenv("UPLOAD_DIR", os.path.join(tempfile.gettempdir(), "uploads"))
    try:
        os.makedirs(upload_dir, exist_ok=True)
    except OSError:
        upload_dir = os.path.join(tempfile.gettempdir(), "uploads")
        os.makedirs(upload_dir, exist_ok=True)
    try:
        await connect_db()
    except Exception as err:
        logger.warning(f"Database connection startup notice: {err}")

@app.on_event("shutdown")
async def shutdown_event():
    await close_db()

@app.get("/health")
@api_router.get("/health")
async def health_check():
    from database import connect_db, check_db_connection, db_client
    if db_client.db is None or db_client.is_mock:
        try:
            await connect_db()
        except Exception:
            pass
    db_status = await check_db_connection()
    return {
        "status": "healthy",
        "service": "CertiTrust AI API",
        "version": "1.0.0",
        "database": db_status
    }

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
