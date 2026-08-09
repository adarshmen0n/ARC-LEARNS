from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

model = SentenceTransformer("all-MiniLM-L6-v2")

index = None
documents = []


def create_vector_store(chunks):

    global index, documents

    documents = chunks

    embeddings = model.encode(chunks)

    embeddings = np.array(embeddings).astype("float32")

    dimension = embeddings.shape[1]

    index = faiss.IndexFlatL2(dimension)

    index.add(embeddings)


def search(query):

    global index, documents

    if index is None or len(documents) == 0:
        return []

    query_embedding = model.encode([query])

    query_embedding = np.array(query_embedding).astype("float32")

    number_of_results = min(5, len(documents))

    distances, indices = index.search(
        query_embedding,
        number_of_results
    )

    results = []
    seen = set()

    for i in indices[0]:

        if i < 0 or i >= len(documents):
            continue

        document = documents[i].strip()

        if document == "":
            continue

        if document in seen:
            continue

        seen.add(document)

        results.append(document)

    return results[:3]