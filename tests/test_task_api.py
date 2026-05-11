"""
Task API Tests

Unit tests for task API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


class TestTaskAPI:
    """Task API tests"""
    
    def test_root_endpoint(self):
        """Test root endpoint redirects to web UI"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/web/"
    
    def test_health_endpoint(self):
        """Test health endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    # TODO: Add more tests for task endpoints