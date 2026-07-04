# The Tale of Vault: A Privacy-Preserving Memory Layer for Cognee

## Chapter 1: The Curse of the Perfect Memory

Once upon a time in the realm of AI, there existed memory layers like Cognee. They were magnificent, designed to remember everything an agent was told. This was incredibly powerful—until "everything" began to include API keys, credentials, and whispered secrets that were never meant to be stored forever in plain sight. 

The problem was clear: Cognee's brilliant hybrid graph-vector search needed to read the plaintext to understand the world, extract entities, and compute embeddings. But how could one protect the kingdom's secrets when standard searchable encryption couldn't support semantic search natively?

## Chapter 2: The Vault is Forged

Our heroes realized they couldn't encrypt the entire world without losing the magic of the graph. Instead, they built **Vault**—a vigilant gatekeeper standing before Cognee. 

Vault operates with a simple but profound rule: *Decide, chunk by chunk, what the AI is allowed to see.* 

When a user speaks, Vault's classifier leaps into action. Safe, everyday knowledge flows freely into Cognee to receive the full graph treatment. But the moment a secret is detected, Vault snatches it away. It encrypts the sensitive data with AES-GCM and locks it in a local SQLite vault, far away from Cognee's prying eyes. 

To ensure the user could still find their secrets, Vault leaves behind a clever Trapdoor Index (HMAC-SHA256). The data remains searchable by keyword, and every glance is cryptographically audited. When the time comes to forget, Vault doesn't just erase the record—it shatters the encryption key, casting the memory into the abyss, permanently irrecoverable.

## Chapter 3: The Architecture of the Gate

```text
User's Whisper 
      │
      ▼
[ Classifier ] ──(Is it a secret?)──▶ [ YES ] ──▶ AES-GCM Encrypted Vault (Local SQLite)
      │                                                 └─ Trapdoor Index (HMAC-SHA256)
      │
    [ NO ]
      │
      ▼
Cognee Cloud (Graph/Vector Magic)
```

## Chapter 4: Embarking on the Journey (Quickstart)

Are you ready to deploy your own Vault? Follow these steps, brave adventurer:

1. **Summon the Backend**:
```bash
git clone <your-repo-url>
cd vault/backend
python -m venv venv

# If you wield Windows:
.\venv\Scripts\activate
# If you wield Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

2. **Prepare the Environment**:
Create your sacred `.env` scroll by copying `backend/.env.example` to `backend/.env`. Visit [platform.cognee.ai](https://platform.cognee.ai) and invoke the code **COGNEE-35** for free mystical credits.

```env
COGNEE_SERVICE_URL=https://api.cognee.ai
COGNEE_API_KEY=your_api_key_here
VAULT_MASTER_KEY=super_secret_master_key
```

3. **Awaken the Backend**:
```bash
uvicorn app.main:app --port 8000
```

4. **Awaken the Frontend**:
In a fresh terminal window, chant:
```bash
cd vault/frontend
npm install
npm run dev
```
Then, gaze into the portal at `http://localhost:5173`.

## Chapter 5: The Dance with Cognee

Vault does not work alone; it dances intimately with the Cognee SDK lifecycle:

- **`cognee.remember()`**: The gate opens, but only non-sensitive data may pass into the `MemoryService.ingest`.
- **`cognee.recall()`**: A dual search occurs. The `MemoryService.query` fetches graph results while Vault simultaneously searches the secure trapdoor, merging the two realms seamlessly.
- **`cognee.forget()`**: When the command is given, `MemoryService.forget` wipes the public graph, while Vault performs a cryptographic erasure, ensuring the dataset is completely cleansed.
- **`cognee.improve()`**: Used strictly for the public graph. The LLM is expressly forbidden from enriching the decrypted sensitive content.

## Epilogue: Confessions of the Architects

Under the sacred rules of the hackathon, we must confess that Claude (via Anthropic) served as our loyal development apprentice. We provided strict architectural decrees and guided Claude to scaffold the boilerplate, forge tests, and craft the React UI. All cryptographic logic, limitations, and control flows were dictated by human design.

## Appendix: The Cracks in the Armor (Known Limitations)

Even the most formidable Vault has its flaws:
- **Search Pattern Echoes**: The deterministic trapdoor index reveals query patterns. An observant adversary might infer term frequency. We accept this limitation of deterministic Searchable Symmetric Encryption (SSE), choosing to watch the watchers via our access audit log.
- **The Regex Illusion**: The current classifier relies on regex, a simple spell that a cunning adversary might evade through obfuscation.
- **A Prototype's Promise**: This Vault is a proof-of-concept. It demonstrates a privacy-preserving routing layer but has not yet been hardened for the brutal battlefields of production.
