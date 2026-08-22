"""
SQLAlchemy Document Database Model Placeholder.
Defines entity table schema for ingested certificates and verification results.
"""

from datetime import datetime
from sqlalchemy import Column, String, DateTime, Float, JSON
from app.database.session import Base


class DocumentModel(Base):
    """
    Document table schema placeholder.
    """

    __tablename__ = "documents"

    id = Column(String, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    mime_type = Column(String, nullable=False)
    status = Column(String, default="PENDING")
    trust_score = Column(Float, nullable=True)
    extracted_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
