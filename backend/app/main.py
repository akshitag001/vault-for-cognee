from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os

from app.crypto import KeyStore
from app.vault_store import VaultStore
from app.memory_service import MemoryService
import app.cognee_client as cognee_client
import app.access_log as access_log
from app.models import IngestRequest, QueryRequest, DatasetRequest, IngestResult, QueryResult, ForgetResult, ImproveResult

keystore = KeyStore(storage_path=os.getenv("VAULT_KEYSTORE_PATH", "keystore.json"))
vault_store = VaultStore(keystore=keystore, db_path=os.getenv("VAULT_DB_PATH", "vault_store.db"))
memory_service = MemoryService(vault_store=vault_store)

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await cognee_client.connect()
    except Exception as e:
        print(f"Warning: Failed to connect to Cognee on startup: {e}")
    yield

app = FastAPI(title="Vault API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/ingest", response_model=IngestResult)
async def ingest(request: IngestRequest):
    return await memory_service.ingest(content=request.content, dataset_name=request.dataset_name)

@app.post("/query", response_model=QueryResult)
async def query(request: QueryRequest):
    return await memory_service.query(query_text=request.query, dataset_name=request.dataset_name)

@app.post("/forget", response_model=ForgetResult)
async def forget(request: DatasetRequest):
    return await memory_service.forget(dataset_name=request.dataset_name)

@app.post("/improve", response_model=ImproveResult)
async def improve(request: DatasetRequest):
    return await memory_service.improve(dataset_name=request.dataset_name)

@app.get("/access-log/{dataset_name}")
async def get_access_log(dataset_name: str):
    return access_log.get_access_log(dataset_name)

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "cognee_connected": cognee_client._is_connected
    }

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
