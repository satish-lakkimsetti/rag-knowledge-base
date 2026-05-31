# Local RAG Pipeline

A fully local Retrieval-Augmented Generation (RAG) system that ingests plain text, stores semantic embeddings in a vector database, and answers questions using a local LLM — no cloud services required.

## What it does

1. **Ingest** — splits text into chunks, generates an embedding for each chunk using a local LLM, and stores the chunks + vectors in Weaviate.
2. **Query** — embeds a question, finds the most semantically similar chunks via vector search, then feeds those chunks as context to the LLM to generate a grounded answer.

## Stack

| Layer | Technology |
|---|---|
| Local LLM + Embeddings | [Ollama](https://ollama.com) running `granite4.1:3b` |
| Vector Database | [Weaviate](https://weaviate.io) |
| Embedding endpoint | Ollama `/api/embed` |
| Generation endpoint | Ollama `/api/generate` |
| Weaviate client | `weaviate-client` v4 (Python) |
| HTTP client | `requests` (Python) |
| Runtime | Python 3.14 |
| Infrastructure | Docker (Ollama on port 11434, Weaviate on port 8080) |

## Scripts

### `app.py` — Health check
Verifies that both Ollama and Weaviate are reachable before doing any work.

### `ingest.py` — Ingest text into the knowledge base
Accepts a plain text string, splits it into overlapping word-based chunks (~50 words each, 10-word overlap), generates a 2560-dim embedding for each chunk via Ollama, and stores the chunk + vector in Weaviate under a collection called `KnowledgeBase`. Creates the collection automatically if it does not exist.

### `query.py` — Query the knowledge base
Accepts a question, embeds it using Ollama, retrieves the 3 nearest chunks from Weaviate via cosine similarity search, then sends those chunks as context to Ollama to generate a final answer.

## How to run

### 1. Check both services are up

```bash
python3 /workspace/app.py
```

Expected output:
```
[OK] Ollama is reachable at http://localhost:11434
[OK] Weaviate is reachable at http://localhost:8080

Both services are up and ready.
```

### 2. Ingest text

Pass any plain text string as an argument:

```bash
python3 /workspace/ingest.py "Satish is an AI engineer based in Hyderabad. He is learning to build AI systems using Docker containers. He uses Ollama to run local LLMs and Weaviate as a vector database. His goal is to get a job in the AI field by building real projects."
```

You can also pipe text from a file:

```bash
cat mydocument.txt | python3 /workspace/ingest.py
```

Run multiple times with different text to build up the knowledge base. Each run appends new chunks — it does not overwrite existing ones.

### 3. Query the knowledge base

```bash
python3 /workspace/query.py "Where is Satish based and what is his goal?"
```

```bash
python3 /workspace/query.py "What is deep learning?"
```

```bash
python3 /workspace/query.py "What tools does Satish use?"
```

Expected output format:
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

## Configuration

All constants are defined at the top of each script and can be edited directly:

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
