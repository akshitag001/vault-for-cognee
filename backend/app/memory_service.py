import uuid
import asyncio
from typing import Optional
from app.models import IngestResult, QueryResult, ForgetResult, ImproveResult
from app.classifier import classify_chunk
from app.crypto import DecryptionFailedError
from app.vault_store import VaultStore
import app.cognee_client as cognee_client
import app.access_log as access_log

class MemoryService:
    """
    Ties together the classifier, vault_store, and cognee_client.
    This is the core routing layer of the Vault product logic.
    """
    def __init__(self, vault_store: VaultStore):
        self.vault_store = vault_store

    async def ingest(self, content: str, dataset_name: str, doc_id: Optional[str] = None) -> IngestResult:
        """
        Ingests content into the system. If classified as sensitive, it is routed
        exclusively to the local encrypted VaultStore. If not sensitive, it routes
        to Cognee Cloud for semantic graph enrichment.
        """
        if doc_id is None:
            doc_id = str(uuid.uuid4())

        classification = classify_chunk(content)
        
        if classification.is_sensitive:
            # Route to encrypted vault. Never touches Cognee.
            self.vault_store.put(dataset_name, doc_id, content)
            
            return IngestResult(
                doc_id=doc_id,
                routed_to="vault",
                matched_patterns=classification.matched_patterns
            )
        else:
            # Normal semantic content routes to Cognee Cloud.
            await cognee_client.remember_normal(content, dataset_name)
            
            return IngestResult(
                doc_id=doc_id,
                routed_to="cognee",
                matched_patterns=[]
            )

    async def query(self, query_text: str, dataset_name: str) -> QueryResult:
        """
        Queries both the encrypted vault (for exact keyword/trapdoor matches) and
        Cognee Cloud (for semantic graph matches) concurrently, merging the results.
        """
        # Wrap the synchronous vault_store.search in an async helper
        # to allow running concurrently with the cognee network call.
        async def _search_vault():
            try:
                return self.vault_store.search(dataset_name, query_text)
            except DecryptionFailedError:
                return []
            
        # Run both searches concurrently
        vault_task = asyncio.create_task(_search_vault())
        cognee_task = asyncio.create_task(cognee_client.recall_normal(query_text, dataset_name))
        
        vault_hits, cognee_hits = await asyncio.gather(vault_task, cognee_task)
        
        # Tag vault hits with their source so the frontend can visually distinguish them.
        for hit in vault_hits:
            hit["source"] = "vault"
            
        # cognee_hits are already tagged with source="cognee" by the client wrapper
        
        total = len(vault_hits) + len(cognee_hits)
        
        return QueryResult(
            vault_hits=vault_hits,
            cognee_hits=cognee_hits,
            total_count=total
        )

    async def forget(self, dataset_name: str) -> ForgetResult:
        """
        Forgets a dataset by cryptographically erasing the Vault and
        issuing a forget command to Cognee Cloud.
        """
        self.vault_store.forget_dataset(dataset_name)
        await cognee_client.forget_normal(dataset_name)
        
        return ForgetResult(
            success=True,
            message=f"Dataset {dataset_name} has been forgotten in both Vault and Cognee."
        )

    async def improve(self, dataset_name: str) -> ImproveResult:
        """
        Triggers graph improvement processes.
        Explicitly does NOT run LLM-based semantic enrichment over the sensitive 
        encrypted vault content, as we do not want LLMs touching plaintext sensitive data.
        Instead, this returns an 'audit improve' summary for the sensitive partition.
        """
        # 1. Normal partition -> cognee.improve()
        # We explicitly skip LLM-based enrichment for sensitive vault partition here.
        await cognee_client.improve_normal()
        
        # 2. Sensitive partition -> "audit improve"
        # We surface an access pattern audit summary for transparency.
        logs = access_log.get_access_log(dataset_name)
        
        total_queries = len(logs)
        doc_counts = {}
        for entry in logs:
            for doc in entry.get("matched_doc_ids", []):
                doc_counts[doc] = doc_counts.get(doc, 0) + 1
                
        sorted_docs = sorted(doc_counts.items(), key=lambda x: x[1], reverse=True)
        top_queried_docs = [doc for doc, count in sorted_docs[:5]]
        
        summary = {
            "total_sensitive_queries": total_queries,
            "most_queried_docs": top_queried_docs
        }
        
        return ImproveResult(audit_summary=summary)
