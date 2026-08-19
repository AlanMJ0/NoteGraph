# Vector database engine
# This file handles everything related to storing and searching chunks
# using ChromaDB, our vector database.

import chromadb
from pathlib import Path
from chromadb.utils.embedding_functions.onnx_mini_lm_l6_v2 import ONNXMiniLM_L6_V2
from src import config
from src.gemini_client import generate_json

# Monkey-patch ChromaDB's hardcoded ONNX model download path to use our D drive cache.
# This prevents it from falling back to C:\Users\...\.cache\chroma\onnx_models.
ONNXMiniLM_L6_V2.DOWNLOAD_PATH = Path(config.CHROMA_CACHE_DIR) / "onnx_models" / ONNXMiniLM_L6_V2.MODEL_NAME

# Set up the database connection once, here at the top, so every function
# below can reuse it. We pass Settings to redirect the ONNX model cache
# from the default C:\Users\..\.cache\chroma to our project's D: drive folder.
db_client = chromadb.PersistentClient(
    path=config.VECTOR_DB_DIR,
    settings=chromadb.Settings(chroma_cache_dir=config.CHROMA_CACHE_DIR),
)
collection = db_client.get_or_create_collection(name=config.VECTOR_COLLECTION_NAME)

def clear():
    global collection
    # Safely delete all items without dropping the collection itself.
    # Dropping the collection on Windows can cause race conditions and missing chunks.
    result = collection.get()
    if result and result.get("ids"):
        collection.delete(ids=result["ids"])


def upsert_chunks(chunks):
    """
    Saves a list of Chunk objects into the database. "Upsert" means:
    if a chunk with this ID already exists, update it; otherwise, add it.
    """
    if len(chunks) == 0:
        return

    ids = []
    texts = []
    metadatas = []

    for chunk in chunks:
        ids.append(chunk.chunk_id)
        texts.append(chunk.text)
        metadatas.append(chunk.to_metadata())

    collection.upsert(ids=ids, documents=texts, metadatas=metadatas)


def raw_query(query_text, n_results):
    """
    Asks ChromaDB for the n_results chunks most similar to query_text,
    based on meaning (not just matching words).
    """
    results = collection.query(query_texts=[query_text], n_results=n_results)

    output = []
    number_found = len(results["ids"][0])
    for i in range(number_found):
        output.append({
            "chunk_id": results["ids"][0][i],
            "text": results["documents"][0][i],
            "metadata": results["metadatas"][0][i],
            "distance": results["distances"][0][i],
        })

    return output


def rerank(query_text, candidates, top_k):
    """
    Takes a bigger list of candidate chunks and asks Gemini to score how
    relevant each one really is, then keeps only the best top_k. This helps
    because "similar wording" (what ChromaDB measures) isn't always the
    same as "actually answers the question."
    """
    if len(candidates) <= top_k:
        return candidates

    # Build a numbered list of the candidate texts to show Gemini.
    listing = ""
    for i in range(len(candidates)):
        preview = candidates[i]["text"][:400]
        listing = listing + "[" + str(i) + "] " + preview + "\n"

    prompt = (
        "Query: " + query_text + "\n\n"
        "Candidate passages:\n" + listing + "\n"
        "Score each passage's relevance to the query from 0 (irrelevant) to 10 "
        "(directly answers it). Return ONLY a JSON array of integers, in the same "
        "order as the passages, e.g. [7, 2, 9]."
    )

    try:
        scores = generate_json(prompt, model=config.MODEL_FAST)
    except Exception as error:
        # If re-ranking fails for any reason, just fall back to the
        # original order instead of crashing the whole search.
        print("Rerank failed, using original order:", error)
        return candidates[:top_k]

    # Pair each candidate with its score, then sort by score, highest first.
    paired = list(zip(candidates, scores))
    paired.sort(key=lambda pair: pair[1], reverse=True)

    best_candidates = []
    for chunk, score in paired[:top_k]:
        best_candidates.append(chunk)

    return best_candidates


def query_similarity(query_text, top_k=None, use_rerank=True):
    """
    The main function other files will call. Returns the top_k chunks
    most relevant to query_text.
    """
    if top_k is None:
        top_k = config.VECTOR_TOP_K

    if use_rerank:
        candidates = raw_query(query_text, config.VECTOR_RERANK_CANDIDATES)
        return rerank(query_text, candidates, top_k)
    else:
        return raw_query(query_text, top_k)


# Quick manual test -- run with: python -m src.vector_engine
if __name__ == "__main__":
    from src.chunker import chunk_document

    sample_text = """# Sorting
## QuickSort
QuickSort has average time complexity O(n log n) and worst case O(n^2).
## MergeSort
MergeSort always runs in O(n log n) regardless of input order.
"""
    chunks = chunk_document(sample_text, "sample.md")
    upsert_chunks(chunks)

    results = query_similarity("What is the time complexity of QuickSort?", top_k=2, use_rerank=False)
    for result in results:
        print(result["chunk_id"], result["distance"], result["text"][:60])