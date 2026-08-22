"""
API Version 1 Router Aggregator.
Combines feature routers (health, upload, extract, metadata, logo, cv_analysis, validation, trust_score, report, analyze, verification, blockchain) under the /api/v1 prefix.
"""

from fastapi import APIRouter
from app.routes import health, upload, extract, metadata, logo, cv_analysis, validation, trust_score, report, analyze, verification, blockchain, issuer, employer, resume_intelligence

api_v1_router = APIRouter()

# Include feature sub-routers
api_v1_router.include_router(health.router)
api_v1_router.include_router(upload.router)
api_v1_router.include_router(extract.router)
api_v1_router.include_router(metadata.router)
api_v1_router.include_router(logo.router)
api_v1_router.include_router(cv_analysis.router)
api_v1_router.include_router(validation.router)
api_v1_router.include_router(trust_score.router)
api_v1_router.include_router(report.router)
api_v1_router.include_router(analyze.router)
api_v1_router.include_router(verification.router)
api_v1_router.include_router(blockchain.router)
api_v1_router.include_router(issuer.router)
api_v1_router.include_router(employer.router)
api_v1_router.include_router(resume_intelligence.router)
