# Vault — Privacy-Preserving Memory Layer on Cognee

Memory layers like Cognee make AI agents remember everything — which is great, until "everything" includes API keys, credentials, or private details that a user pasted into a note without thinking. **Vault** adds a classification and encryption gate in front of Cognee: normal content flows through to get full graph/vector richness, but anything sensitive is encrypted with AES-GCM before it ever reaches Cognee's pipeline. It's indexed separately using a deterministic searchable-encryption scheme so it remains findable by keyword, and every access is cryptographically audited. When you call `forget()`, Vault doesn't just delete rows — it destroys the encryption key, making the ciphertext permanently irrecoverable.

## The Problem

Cognee's hybrid graph-vector search needs to process plaintext to extract entities and compute embeddings. Standard searchable encryption schemes can't support that kind of semantic search natively. 

Vault solves this by not trying to encrypt everything. Instead, it decides — chunk by chunk — what Cognee is allowed to see. Safe semantic content gets the full graph treatment; sensitive data is routed exclusively into a locked local vault.

## Architecture

```text
User Input 
   │
   ▼
[ Classifier ] ──(Sensitive?)──▶ [ YES ] ──▶ AES-GCM Encrypted Vault (Local SQLite)
   │                                           └─ Trapdoor Index (HMAC-SHA256)
   │
 [ NO ]
   │
   ▼
Cognee Cloud (Graph/Vector)
```

## Quickstart

1. **Clone and setup the backend**:
```bash
git clone <your-repo-url>
cd vault/backend
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate
pip install -r requirements.txt
```

2. **Environment Setup**:
Copy `backend/.env.example` to `backend/.env`. Sign in at [platform.cognee.ai](https://platform.cognee.ai) and use the code **COGNEE-35** for free credits.
```env
COGNEE_SERVICE_URL=https://api.cognee.ai
COGNEE_API_KEY=your_api_key_here
VAULT_MASTER_KEY=super_secret_master_key
```

3. **Run the backend**:
```bash
uvicorn app.main:app --port 8000
```

4. **Run the frontend**:
In a new terminal:
```bash
cd vault/frontend
npm install
npm run dev
```
Open `http://localhost:5173` in your browser.

## Cognee Lifecycle Integration

Vault deeply integrates with the Cognee SDK lifecycle:
- **`cognee.remember()`**: Called in `MemoryService.ingest` only for data classified as non-sensitive.
- **`cognee.recall()`**: Called concurrently alongside the Vault search in `MemoryService.query` to merge graph results with secure trapdoor hits.
- **`cognee.forget()`**: Triggered alongside cryptographic erasure in `MemoryService.forget` to ensure complete dataset wiping across both partitions.
- **`cognee.improve()`**: Leveraged in `MemoryService.improve` strictly for the public graph. We explicitly do NOT run LLM-based enrichment over the decrypted sensitive content.

## AI Assistant Disclosure

Under the hackathon's disclosure rules, I want to clearly state that I utilized Claude (via Anthropic) as a development assistant during this build. I provided strict, sequenced architectural prompts, directed all security and system design decisions, and guided Claude to scaffold the boilerplate, tests, and React UI components. All cryptographic logic, limitations, and control flows were explicitly dictated by my design spec.

## Known Limitations

- **Search Pattern Leakage**: The deterministic trapdoor index leaks query co-occurrence patterns (an adversary watching the index could infer term frequency). This is a known limitation of deterministic Searchable Symmetric Encryption (SSE), which we mitigate via the access audit log rather than attempting to hide it.
- **Classifier Evasion**: The current sensitive data classifier is regex-based and is not bulletproof against adversarial obfuscation.
- **Hackathon Status**: This is a proof-of-concept prototype demonstrating a privacy-preserving routing layer. It is not currently hardened for production deployment.
