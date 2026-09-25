'''
Computes embeddings for chunk text. Storage (Chroma) is a separate step.
Run from app/embedding_scripts.
'''

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

MODEL_NAME = os.getenv("MODEL_NAME")
BATCH_SIZE = 64

@lru_cache(maxsize=1)
def get_model() -> SentenceTransformer:
    '''Loads the embedding model once, on first use.'''
    return SentenceTransformer(MODEL_NAME)


def embed_texts(texts: list[str]) -> list[list[float]]:
    '''
    Embeds texts, normalized for cosine similarity, and returns the vectors.
    '''
    if not texts:
        return []
    vectors = get_model().encode(texts, batch_size=BATCH_SIZE, normalize_embeddings=True)
    return vectors.tolist()
