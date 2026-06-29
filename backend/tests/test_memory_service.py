import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from app.memory_service import MemoryService
from app.vault_store import VaultStore
from app.models import IngestResult, QueryResult, ClassificationResult

pytestmark = pytest.mark.asyncio

@pytest.fixture
def mock_vault_store():
    store = MagicMock(spec=VaultStore)
    store.put = MagicMock()
    store.search = MagicMock(return_value=[{"doc_id": "v1", "content": "secret text"}])
    store.forget_dataset = MagicMock()
    return store

@pytest.fixture
def memory_service(mock_vault_store):
    return MemoryService(vault_store=mock_vault_store)

@patch("app.memory_service.cognee_client")
@patch("app.memory_service.classify_chunk")
async def test_ingest_sensitive_routes_to_vault(mock_classify, mock_cognee_client, memory_service, mock_vault_store):
    mock_cognee_client.remember_normal = AsyncMock()
    mock_classify.return_value = ClassificationResult(
        is_sensitive=True,
        matched_patterns=["keyword"],
        confidence=0.33
    )
    
    res = await memory_service.ingest("This is a secret", "test_data", "doc1")
    
    assert res.routed_to == "vault"
    mock_vault_store.put.assert_called_once_with("test_data", "doc1", "This is a secret")
    mock_cognee_client.remember_normal.assert_not_called()

@patch("app.memory_service.cognee_client")
@patch("app.memory_service.classify_chunk")
async def test_ingest_normal_routes_to_cognee(mock_classify, mock_cognee_client, memory_service, mock_vault_store):
    mock_cognee_client.remember_normal = AsyncMock()
    mock_classify.return_value = ClassificationResult(
        is_sensitive=False,
        matched_patterns=[],
        confidence=0.0
    )
    
    res = await memory_service.ingest("Just a normal day", "test_data", "doc2")
    
    assert res.routed_to == "cognee"
    mock_cognee_client.remember_normal.assert_called_once_with("Just a normal day", "test_data")
    mock_vault_store.put.assert_not_called()

@patch("app.memory_service.cognee_client")
async def test_query_merges_results(mock_cognee_client, memory_service, mock_vault_store):
    mock_cognee_client.recall_normal = AsyncMock(return_value=[{"content": "graph text", "source": "cognee"}])
    
    res = await memory_service.query("search query", "test_data")
    
    mock_vault_store.search.assert_called_once_with("test_data", "search query")
    mock_cognee_client.recall_normal.assert_called_once_with("search query", "test_data")
    
    assert res.total_count == 2
    assert len(res.vault_hits) == 1
    assert res.vault_hits[0]["source"] == "vault"
    assert res.vault_hits[0]["content"] == "secret text"
    
    assert len(res.cognee_hits) == 1
    assert res.cognee_hits[0]["source"] == "cognee"
    assert res.cognee_hits[0]["content"] == "graph text"

@patch("app.memory_service.cognee_client")
async def test_forget_calls_both_paths(mock_cognee_client, memory_service, mock_vault_store):
    mock_cognee_client.forget_normal = AsyncMock()
    
    res = await memory_service.forget("test_data")
    
    assert res.success is True
    mock_vault_store.forget_dataset.assert_called_once_with("test_data")
    mock_cognee_client.forget_normal.assert_called_once_with("test_data")
