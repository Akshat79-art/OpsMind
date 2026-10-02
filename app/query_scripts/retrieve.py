'''
Query-stage retrieval: Embeds a question with the bge query instruction and fetch the top-k most similar chunks from the persistent Chroma collection.
'''

import os, sys
from pathlib import Path
from dotenv import load_dotenv

import chromadb

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "embedding_scripts"))

from embed import get_model

CHROMA_PATH = Path("../../data/chroma")
COLLECTION_NAME = os.getenv("COLLECTION_NAME")


def embed_query(question: str) -> list[float]:
    '''
    Embeds a search query for retrieval. 
    The bge instruction prefix is prepended so the query matches the (prefix-free) passage embeddings.
    Returns a single normalized vector.
    '''
    bge_query_instruction = "Represent this sentence for searching relevant passages: "
    vector = get_model().encode(bge_query_instruction + question, normalize_embeddings=True)
    return vector.tolist()


def get_collection() -> chromadb.Collection:

    chroma_client = chromadb.PersistentClient(path = CHROMA_PATH)

    try:
        collection = chroma_client.get_collection(name = COLLECTION_NAME)
    except chromadb.errors.NotFoundError as exc:
        raise RuntimeError(
            f"Collection '{COLLECTION_NAME}' not found at {CHROMA_PATH}."
            "Build it first with chroma_store.py."
        ) from exc

    return collection


def retrieve(question: str, top_k = 5) -> list[dict]:
    '''Returns the top_k most similar chunks for a question.'''
    vector = embed_query(question)
    collection = get_collection()
    results = collection.query(
        query_embeddings=[vector],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )
    hits = []
    for text, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        hits.append({"text": text, "metadata": meta, "distance": dist})
    return hits

def main():
    ans = retrieve("What is a router?")
    for items in ans:
        print(items)

if __name__ == "__main__":
    main()