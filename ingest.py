import sys
import requests
import weaviate
import weaviate.classes as wvc

OLLAMA_URL = "http://localhost:11434"
WEAVIATE_HOST = "localhost"
WEAVIATE_PORT = 8080
EMBEDDING_MODEL = "granite4.1:3b"
COLLECTION_NAME = "KnowledgeBase"
CHUNK_WORDS = 50
CHUNK_OVERLAP = 10


def chunk_text(text, chunk_words=CHUNK_WORDS, overlap=CHUNK_OVERLAP):
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        chunk = " ".join(words[start : start + chunk_words])
        chunks.append(chunk)
        if start + chunk_words >= len(words):
            break
        start += chunk_words - overlap
    return chunks


def get_embedding(text):
    response = requests.post(
        f"{OLLAMA_URL}/api/embed",
        json={"model": EMBEDDING_MODEL, "input": text},
        timeout=60,
    )
    response.raise_for_status()
    return response.json()["embeddings"][0]


def ensure_collection(client):
    if client.collections.exists(COLLECTION_NAME):
        print(f"Collection '{COLLECTION_NAME}' already exists — reusing it.")
        return client.collections.get(COLLECTION_NAME)
    collection = client.collections.create(
        name=COLLECTION_NAME,
        vectorizer_config=wvc.config.Configure.Vectorizer.none(),
        properties=[
            wvc.config.Property(name="text", data_type=wvc.config.DataType.TEXT),
            wvc.config.Property(name="chunk_index", data_type=wvc.config.DataType.INT),
        ],
    )
    print(f"Created collection '{COLLECTION_NAME}'.")
    return collection


def ingest(text):
    chunks = chunk_text(text)
    print(f"Text split into {len(chunks)} chunk(s) (~{CHUNK_WORDS} words each, {CHUNK_OVERLAP}-word overlap)\n")

    with weaviate.connect_to_local(host=WEAVIATE_HOST, port=WEAVIATE_PORT) as client:
        collection = ensure_collection(client)

        for i, chunk in enumerate(chunks):
            print(f"[{i + 1}/{len(chunks)}] Generating embedding for: \"{chunk[:60]}{'...' if len(chunk) > 60 else ''}\"")
            embedding = get_embedding(chunk)
            collection.data.insert(
                properties={"text": chunk, "chunk_index": i},
                vector=embedding,
            )
            print(f"         Stored — {len(chunk)} chars, {len(embedding)}-dim vector")

    print(f"\nDone. {len(chunks)} chunk(s) ingested into '{COLLECTION_NAME}'.")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        text = " ".join(sys.argv[1:])
    else:
        stdin_text = "" if sys.stdin.isatty() else sys.stdin.read().strip()
        text = stdin_text if stdin_text else (
            "Artificial intelligence is the simulation of human intelligence by machines. "
            "Machine learning is a subset of AI that enables systems to learn from data. "
            "Deep learning uses neural networks with many layers to model complex patterns. "
            "Natural language processing allows computers to understand and generate human language. "
            "Computer vision enables machines to interpret and understand visual information. "
            "Reinforcement learning trains agents to make decisions by rewarding desired behaviour. "
            "Large language models are trained on vast corpora of text to generate coherent responses. "
            "Embeddings are dense vector representations that capture semantic meaning of text."
        )
        if not stdin_text:
            print("No input provided — using built-in sample text.\n")

    ingest(text)
