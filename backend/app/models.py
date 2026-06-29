from pydantic import BaseModel
from typing import List, Dict, Any, Optional, Literal
from datetime import datetime

class ClassificationResult(BaseModel):
    is_sensitive: bool
    matched_patterns: List[str]
    confidence: float

class EncryptedBlob(BaseModel):
    ciphertext: bytes
    nonce: bytes
    created_at: datetime

class IngestResult(BaseModel):
    doc_id: str
    routed_to: Literal["vault", "cognee"]
    matched_patterns: List[str]

class QueryResult(BaseModel):
    vault_hits: List[Dict[str, Any]]
    cognee_hits: List[Dict[str, Any]]
    total_count: int

class ForgetResult(BaseModel):
    success: bool
    message: str

class ImproveResult(BaseModel):
    audit_summary: Dict[str, Any]

class IngestRequest(BaseModel):
    content: str
    dataset_name: str

class QueryRequest(BaseModel):
    query: str
    dataset_name: str

class DatasetRequest(BaseModel):
    dataset_name: str
