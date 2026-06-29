import os
import logging
from typing import List, Dict, Any, Optional

try:
    import cognee
except ImportError:
    # Handle the case where cognee isn't installed during testing or build
    import sys
    from unittest.mock import MagicMock
    cognee = MagicMock()
    sys.modules["cognee"] = cognee

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

_is_connected = False

async def connect() -> None:
    global _is_connected
    if _is_connected:
        return
        
    try:
        # Load environment via dotenv is usually done at app startup
        # cognee.serve() will pick up COGNEE_SERVICE_URL and COGNEE_API_KEY
        await cognee.serve()
        _is_connected = True
        logger.info("Connected to Cognee Cloud.")
    except Exception as e:
        logger.error(f"Failed to connect to Cognee Cloud: {e}")
        raise

async def remember_normal(content: str, dataset_name: str) -> None:
    try:
        await cognee.remember(content, dataset_name=dataset_name)
    except Exception as e:
        logger.error(f"Failed to remember content in dataset '{dataset_name}': {e}")
        raise

async def recall_normal(query: str, dataset_name: Optional[str] = None) -> List[Dict[str, Any]]:
    try:
        kwargs = {"query_text": query}
        if dataset_name:
            kwargs["dataset_name"] = dataset_name
            
        results = await cognee.recall(**kwargs)
        
        normalized = []
        # Normalizing the return shape into a list of dicts: {content, source: "cognee"}
        if results is None:
            return normalized
            
        for res in results:
            content = ""
            if isinstance(res, str):
                content = res
            elif isinstance(res, dict):
                content = res.get("content") or res.get("text") or str(res)
            elif hasattr(res, "content"):
                content = res.content
            elif hasattr(res, "text"):
                content = res.text
            else:
                content = str(res)
                
            normalized.append({
                "content": content,
                "source": "cognee"
            })
        return normalized
    except Exception as e:
        logger.error(f"Failed to recall query '{query}': {e}")
        raise

async def forget_normal(dataset_name: str) -> None:
    try:
        await cognee.forget(dataset=dataset_name)
    except Exception as e:
        logger.error(f"Failed to forget dataset '{dataset_name}': {e}")
        raise

async def improve_normal() -> None:
    try:
        await cognee.improve()
    except Exception as e:
        logger.error(f"Failed to improve cognee graph: {e}")
        raise
