"""
CertiTrust AI - Pydantic Request & Response Schemas for Information Extraction Module.
"""

from typing import Optional, List
from pydantic import BaseModel, Field


class ExtractionRequest(BaseModel):
    """
    Input request schema accepting raw OCR text for entity extraction.
    """

    text: str = Field(..., example="This is to certify that JANE DOE completed Bachelor of Technology in Computer Science from Stanford University on 2026-05-10. Cert ID: CT-998241. CGPA: 3.8/4.0")


class ExtractionResponse(BaseModel):
    """
    Output response schema containing extracted certificate metadata fields.
    """

    student_name: Optional[str] = Field(None, example="Jane Doe")
    university: Optional[str] = Field(None, example="Stanford University")
    degree: Optional[str] = Field(None, example="Bachelor of Technology")
    course: Optional[str] = Field(None, example="Computer Science")
    certificate_number: Optional[str] = Field(None, example="CT-998241")
    issue_date: Optional[str] = Field(None, example="2026-05-10")
    organization: Optional[str] = Field(None, example="Stanford University")
    cgpa: Optional[str] = Field(None, example="3.8/4.0")
    skills: List[str] = Field(default_factory=list, example=["Computer Science", "Artificial Intelligence"])
