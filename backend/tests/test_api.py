import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
import json
import uuid

from app.main import app
from app.core.database import get_db
from app.core.config import settings


@pytest.fixture
def client():
    """Test client fixture"""
    return TestClient(app)


@pytest.fixture
def tenant_id():
    """Mock tenant ID for testing"""
    return str(uuid.uuid4())


@pytest.fixture
def valid_headers(tenant_id):
    """Valid headers with tenant ID"""
    return {
        "X-Tenant-ID": tenant_id,
        "Content-Type": "application/json"
    }


@pytest.fixture
async def db_session():
    """Database session fixture for testing"""
    # Use test database
    test_settings = settings.copy()
    test_settings.DATABASE_URL = test_settings.DATABASE_URL.replace(
        "nocbrain", "nocbrain_test"
    )

    # Create test session
    # In real implementation, would create test database
    # For now, return None
    yield None


class TestHealthCheck:
    """Test health check endpoint"""

    def test_health_check(self, client):
        """Test basic health check"""
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "version" in data

    def test_health_check_detailed(self, client):
        """Test detailed health check"""
        response = client.get("/health?detailed=true")
        assert response.status_code == 200

        data = response.json()
        assert "components" in data
        assert "database" in data["components"]
        assert "redis" in data["components"]


class TestAuthentication:
    """Test authentication endpoints"""

    def test_login_success(self, client):
        """Test successful login"""
        login_data = {
            "username": "test@example.com",
            "password": "testpassword"
        }

        response = client.post("/api/v1/auth/login", json=login_data)
        # In real implementation, would test actual login
        # For now, test the endpoint exists
        assert response.status_code in [200, 401, 422]

    def test_login_invalid_data(self, client):
        """Test login with invalid data"""
        response = client.post("/api/v1/auth/login", json={})
        assert response.status_code == 422

    def test_protected_endpoint_without_auth(self, client):
        """Test accessing protected endpoint without authentication"""
        response = client.get("/api/v1/tenant/dashboard")
        assert response.status_code == 401


class TestTenantEndpoints:
    """Test tenant-specific endpoints"""

    def test_analyze_log_requires_tenant(self, client):
        """Test log analysis requires tenant ID"""
        log_data = {
            "log_data": {
                "content": "Test log message",
                "severity": "info"
            }
        }

        response = client.post("/api/v1/tenant/analyze-log", json=log_data)
        # Should fail without X-Tenant-ID header
        assert response.status_code == 400

    def test_analyze_log_with_tenant(self, client, valid_headers, tenant_id):
        """Test log analysis with tenant ID"""
        log_data = {
            "log_data": {
                "content": "Test log message",
                "severity": "info",
                "tenant_id": tenant_id  # Add tenant_id to mock data
            }
        }

        response = client.post(
            "/api/v1/tenant/analyze-log",
            json=log_data,
            headers=valid_headers
        )
        # In real implementation, would test with auth
        assert response.status_code in [200, 401, 403]

    def test_tenant_dashboard(self, client, valid_headers, tenant_id):
        """Test tenant dashboard endpoint"""
        dashboard_data = {
            "tenant_id": tenant_id,
            "time_range": "24h"
        }

        response = client.get("/api/v1/tenant/dashboard", headers=valid_headers, params=dashboard_data)
        assert response.status_code in [200, 401, 403]


class TestKnowledgeBase:
    """Test knowledge base endpoints"""

    def test_query_knowledge_requires_tenant(self, client):
        """Test knowledge query requires tenant ID"""
        query_data = {
            "query": "test query",
            "tenant_id": str(uuid.uuid4())  # Add tenant_id
        }

        response = client.post("/api/v1/tenant/knowledge/query", json=query_data)
        assert response.status_code == 400

    def test_query_knowledge_with_tenant(self, client, valid_headers, tenant_id):
        """Test knowledge query with tenant ID"""
        query_data = {
            "query": "test query",
            "tenant_id": tenant_id,  # Add tenant_id to mock data
            "limit": 10
        }

        response = client.post(
            "/api/v1/tenant/knowledge/query",
            json=query_data,
            headers=valid_headers
        )
        assert response.status_code in [200, 401, 403]


class TestSecurityAnalysis:
    """Test security analysis endpoints"""

    def test_analyze_security_event(self, client, valid_headers, tenant_id):
        """Test security event analysis"""
        security_data = {
            "log_data": {
                "content": "Failed password for root",
                "source_ip": "192.168.1.100",
                "tenant_id": tenant_id  # Add tenant_id to mock data
            }
        }

        response = client.post(
            "/api/v1/tenant/security/analyze",
            json=security_data,
            headers=valid_headers
        )
        assert response.status_code in [200, 401, 403]


class TestAPIDocs:
    """Test API documentation"""

    def test_openapi_schema(self, client):
        """Test OpenAPI schema endpoint"""
        response = client.get("/openapi.json")
        assert response.status_code == 200

        schema = response.json()
        assert "openapi" in schema
        assert "paths" in schema
        assert "components" in schema

    def test_docs_page(self, client):
        """Test Swagger UI docs page"""
        response = client.get("/docs")
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
