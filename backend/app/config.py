"""
CertiTrust AI - Application Configuration Module.
Loads environment variables using python-dotenv and provides typed setting objects.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file using python-dotenv
BASE_DIR = Path(__file__).resolve().parent.parent
env_path = BASE_DIR / ".env"
load_dotenv(dotenv_path=env_path)


class Settings:
    """
    Central Settings Manager for CertiTrust AI Environment.
    """

    def __init__(self):
        # API Versioning & Server Settings
        self.PROJECT_NAME: str = os.getenv("PROJECT_NAME", "CertiTrust AI")
        self.API_VERSION: str = os.getenv("API_VERSION", "v1")
        self.ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
        self.DEBUG: bool = os.getenv("DEBUG", "True").lower() in ("true", "1", "t")

        self.HOST: str = os.getenv("HOST", "0.0.0.0")
        self.PORT: int = int(os.getenv("PORT", "8000"))

        # Database Configuration
        self.MONGODB_URI: str = os.getenv("MONGODB_URI") or os.getenv("MONGODB_URL") or "mongodb://localhost:27017/certitrust_ai"

        # Security & Authentication
        self.JWT_SECRET: str = os.getenv("JWT_SECRET") or os.getenv("JWT_SECRET_KEY") or "certitrust_ai_jwt_super_secret_key_change_in_production"
        self.JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
        self.ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

        # Upload & File Storage Config
        self.UPLOAD_FOLDER: Path = BASE_DIR / os.getenv("UPLOAD_FOLDER", "uploads")
        self.UPLOAD_DIR: Path = self.UPLOAD_FOLDER
        self.MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", "26214400"))  # 25 MB default

        # CORS Configuration
        allowed_origins_raw = os.getenv("ALLOWED_ORIGINS", '["http://localhost:3000","http://127.0.0.1:3000"]')
        try:
            import json
            self.ALLOWED_ORIGINS = json.loads(allowed_origins_raw)
        except Exception:
            self.ALLOWED_ORIGINS = [i.strip() for i in allowed_origins_raw.split(",") if i.strip()]

        # System Directories to Validate
        self.REQUIRED_DIRS = [
            self.UPLOAD_FOLDER,
            BASE_DIR / "templates",
            BASE_DIR / "sample_documents",
        ]


# Instantiate global settings object
settings = Settings()
