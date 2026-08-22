"""
Test suite for health check endpoints.
Verifies GET / root health response format and GET /api/v1/health status.
"""

from fastapi.testclient import TestClient


def test_root_health_endpoint(client: TestClient):
    """
    Test GET / endpoint returns required JSON response format:
    {
        "project": "CertiTrust AI",
        "status": "running"
    }
    """
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data == {
        "project": "CertiTrust AI",
        "status": "running",
    }


def test_api_v1_health_endpoint(client: TestClient):
    """
    Test GET /api/v1/health endpoint under versioned API router.
    """
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["project"] == "CertiTrust AI"
    assert data["status"] == "running"
