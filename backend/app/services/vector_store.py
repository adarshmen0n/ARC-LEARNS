"""Vector store and RAG indexing service for ARC LEARNS.

Implements TF-IDF / BM25 lexical vector similarity, zero external heavy dependencies,
disk persistence to prevent Render cold-start data loss, and safe fallback search.
"""

import json
import logging
import math
import os
import re
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger("arc_learns.vector_store")

# Global state
documents: List[str] = []
document_vectors: List[Dict[str, float]] = []
idf: Dict[str, float] = {}
vocabulary: set = set()

STORAGE_DIR = Path("processed")
STORAGE_FILE = STORAGE_DIR / "vector_store.json"


def tokenize(text: str) -> List[str]:
    """Tokenize text into lowercase alpha-numeric tokens."""
    return re.findall(r"[a-zA-Z0-9]+", text.lower())


def save_store_to_disk() -> None:
    """Persist vector store to disk so Render cold starts retain uploaded knowledge."""
    try:
        STORAGE_DIR.mkdir(parents=True, exist_ok=True)
        data = {
            "documents": documents,
            "document_vectors": document_vectors,
            "idf": idf,
            "vocabulary": list(vocabulary),
        }
        with open(STORAGE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        logger.info("Persisted %d chunks to %s", len(documents), STORAGE_FILE)
    except Exception as e:
        logger.warning("Could not persist vector store: %s", e)


def load_store_from_disk() -> bool:
    """Reload vector store from disk if in-memory store is empty."""
    global documents, document_vectors, idf, vocabulary
    if not STORAGE_FILE.exists():
        return False
    try:
        with open(STORAGE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        documents = data.get("documents", [])
        document_vectors = data.get("document_vectors", [])
        idf = data.get("idf", {})
        vocabulary = set(data.get("vocabulary", []))
        logger.info("Restored %d chunks from %s", len(documents), STORAGE_FILE)
        return len(documents) > 0
    except Exception as e:
        logger.warning("Could not restore vector store from disk: %s", e)
        return False


def create_vector_store(chunks: List[str]) -> None:
    """Create a TF-IDF vector store from extracted document chunks and save to disk."""
    global documents, document_vectors, idf, vocabulary

    documents = []
    document_vectors = []
    idf = {}
    vocabulary = set()

    # Filter non-empty chunks
    for chunk in chunks:
        if chunk and str(chunk).strip():
            documents.append(str(chunk).strip())

    if not documents:
        return

    # 1. Tokenize all chunks
    tokenized_docs = [tokenize(doc) for doc in documents]
    for tokens in tokenized_docs:
        vocabulary.update(tokens)

    total_docs = len(documents)

    # 2. Compute Document Frequency and IDF
    df = Counter()
    for tokens in tokenized_docs:
        for t in set(tokens):
            df[t] += 1

    for token in vocabulary:
        idf[token] = math.log((total_docs + 1) / (df[token] + 1)) + 1.0

    # 3. Compute TF-IDF vectors
    for tokens in tokenized_docs:
        tf = Counter(tokens)
        doc_len = max(1, len(tokens))
        vec: Dict[str, float] = {}
        for token, count in tf.items():
            vec[token] = (count / doc_len) * idf.get(token, 1.0)
        document_vectors.append(vec)

    # Persist to disk for cold-start resilience
    save_store_to_disk()
    logger.info("Created vector store with %d chunks and %d vocabulary terms", len(documents), len(vocabulary))


def search(query: str, top_k: int = 5) -> List[str]:
    """Retrieve top-k most relevant document chunks for a query string."""
    global documents, document_vectors, idf, vocabulary

    # If memory was cleared (e.g. Render spin up), attempt disk restoration
    if not documents:
        load_store_from_disk()

    if not documents:
        logger.warning("Vector store is empty. No documents to search.")
        return []

    query_tokens = tokenize(query)
    if not query_tokens:
        return documents[:top_k]

    # Compute query TF-IDF vector
    query_tf = Counter(query_tokens)
    q_len = max(1, len(query_tokens))
    query_vec = {t: (count / q_len) * idf.get(t, 1.0) for t, count in query_tf.items()}

    # Compute cosine similarity
    scores = []
    q_norm = math.sqrt(sum(val ** 2 for val in query_vec.values())) or 1.0

    for idx, doc_vec in enumerate(document_vectors):
        dot_product = sum(query_vec[t] * doc_vec[t] for t in query_tokens if t in doc_vec)
        doc_norm = math.sqrt(sum(val ** 2 for val in doc_vec.values())) or 1.0
        score = dot_product / (q_norm * doc_norm)
        scores.append((idx, score))

    # Sort descending
    scores.sort(key=lambda x: x[1], reverse=True)

    # If best score is > 0, return top matches
    top_indices = [idx for idx, s in scores if s > 0][:top_k]

    # Fallback: if no exact TF-IDF match, check substring or return first chunks
    if not top_indices:
        query_words = set(query.lower().split())
        fallback_scored = []
        for idx, doc in enumerate(documents):
            overlap = sum(1 for w in query_words if w in doc.lower())
            fallback_scored.append((idx, overlap))
        fallback_scored.sort(key=lambda x: x[1], reverse=True)
        top_indices = [idx for idx, ov in fallback_scored if ov > 0][:top_k]

    if not top_indices:
        top_indices = list(range(min(top_k, len(documents))))

    return [documents[i] for i in top_indices]


# Compatibility alias
search_vector_store = search