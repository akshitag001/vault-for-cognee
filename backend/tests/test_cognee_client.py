import pytest
from unittest.mock import AsyncMock, patch
from app.cognee_client import connect, remember_normal, recall_normal, forget_normal, improve_normal
import app.cognee_client as cognee_client

pytestmark = pytest.mark.asyncio

@patch("app.cognee_client.cognee")
async def test_connect(mock_cognee):
    mock_cognee.serve = AsyncMock()
    
    cognee_client._is_connected = False
    
    await connect()
    mock_cognee.serve.assert_called_once()
    assert cognee_client._is_connected is True
    
    # Calling again should be a no-op
    await connect()
    mock_cognee.serve.assert_called_once()

@patch("app.cognee_client.cognee")
async def test_remember_normal(mock_cognee):
    mock_cognee.remember = AsyncMock()
    
    await remember_normal("some content", "test_dataset")
    mock_cognee.remember.assert_called_once_with("some content", dataset_name="test_dataset")
    
    mock_cognee.remember.side_effect = Exception("API error")
    with pytest.raises(Exception, match="API error"):
        await remember_normal("fail content", "fail_dataset")

@patch("app.cognee_client.cognee")
async def test_recall_normal(mock_cognee):
    mock_cognee.recall = AsyncMock(return_value=[
        "string result",
        {"content": "dict result"},
        {"text": "another dict"}
    ])
    
    results = await recall_normal("my query", "my_dataset")
    mock_cognee.recall.assert_called_once_with(query_text="my query", dataset_name="my_dataset")
    
    assert len(results) == 3
    assert results[0] == {"content": "string result", "source": "cognee"}
    assert results[1] == {"content": "dict result", "source": "cognee"}
    assert results[2] == {"content": "another dict", "source": "cognee"}

@patch("app.cognee_client.cognee")
async def test_forget_normal(mock_cognee):
    mock_cognee.forget = AsyncMock()
    
    await forget_normal("my_dataset")
    mock_cognee.forget.assert_called_once_with(dataset="my_dataset")

@patch("app.cognee_client.cognee")
async def test_improve_normal(mock_cognee):
    mock_cognee.improve = AsyncMock()
    
    await improve_normal()
    mock_cognee.improve.assert_called_once()
