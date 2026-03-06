# Nexus

> The central point for your files and AI — a self-hosted, multi-tenant AI chat platform with RAG (Retrieval-Augmented Generation), document intelligence, and support for any LLM.

Nexus lets your team chat with AI models, upload documents, and get answers grounded in your own knowledge base — all running on your own infrastructure with no data leaving your servers.

---

## Features

- 🤖 **Multi-model chat** — Switch between local Ollama models (Llama 3, Qwen 2.5, LLaVA) or external API providers (OpenAI, Anthropic, any OpenAI-compatible endpoint) mid-conversation
- 📄 **Document intelligence** — Upload PDFs, images, and text files; the pipeline chunks, embeds, and indexes them automatically for RAG retrieval
- 🔍 **Smart RAG** — An AI router decides per-message whether retrieval is needed, so you don't pay retrieval cost on simple questions
- 🧠 **Long-context memory** — Conversations are stored in Redis; a summarizer agent compresses old history so the LLM context window never overflows
- 🏢 **Multi-tenant** — Organizations and users are fully isolated; each team gets its own data partition
- 🔐 **Secure API key management** — Users store their own LLM provider keys, encrypted at rest
- 🖼️ **Multimodal** — Send images alongside text; LLaVA describes images extracted from PDFs
- ✏️ **Message editing & regeneration** — Edit any past message and get a fresh response, or regenerate the last assistant reply
- 🗂️ **Artifact rendering** — Code, markdown, and diagram artifacts are extracted from LLM responses and rendered separately in the UI

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React + Vite (served via Nginx) |
| Backend API | FastAPI (Python) |
| Orchestration | FastAPI microservice |
| LLM Host | FastAPI + Ollama / OpenAI-compatible APIs |
| RAG Pipeline | FastAPI + LangChain + BGE embeddings + CLIP |
| Conversation Store | Redis 7 |
| Relational DB | PostgreSQL 15 |
| Vector DB | Qdrant |
| Object Storage | MinIO (S3-compatible) |
| Container Runtime | Docker + Docker Compose |

---

## Architecture

```
┌──────────────┐
│    Client    │  React SPA  :5173
└──────┬───────┘
       │ REST
┌──────▼───────┐
│   Backend    │  FastAPI    :8000
│  (Auth, API) │
└──────┬───────┘
       │             ┌─────────┐
       ├────────────▶│  Redis  │  Conversation store  :6379
       │             └─────────┘
       │             ┌──────────────┐
       ├────────────▶│  PostgreSQL  │  Users, orgs, docs  :5432
       │             └──────────────┘
       │             ┌──────────────┐
       ├────────────▶│    MinIO     │  File storage  :9000
       │             └──────────────┘
       │ HTTP
┌──────▼──────────────┐
│   Orchestration     │  FastAPI  :8001
│  (routes requests)  │
└────┬────────────────┘
     │                │
┌────▼──────┐  ┌──────▼────────┐
│ LLMs Host │  │ RAG Pipeline  │
│ :8002     │  │ :8003         │
└────┬──────┘  └──────┬────────┘
     │                │
     └──────┬─────────┘
            ▼
       ┌─────────┐
       │ Qdrant  │  Vector DB  :6333
       └─────────┘
```

---

