# rag-knowledge-base

A fully local Retrieval-Augmented Generation (RAG) system. Feed it any text, ask it questions, get answers grounded in your own data — no cloud, no API costs, no data leaving your machine.

Built with Ollama, Weaviate, and Python. Everything runs locally.

---

## How it works

1. **Ingest** — you give it text. It splits it into chunks, converts each chunk into a vector (a numerical fingerprint of its meaning) using a local AI model, and stores everything in Weaviate.
2. **Search** — you ask a question. The question gets converted to a vector. Weaviate finds the chunks whose vectors are closest to your question.
3. **Answer** — those chunks get sent to the local LLM as context. It reads them and writes a grounded answer, sourced from your data.

---

## Stack

| Layer | Technology |
|---|---|
| Local LLM + Embeddings | [Ollama](https://ollama.com) with `granite4.1:3b` |
| Vector database | [Weaviate](https://weaviate.io) |
| Embedding endpoint | Ollama `/api/embed` |
| Generation endpoint | Ollama `/api/generate` |
| Weaviate client | `weaviate-client` v4 (Python) |
| HTTP client | `requests` (Python) |
| Runtime | Python 3.8+ |
| Infrastructure | Docker |

---

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) installed and running
- [Ollama](https://ollama.com/download) installed (available for macOS, Linux, and Windows)
- Python 3.8+

---

## Setup

### 1. Install Ollama

Download and install from [ollama.com/download](https://ollama.com/download) for your platform.

Then pull the model used by this project:

```bash
ollama pull granite4.1:3b
```

Ollama runs on `http://localhost:11434` by default.

---

### 2. Run Weaviate

```bash
docker run -d \
  --network host \
  --name weaviate \
  -e AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED=true \
  -e PERSISTENCE_DATA_PATH=/var/lib/weaviate \
  -e DEFAULT_VECTORIZER_MODULE=none \
  -e CLUSTER_HOSTNAME=node1 \
  cr.weaviate.io/semitechnologies/weaviate:latest
```

> **Windows/macOS:** Replace `--network host` with `-p 8080:8080` since host networking behaves differently outside Linux.

Verify it is running:

```bash
curl http://localhost:8080/v1/meta
```

You should see a JSON response with Weaviate version info.

**Environment variables explained:**

| Variable | Value | Purpose |
|---|---|---|
| `AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED` | `true` | Disables login — fine for local dev |
| `PERSISTENCE_DATA_PATH` | `/var/lib/weaviate` | Where Weaviate stores data inside the container |
| `DEFAULT_VECTORIZER_MODULE` | `none` | We handle vectorization ourselves via Ollama |
| `CLUSTER_HOSTNAME` | `node1` | Required name for the single-node cluster |

---

### 3. Clone this repo

```bash
git clone https://github.com/satish-lakkimsetti/rag-knowledge-base.git
cd rag-knowledge-base
```

---

### 4. Create a virtual environment and install dependencies

```bash
python -m venv venv
```

Activate it:

```bash
# macOS / Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

Install dependencies:

```bash
pip install weaviate-client requests
```

---

## Scripts

### `app.py` — Health check
Verifies that both Ollama and Weaviate are reachable before doing any work.

### `ingest.py` — Ingest text into the knowledge base
Accepts a plain text string, splits it into overlapping word-based chunks (~50 words each, 10-word overlap), generates a 2560-dim embedding for each chunk via Ollama `/api/embed`, and stores the chunk + vector in Weaviate under a collection called `KnowledgeBase`. Creates the collection automatically if it does not exist.

### `query.py` — Query the knowledge base
Accepts a question, embeds it using Ollama, retrieves the 3 nearest chunks from Weaviate via cosine similarity search, then sends those chunks as context to Ollama `/api/generate` to produce a final grounded answer.

---

## Usage

### Step 1 — Health check

```bash
python app.py
```

Expected output:
```
[OK] Ollama is reachable at http://localhost:11434
[OK] Weaviate is reachable at http://localhost:8080
Both services are up and ready.
```

---

### Step 2 — Ingest text

Pass any text as an argument:

```bash
python ingest.py "Satish is an AI engineer based in Hyderabad. He is learning to build AI systems using Docker. He uses Ollama to run local LLMs and Weaviate as a vector database. His goal is to get a job in the AI field by building real projects."
```

Or pipe from a file:

```bash
cat mydocument.txt | python ingest.py
```

Run multiple times with different text to grow the knowledge base. Each run appends — it does not overwrite.

Expected output:
```
Text split into 1 chunk(s) (~50 words each, 10-word overlap)
Collection 'KnowledgeBase' already exists — reusing it.
Ingesting chunk 1/1... done (2560 dims)
Ingestion complete. 1 chunk(s) stored in 'KnowledgeBase'.
```

---

### Step 3 — Ask a question

```bash
python query.py "Where is Satish based and what is his goal?"
```

```bash
python query.py "What is deep learning?"
```

```bash
python query.py "What tools does Satish use?"
```

Expected output:
```
Question: Where is Satish based and what is his goal?

Generating question embedding...
Searching 'KnowledgeBase' for top 3 chunks...

Retrieved chunks:
  [chunk 3] dist=0.3300  "Satish is an AI engineer based in Hyderabad..."
  [chunk 1] dist=0.6193  "Artificial intelligence is the simulation of..."
  [chunk 2] dist=0.7794  "computers to understand and generate human language..."

Generating answer...

Answer:
Satish is based in Hyderabad, and his goal is to get a job in the AI field by building real projects.
```

---

## Configuration

All settings are defined at the top of each script and can be edited directly:

| Constant | Default | Description |
|---|---|---|
| `OLLAMA_URL` | `http://localhost:11434` | Ollama API base URL |
| `WEAVIATE_HOST` | `localhost` | Weaviate host |
| `WEAVIATE_PORT` | `8080` | Weaviate port |
| `EMBEDDING_MODEL` | `granite4.1:3b` | Model used for embeddings |
| `GENERATION_MODEL` | `granite4.1:3b` | Model used for answer generation |
| `COLLECTION_NAME` | `KnowledgeBase` | Weaviate collection name |
| `CHUNK_WORDS` | `50` | Target chunk size in words |
| `CHUNK_OVERLAP` | `10` | Word overlap between consecutive chunks |
| `TOP_K` | `3` | Number of chunks retrieved per query |

---

## Project structure

```
rag-knowledge-base/
├── app.py        # Health check — verifies Ollama and Weaviate are reachable
├── ingest.py     # Ingests text into the knowledge base
├── query.py      # Queries the knowledge base and generates an answer
└── README.md
```

---

## Cleanup

Stop and remove Weaviate:

```bash
docker stop weaviate && docker rm weaviate
```

Remove the Ollama model:

```bash
ollama rm granite4.1:3b
```
