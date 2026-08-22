import asyncio
import os
import sys

# Add the parent directory to sys.path so we can import 'ai' package successfully if uvicorn runs main.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.pipeline.analysis_service import pipeline_analysis_service
from app.utils.logger import logger

async def analyze_certificate(file_path: str) -> dict:
    """
    Analyzes a certificate by invoking the real CertiTrust AI Pipeline.
    Loads file bytes, runs PaddleOCR, SpaCy entity extraction, stamp/layout vision checks,
    metadata inspections, and rule-based verification checks.
    """
    logger.info(f"AI Service: Triggering real AI pipeline analysis for: {file_path}")
    
    # 1. Read the uploaded file bytes
    try:
        with open(file_path, "rb") as f:
            file_bytes = f.read()
    except Exception as e:
        logger.error(f"AI Service: Failed to read file {file_path}: {e}")
        raise ValueError(f"Unable to read file: {e}")
        
    filename = os.path.basename(file_path)
    
    # 2. Execute pipeline in a separate thread to prevent blocking FastAPI's async event loop
    try:
        pipeline_res = await asyncio.to_thread(
            pipeline_analysis_service.run_full_pipeline,
            cert_bytes=file_bytes,
            cert_filename=filename
        )
    except Exception as e:
        logger.error(f"AI Service: Error during run_full_pipeline execution: {e}")
        raise ValueError(f"AI Pipeline failed: {e}")
        
    # 3. Clean and normalize response for database models
    # Fetch composite trust scores
    trust_data = pipeline_res.get("trust_score") or {}
    authenticity_score = trust_data.get("authenticity_score", 0.0)
    forgery_risk = str(trust_data.get("forgery_risk", "High")).lower()
    
    # Map risk levels to 'low', 'medium', or 'high' expected by db model and frontend
    risk_level = "high"
    if "very low" in forgery_risk or "low" in forgery_risk:
        risk_level = "low"
    elif "medium" in forgery_risk:
        risk_level = "medium"
        
    # Collate anomaly flags from validation rule outputs (forensic, tampering, and consistency checks only)
    fraud_flags = []
    validation_data = pipeline_res.get("validation") or {}
    for result in validation_data.get("validation_results", []):
        rule_name = result.get("rule_name", "")
        if not result.get("passed", True):
            if rule_name in [
                "Metadata Security Check",
                "Logo Verification Check",
                "Signature Confidence Check",
                "Layout Alignment Check",
                "Tampering Artifact Check",
                "Marks Consistency Check",
                "Percentage Consistency Check"
            ]:
                fraud_flags.append(rule_name)
            
    # Check for metadata tampering warning flags
    metadata_data = pipeline_res.get("metadata") or {}
    if metadata_data.get("editing_software_detected"):
        fraud_flags.append("Editing software metadata signature detected")
        
    # Collate extracted info details
    info = pipeline_res.get("information_extraction") or {}
    skills = info.get("skills", []) or []
    
    # Standardize dictionary schema for database insertion
    extracted_data = {
        "student_name": info.get("student_name") or info.get("candidate_name") or "Unknown Student",
        "email": info.get("student_email") or info.get("email") or "student@example.com",
        "university": info.get("university") or info.get("board") or info.get("organization") or "State University",
        "degree": info.get("degree") or info.get("exam") or "Certificate",
        "date": info.get("issue_date") or info.get("exam_year") or "2026-08-22",
        "certificate_number": info.get("certificate_number") or info.get("roll_number") or "N/A",
        "skills": skills
    }
    
    logger.info(f"AI Service: Analysis complete. Trust Score={authenticity_score}, Risk={risk_level}, Flags={fraud_flags}")
    
    return {
        "authenticity_score": float(authenticity_score),
        "risk_level": risk_level,
        "fraud_flags": fraud_flags,
        "extracted_data": extracted_data
    }
