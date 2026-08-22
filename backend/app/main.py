"""
CertiTrust AI - Main FastAPI Application Entry Point.
Initializes middleware, routing, CORS, exception handling, environment startup validation,
and startup banner logging using Loguru.
"""

import sys
import os
os.environ["FLAGS_use_onednn"] = "0"
os.environ["FLAGS_use_mkldnn"] = "0"
os.environ["FLAGS_enable_pir_api"] = "0"

from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.config import settings
from app.middleware.cors import setup_cors
from app.middleware.exception_handler import setup_exception_handlers
from app.routes.api_v1 import api_v1_router
from app.routes.health import router as root_health_router
from app.utils.logger import logger


def validate_environment_and_directories():
    """
    Startup Validation function:
    1. Checks if environment variables are loaded.
    2. Ensures upload folder and required directories exist (creates if missing).
    """
    logger.info("Performing startup environment & directory validation...")

    # 1. Environment Variables Validation
    required_env_vars = {
        "MONGODB_URI": settings.MONGODB_URI,
        "JWT_SECRET": settings.JWT_SECRET,
        "UPLOAD_FOLDER": settings.UPLOAD_FOLDER,
        "MAX_FILE_SIZE": settings.MAX_FILE_SIZE,
        "API_VERSION": settings.API_VERSION,
    }

    for key, value in required_env_vars.items():
        if not value:
            logger.error(f"Startup Validation Error: Environment variable '{key}' is missing!")
            raise ValueError(f"Missing required environment variable: {key}")
        logger.info(f"Env Check [{key}]: Loaded")

    # 2. Directories Validation & Auto-Creation
    for directory in settings.REQUIRED_DIRS:
        if not directory.exists():
            logger.warning(f"Directory '{directory}' does not exist. Creating...")
            directory.mkdir(parents=True, exist_ok=True)
        logger.info(f"Directory Check [{directory.name}]: Ready")

    logger.info("Startup validation completed successfully.")


def print_startup_banner():
    """
    Prints the required backend startup banner.
    """
    banner = f"""
==================================
CertiTrust AI Backend Started
FastAPI Ready
AI Modules Ready
Version: {settings.API_VERSION}
==================================
"""
    print(banner)
    logger.info(f"CertiTrust AI Backend initialized with API version: {settings.API_VERSION}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI Lifespan Context Manager.
    Handles startup validation, banner display, and shutdown operations.
    """
    # Run startup validation
    validate_environment_and_directories()

    # Print startup banner
    print_startup_banner()

    yield

    # Shutdown tasks
    logger.info(f"Shutting down {settings.PROJECT_NAME} application.")


# Instantiate FastAPI Application
app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="Production-grade FastAPI Backend Architecture for CertiTrust AI Verification System",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Configure CORS Middleware
setup_cors(app)

# Configure Global Exception Handler Middleware
setup_exception_handlers(app)

# Register Root Health Endpoint (GET /)
app.include_router(root_health_router)

# Register active authenticated routes matching frontend API client calls
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from routes import auth, upload, analyze, verify, employer, student, institution
app.include_router(auth.router)
app.include_router(upload.router)
app.include_router(analyze.router)
app.include_router(verify.router)
app.include_router(employer.router)
app.include_router(student.router)
app.include_router(institution.router)

# Register API v1 Versioned Router (/api/v1) as fallback
app.include_router(api_v1_router, prefix=f"/api/{settings.API_VERSION}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
