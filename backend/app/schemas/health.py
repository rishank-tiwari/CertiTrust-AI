"""
Health Check Response Schema.
"""

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """
    Schema for health status endpoint.
    """

    project: str = Field(..., example="CertiTrust AI")
    status: str = Field(..., example="running")
