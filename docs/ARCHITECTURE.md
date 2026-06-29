# Vault Architecture and Design Decisions

## Full Data Flow

The core principle of Vault is data routing based on sensitivity.

1. **Ingestion (`POST /ingest`)**:
   Incoming text is pushed into the `MemoryService`. The data is instantly run against a regex-based classifier.
   - If **Normal**: The text is forwarded to `cognee.remember()`, allowing Cognee to extract entities, build relationships, and generate vector embeddings.
   - If **Sensitive**: The text bypasses Cognee entirely. A unique AES-GCM key is derived for the dataset, encrypting the text. The ciphertext is written to a local SQLite database, and the words are hashed via HMAC-SHA256 into a Deterministic Trapdoor Index.

2. **Querying (`POST /query`)**:
   When a user searches, the `MemoryService` triggers a concurrent query.
   - It awaits `cognee.recall()` to pull semantic and graph-based hits.
   - It hashes the query words and checks the local Trapdoor Index. If hits are found, the AES key decrypts the ciphertext. 
   - A Cryptographic Audit Log records the query hash and the matched documents (before returning to the user).

## Cryptographic Erasure

When `forget()` is called, Vault executes cryptographic erasure. Instead of executing `DELETE` statements on the SQLite tables (which can leave artifacts on disk or in write-ahead logs), the `KeyStore` explicitly destroys the AES-GCM and HMAC keys associated with that dataset.

Without the keys, the ciphertext permanently becomes cryptographic garbage. This guarantees that even if an adversary recovers the raw SQLite file from the disk later, the data is entirely irrecoverable. The `cognee.forget()` method is also invoked to purge the semantic side.

## Design Decisions

### Why we don't encrypt everything
Cognee's primary value proposition is its hybrid graph-vector search. To build a knowledge graph and extract embeddings, Cognee fundamentally needs to process plaintext. Standard searchable encryption (SSE) schemes or Fully Homomorphic Encryption (FHE) are currently too slow or unsupported to allow native semantic operations. By splitting the stream and deciding *per-chunk* what Cognee is allowed to see, we maintain 95% of the graph's utility while perfectly isolating the 5% of data that is dangerously sensitive.

### Why we don't run `improve()` on decrypted sensitive content
The `cognee.improve()` lifecycle hook leverages LLMs to enrich graph data. Running this over sensitive data would mean decrypting the vault and sending plaintext secrets (like API keys or SSNs) back to an external language model API. This completely defeats the purpose of the Vault. We explicitly omit the sensitive partition from semantic enrichment, instead replacing it with an "Audit Improve" summary that surfaces access logs for transparency.
