"""
Utility functions for text embeddings and hashing.
"""

import hashlib
from typing import List

from sentence_transformers import SentenceTransformer

from ..config import get_settings


def get_text_hash(text: str) -> str:
    """Generate MD5 hash for text."""
    return hashlib.md5(text.encode('utf-8')).hexdigest()


def get_text_embedding(text: str) -> List[float]:
    """Generate embedding for text using the configured model."""
    settings = get_settings()
    
    try:
        model = SentenceTransformer(settings.embedding_model)
        embedding = model.encode(text)
        return embedding.tolist()
    except Exception as e:
        raise Exception(f"Failed to generate embedding: {e}")


def get_text_similarity(text1: str, text2: str) -> float:
    """Calculate cosine similarity between two texts."""
    try:
        embedding1 = get_text_embedding(text1)
        embedding2 = get_text_embedding(text2)
        
        # Calculate cosine similarity
        dot_product = sum(a * b for a, b in zip(embedding1, embedding2))
        magnitude1 = sum(a * a for a in embedding1) ** 0.5
        magnitude2 = sum(b * b for b in embedding2) ** 0.5
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
        
    except Exception as e:
        raise Exception(f"Failed to calculate similarity: {e}") 