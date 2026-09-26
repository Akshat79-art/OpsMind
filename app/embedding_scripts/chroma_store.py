'''
Chroma Store - Build (or refresh) a persistent vector index from chunks_data, so later ask can query it. 
One run should produce a ready-to-query Chroma collection.
'''

import json, sys
from collections.abc import Iterator
from pathlib import Path

import chromadb

from embed import embed_texts

COLLECTION_NAME = "opsmind"
BATCH_SIZE = 64

CHUNKS_ROOT = Path("../../data/chunks_data")
CHROMA_PATH = Path("../../data/chroma")

def load_chunk_batches(root: Path = CHUNKS_ROOT, size: int = BATCH_SIZE) -> Iterator[list[dict]]:
    '''
    Yields chunk records from every chunks.jsonl under root in batches
    of at most `size`, so downstream embedding/storage stays bounded.
    '''
    batch: list[dict] = []
    for chunks_path in sorted(root.rglob("chunks.jsonl")):
        with open(chunks_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                batch.append(json.loads(line))
                if len(batch) >= size:
                    yield batch
                    batch = []
    if batch:
        yield batch


def get_collection(rebuild: bool) -> chromadb.Collection:

    chroma_client = chromadb.PersistentClient(path = CHROMA_PATH)

    if rebuild:
        try:
            chroma_client.delete_collection(name=COLLECTION_NAME)
            print(f"Collection '{COLLECTION_NAME}' deleted successfully.")
        except chromadb.errors.NotFoundError:
            print(f"Collection '{COLLECTION_NAME}' does not exist. Skipping deletion.")

    collection = chroma_client.get_or_create_collection(name = COLLECTION_NAME, metadata = {"hnsw:space": "cosine"})
    return collection


def build_metadata(record: dict) -> dict:
    '''
    Builds Chroma metadata from a chunk record, omitting None values.
    '''
    metadata = {
        "category": record["category"],
        "slug": record["slug"],
        "source": record["source"],
        "order": record["order"],
        "chunk_index": record["chunk_index"],
    }
    if record.get("page") is not None:
        metadata["page"] = record["page"]
    if record.get("title") is not None:
        metadata["title"] = record["title"]
    return metadata


def run(full_rebuild: bool = False) -> None:
    '''
    Indexes all chunks into Chroma. 
    full_rebuild deletes and recreates the collection first for a clean index.
    Else it upserts into the existing one.
    '''

    collection = get_collection(full_rebuild)
    total = 0
    for batch in load_chunk_batches():
        ids = [record["chunk_id"] for record in batch]
        texts = [record["text"] for record in batch]
        metadatas = [build_metadata(record) for record in batch]
        embeddings = embed_texts(texts)
        collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
        )
        total += len(ids)
        print(f"Indexed {total} chunks")

    print(f"Done. Collection count = {collection.count()}")


def main() -> None:
    full_rebuild = "--rebuild" in sys.argv[1:]
    run(full_rebuild=full_rebuild)


if __name__ == "__main__":
    main()