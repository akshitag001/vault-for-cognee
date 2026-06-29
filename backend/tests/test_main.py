import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from app.main import app
from app.models import IngestResult, QueryResult, ForgetResult, ImproveResult

client = TestClient(app)

@patch("app.main.memory_service")
def test_ingest_endpoint(mock_memory_service):
    mock_memory_service.ingest = AsyncMock(return_value=IngestResult(
        doc_id="test-doc-123",
        routed_to="vault",
        matched_patterns=["secret"]
    ))
    
    response = client.post("/ingest", json={"content": "super secret", "dataset_name": "test_data"})
    assert response.status_code == 200
    data = response.json()
    assert data["doc_id"] == "test-doc-123"
    assert data["routed_to"] == "vault"
    
    mock_memory_service.ingest.assert_called_once_with(content="super secret", dataset_name="test_data")

@patch("app.main.memory_service")
def test_query_endpoint(mock_memory_service):
    mock_memory_service.query = AsyncMock(return_value=QueryResult(
        vault_hits=[{"doc_id": "v1", "source": "vault"}],
        cognee_hits=[],
        total_count=1
    ))
    
    response = client.post("/query", json={"query": "find secret", "dataset_name": "test_data"})
    assert response.status_code == 200
    data = response.json()
    assert data["total_count"] == 1
    assert data["vault_hits"][0]["source"] == "vault"
    
    mock_memory_service.query.assert_called_once_with(query_text="find secret", dataset_name="test_data")

@patch("app.main.memory_service")
def test_forget_endpoint(mock_memory_service):
    mock_memory_service.forget = AsyncMock(return_value=ForgetResult(
        success=True,
        message="Forgotten."
    ))
    
    response = client.post("/forget", json={"dataset_name": "test_data"})
    assert response.status_code == 200
    assert response.json()["success"] is True
    
    mock_memory_service.forget.assert_called_once_with(dataset_name="test_data")

@patch("app.main.memory_service")
def test_improve_endpoint(mock_memory_service):
    mock_memory_service.improve = AsyncMock(return_value=ImproveResult(
        audit_summary={"total_sensitive_queries": 5}
    ))
    
    response = client.post("/improve", json={"dataset_name": "test_data"})
    assert response.status_code == 200
    assert response.json()["audit_summary"]["total_sensitive_queries"] == 5
    
    mock_memory_service.improve.assert_called_once_with(dataset_name="test_data")

@patch("app.main.access_log")
def test_access_log_endpoint(mock_access_log):
    mock_access_log.get_access_log.return_value = [{"id": 1, "query_hash": "abc"}]
    
    response = client.get("/access-log/test_data")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == 1
    
    mock_access_log.get_access_log.assert_called_once_with("test_data")

@patch("app.main.cognee_client")
def test_health_endpoint(mock_cognee_client):
    mock_cognee_client._is_connected = True
    
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["cognee_connected"] is True
