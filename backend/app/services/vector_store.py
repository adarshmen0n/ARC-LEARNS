import re
import math
from collections import Counter

# ============================================================
# LIGHTWEIGHT VECTOR STORE
# No PyTorch
# No Sentence Transformers
# No FAISS
# No NumPy
#
# Designed for low-memory deployment such as Render Free.
# ============================================================

documents = []
document_vectors = []
idf = {}
vocabulary = set()


# ============================================================
# TEXT TOKENIZATION
# ============================================================

def tokenize(text):
    return re.findall(r"[a-zA-Z0-9]+", text.lower())


# ============================================================
# CREATE TF-IDF VECTOR STORE
# ============================================================

def create_vector_store(chunks):

    global documents
    global document_vectors
    global idf
    global vocabulary

    documents = []
    document_vectors = []
    idf = {}
    vocabulary = set()

    # Clean chunks
    for chunk in chunks:

        if not chunk:
            continue

        chunk = str(chunk).strip()

        if chunk:
            documents.append(chunk)

    if not documents:
        return

    # --------------------------------------------------------
    # Tokenize documents
    # --------------------------------------------------------

    tokenized_documents = []

    for document in documents:

        tokens = tokenize(document)

        tokenized_documents.append(tokens)

        vocabulary.update(tokens)

    total_documents = len(documents)

    # --------------------------------------------------------
    # Calculate IDF
    # --------------------------------------------------------

    document_frequency = Counter()

    for tokens in tokenized_documents:

        unique_tokens = set(tokens)

        for token in unique_tokens:
            document_frequency[token] += 1

    for token in vocabulary:

        df = document_frequency[token]

        idf[token] = math.log(
            (total_documents + 1) / (df + 1)
        ) + 1

    # --------------------------------------------------------
    # Create TF-IDF vectors
    # --------------------------------------------------------

    for tokens in tokenized_documents:

        counts = Counter(tokens)

        total_words = len(tokens)

        vector = {}

        if total_words == 0:
            document_vectors.append(vector)
            continue

        for token, count in counts.items():

            tf = count / total_words

            vector[token] = tf * idf.get(token, 1.0)

        # Normalize vector
        magnitude = math.sqrt(
            sum(value * value for value in vector.values())
        )

        if magnitude > 0:

            for token in vector:

                vector[token] /= magnitude

        document_vectors.append(vector)


# ============================================================
# COSINE SIMILARITY
# ============================================================

def cosine_similarity(query_vector, document_vector):

    if not query_vector or not document_vector:
        return 0.0

    score = 0.0

    for token, value in query_vector.items():

        if token in document_vector:

            score += value * document_vector[token]

    return score


# ============================================================
# SEARCH
# ============================================================

def search(query):

    if not documents or not document_vectors:
        return []

    if not query or not query.strip():
        return []

    # --------------------------------------------------------
    # Create query vector
    # --------------------------------------------------------

    tokens = tokenize(query)

    if not tokens:
        return []

    counts = Counter(tokens)

    total_words = len(tokens)

    query_vector = {}

    for token, count in counts.items():

        if token not in vocabulary:
            continue

        tf = count / total_words

        query_vector[token] = (
            tf * idf.get(token, 1.0)
        )

    # Normalize query vector
    magnitude = math.sqrt(
        sum(value * value for value in query_vector.values())
    )

    if magnitude > 0:

        for token in query_vector:

            query_vector[token] /= magnitude

    # --------------------------------------------------------
    # Calculate similarity
    # --------------------------------------------------------

    scored_documents = []

    for index, document_vector in enumerate(document_vectors):

        score = cosine_similarity(
            query_vector,
            document_vector
        )

        scored_documents.append(
            (score, index)
        )

    # --------------------------------------------------------
    # Sort by highest similarity
    # --------------------------------------------------------

    scored_documents.sort(
        key=lambda item: item[0],
        reverse=True
    )

    # --------------------------------------------------------
    # Return top results
    # --------------------------------------------------------

    results = []
    seen = set()

    for score, index in scored_documents[:5]:

        if score <= 0:
            continue

        document = documents[index].strip()

        if not document:
            continue

        if document in seen:
            continue

        seen.add(document)

        results.append(document)

    return results[:3]