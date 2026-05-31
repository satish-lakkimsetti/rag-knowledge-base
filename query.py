import sys
import requests
import weaviate
import weaviate.classes as wvc

OLLAMA_URL = "http://localhost:11434"
WEAVIATE_HOST = "localhost"
WEAVIATE_PORT = 8080
EMBEDDING_MODEL = "granite4.1:3b"
GENERATION_MODEL = "granite4.1:3b"
COLLECTION_NAME = "KnowledgeBase"
TOP_K = 3


def get_embedding(text):
    response = requests.post(
        f"{OLLAMA_URL}/api/embed",
        json={"model": EMBEDDING_MODEL, "input": text},
        timeout=60,
    )
    response.raise_for_status()
    return response.json()["embeddings"][0]


def search_chunks(embedding, top_k=TOP_K):
    with weaviate.connect_to_local(host=WEAVIATE_HOST, port=WEAVIATE_PORT) as client:
        collection = client.collections.get(COLLECTION_NAME)
        results = collection.query.near_vector(
            near_vector=embedding,
            limit=top_k,
            return_properties=["text", "chunk_index"],
            return_metadata=wvc.query.MetadataQuery(distance=True),
        )
    return results.objects


def generate_answer(question, chunks):
    context = "\n\n".join(
        f"[Chunk {obj.properties['chunk_index']}] {obj.properties['text']}"
        for obj in chunks
    )
    prompt = (
        f"Use the context below to answer the question. "
        f"If the answer is not in the context, say so.\n\n"
        f"Context:\n{context}\n\n"
        f"Question: {question}\n\n"
        f"Answer:"
    )
    response = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={"model": GENERATION_MODEL, "prompt": prompt, "stream": False},
        timeout=120,
    )
    response.raise_for_status()
    return response.json()["response"].strip()


def main(question):
    print(f"Question: {question}\n")

    print("Generating question embedding...")
    embedding = get_embedding(question)

    print(f"Searching '{COLLECTION_NAME}' for top {TOP_K} chunks...\n")
    chunks = search_chunks(embedding)

    if not chunks:
        print("No chunks found in KnowledgeBase. Run ingest.py first.")
        sys.exit(1)

    print("Retrieved chunks:")
    for obj in chunks:
        dist = obj.metadata.distance
        preview = obj.properties["text"][:80].replace("\n", " ")
        print(f"  [chunk {obj.properties['chunk_index']}] dist={dist:.4f}  \"{preview}...\"")

    print("\nGenerating answer...\n")
    answer = generate_answer(question, chunks)
    print(f"Answer:\n{answer}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 query.py \"your question here\"")
        sys.exit(1)
    main(" ".join(sys.argv[1:]))
