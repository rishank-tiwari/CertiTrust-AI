"""
Global Exception Handler Middleware.
Catches unhandled exceptions gracefully and returns standard JSON response formatting.
"""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from app.utils.logger import logger


def setup_exception_handlers(app: FastAPI) -> None:
    """
    Registers global exception handlers for the FastAPI app.
    """

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled Error on {request.method} {request.url.path}: {str(exc)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": True,
                "message": "An internal server error occurred.",
                "detail": str(exc) if app.debug else None,
            },
        )
