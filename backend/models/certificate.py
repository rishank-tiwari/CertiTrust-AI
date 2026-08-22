from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from .verification import VerificationResult

class CertificateCreate(BaseModel):
    student_name: str
    university: str
    degree: str
    certificate_number: str

class CertificateResponse(BaseModel):
    id: str
    student_name: str
    university: str
    degree: str
    certificate_number: str
    file_hash: Optional[str] = None
    status: str = 'pending'
    uploaded_by: str
    created_at: datetime

class CertificateDetail(CertificateResponse):
    verification: Optional[VerificationResult] = None

class AnalyzeRequest(BaseModel):
    certificate_id: str
