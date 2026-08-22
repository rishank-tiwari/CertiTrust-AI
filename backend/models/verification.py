from datetime import datetime
from typing import List, Literal, Optional, Dict, Any
from pydantic import BaseModel

class ExtractedData(BaseModel):
    student_name: Optional[str] = None
    university: Optional[str] = None
    degree: Optional[str] = None
    date: Optional[str] = None
    certificate_number: Optional[str] = None

class VerificationResult(BaseModel):
    id: str
    certificate_id: str
    authenticity_score: float
    risk_level: Literal['low', 'medium', 'high']
    fraud_flags: List[str]
    extracted_data: ExtractedData
    certificate_hash: str
    blockchain_tx_hash: str
    verified_at: datetime

class VerificationResponse(BaseModel):
    certificate: Dict[str, Any]
    verification: Dict[str, Any]
    blockchain_proof: Dict[str, Any]
    status: str