## Getting Started

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose
- [Ollama](https://ollama.com/) installed locally (or on a reachable host) with at least one model pulled

```bash
# Pull the recommended models
ollama pull llama3
ollama pull qwen2.5:32b
ollama pull llava
```

### 1. Clone the repository

```bash
git clone https://github.com/your-username/nexus.git
cd nexus
```

### 2. Configure environment variables

Copy the example env file and fill in your values:

```bash
cp database/postgress/.env.example database/postgress/.env
```

Then create a `.env` file at the project root:

```env
# Authentication
JWT_SECRET=your-super-secret-jwt-key-change-this
GOOGLE_CLIENT_ID=                    # optional, for Google OAuth

# Encryption (for stored API keys)
ENCRYPTION_KEY=your-32-byte-fernet-key

# MinIO (object storage)
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin123
```

> **Generate a Fernet key:**
> ```bash
> python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
> ```

### 3. Start all services

```bash
docker compose up -d
```

This starts 8 containers: `postgres`, `redis`, `minio`, `backend`, `client`, `orchestration`, `llms_host`, and `rag_pipeline`.

### 4. Open the app

Visit **http://localhost:5173**, register an account, and start chatting.

---

## Project Structure

```
nexus/
├── client/               # React frontend (Vite)
├── backend/              # Main API — auth, conversations, files, orgs
│   ├── routers/          # FastAPI route handlers
│   ├── redis_client.py   # All Redis operations
│   └── services/         # MinIO storage service
├── orchestration/        # Request router — decides LLM vs RAG path
├── llms_host/            # LLM engine + agent framework
│   ├── agents/           # 8 specialized agents (chat, summarizer, router…)
│   ├── memory/           # Redis-backed conversation context
│   └── prompts/          # System prompts per agent
├── rag_pipline/          # Document ingestion & retrieval pipeline
│   ├── preprocessing/    # PDF, image, table extraction
│   ├── chunking/         # Sentence & semantic chunking strategies
│   ├── retrival/         # Qdrant vector search
│   └── document_pipeline.py
├── database/
│   ├── postgress/        # Schema SQL + setup scripts
│   └── redis/            # Redis documentation
├── docker-compose.yml
└── README.md
```

---

## Services & Ports

| Service | Port | Description |
|---|---|---|
| Client (React) | `5173` | Web UI |
| Backend API | `8000` | REST API — auth, chat, files |
| Orchestration | `8001` | Internal request router |
| LLMs Host | `8002` | LLM engine + agent runner |
| RAG Pipeline | `8003` | Document processing & retrieval |
| Redis | `6379` | Conversation memory |
| PostgreSQL | `5432` | Persistent relational data |
| Qdrant | `6333` | Vector embeddings |
| MinIO API | `9000` | Object storage API |
| MinIO Console | `9001` | MinIO web UI |

---

## How It Works

### Sending a Message

1. The React client sends `POST /conversations/{session_id}/chat` to the backend.
2. The backend forwards the request to the **Orchestration** service along with the user's API key (decrypted on the fly).
3. Orchestration passes it to the **Retrieval Decision Agent**, which decides whether documents from the knowledge base are relevant.
4. If retrieval is triggered, **RAG Pipeline** searches Qdrant and returns matching chunks as context.
5. The **Chat Agent** in `llms_host` assembles the full context (history from Redis + retrieved docs + user message) and calls the LLM.
6. The backend writes both the user message and the assistant reply back to Redis with token counts.
7. The client renders the response, including any extracted code/markdown artifacts.

### Uploading a Document

1. The client sends `POST /files/upload` with the file.
2. The backend saves the raw file to **MinIO** and records metadata in **PostgreSQL**.
3. A background task calls the **Orchestration** service to kick off the RAG Pipeline.
4. The pipeline: downloads from MinIO → preprocesses (OCR optional) → chunks → generates embeddings (BGE for text, CLIP for images) → stores in **Qdrant**.
5. The document is now searchable in future conversations.

---

## Agents

`llms_host` runs a framework of specialized agents, each with its own system prompt, model, and temperature:

| Agent | Model | Temp | Role |
|---|---|---|---|
| ChatAgent | `qwen2.5:32b` | 0.7 | Main conversational agent |
| SummarizerAgent | `llama3` | 0.2 | Compresses long conversation history |
| QueryReWriterAgent | `llama3` | 0.5 | Rewrites queries for better retrieval |
| RouterAgent | `llama3` | 0.1 | Routes requests to the correct pipeline |
| RetrievalDecisionAgent | `llama3` | 0.1 | Decides if RAG lookup is needed |
| SQLAgent | `llama3` | 0.1 | Generates SQL from natural language |
| ImageDescriptionAgent | `llava` | 0.3 | Describes images for multimodal input |
| TableDescriptionAgent | `llama3` | 0.2 | Summarises tabular data from documents |

---

## Using External LLM Providers

Nexus supports any OpenAI-compatible API endpoint. In the UI, go to **Settings → API Keys** and add your key for a provider. The key is AES-encrypted before being stored in PostgreSQL and decrypted per-request by the backend — it is never logged or stored in plaintext.

Supported providers include OpenAI, Anthropic (via compatible proxy), Groq, Together AI, and any self-hosted endpoint that implements the OpenAI chat completions spec.

---

## Database Schema

PostgreSQL stores durable, relational data. The core tables are:

| Table | Purpose |
|---|---|
| `organizations` | Multi-tenant isolation — each org has its own plan and user cap |
| `users` | Authentication, roles (`admin`, `employee`, `viewer`), org membership |
| `user_settings` | Per-user preferences stored as JSONB |
| `api_keys` | Encrypted LLM provider keys per user |
| `documents` | File metadata (MinIO path, filename, type, processing status) |
| `usage_tracking` | Token usage per session and model |

Conversation history lives in **Redis**, not Postgres — keeping chat fast and avoiding row-level locking on high-throughput message writes.

---

## Configuration Reference

| Variable | Service | Description |
|---|---|---|
| `JWT_SECRET` | backend | Secret for signing JWTs |
| `ENCRYPTION_KEY` | backend | Fernet key for API key encryption |
| `GOOGLE_CLIENT_ID` | backend | For Google OAuth (optional) |
| `REDIS_HOST` / `REDIS_PORT` | backend, llms_host, rag_pipeline | Redis connection |
| `DB_HOST` / `DB_PORT` / `DB_NAME` / `DB_USER` / `DB_PASSWORD` | backend | PostgreSQL connection |
| `MINIO_ENDPOINT` / `MINIO_ACCESS_KEY` / `MINIO_SECRET_KEY` | backend, rag_pipeline | MinIO connection |
| `ORCHESTRATION_URL` | backend | Internal URL of the orchestration service |
| `LLMS_HOST_URL` | orchestration | Internal URL of the LLM host service |
| `RAG_PIPELINE_URL` | orchestration | Internal URL of the RAG pipeline service |
| `OLLAMA_HOST` | llms_host | Ollama server URL (default: `http://localhost:11434`) |

---

## Development

### Run only the infrastructure (databases)

```bash
docker compose up -d postgres redis minio
```

### Run a service locally

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# LLMs Host
cd llms_host
pip install -r requirement.txt
uvicorn main:app --reload --port 8002
```

### Check service logs

```bash
docker compose logs -f backend
docker compose logs -f llms_host
```

### Inspect Redis conversations

```bash
docker exec -it nexus_redis redis-cli
KEYS conversation:*
GET conversation:<session_id>
```

---

## License

[MIT](LICENSE)
