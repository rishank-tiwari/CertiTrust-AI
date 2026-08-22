"""
Pytest Fixture Configuration.
Sets up FastAPI TestClient and async client fixtures for unit and integration tests.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture(scope="module")
def client() -> TestClient:
    """
    Returns a synchronous TestClient instance for testing FastAPI endpoints.
    """
    with TestClient(app) as test_client:
        yield test_client
