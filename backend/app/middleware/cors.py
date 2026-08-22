"""
CORS Middleware configuration module.
Configures Cross-Origin Resource Sharing rules for the FastAPI application.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings


def setup_cors(app: FastAPI) -> None:
    """
    Attaches CORSMiddleware to the FastAPI application.
    Allows frontend clients to interact with the backend API securely.
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
