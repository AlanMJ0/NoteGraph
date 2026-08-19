import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Which Gemini models to use. Change these to match whatever you have access to.
MODEL_FAST = "gemini-3.1-flash-lite"
MODEL_STRONG = "gemini-3.6-flash"

# How many times to retry an API call if it fails, and how long to wait between tries.
MAX_RETRIES = 4
BASE_BACKOFF_SECONDS = 1.5

# File paths. os.path.join just glues folder names together correctly
RAW_NOTES_DIR = os.path.join("data", "raw_notes")
GRAPH_PATH = os.path.join("data", "knowledge_graph.json")
EVAL_SET_PATH = os.path.join("data", "eval_set.json")
VECTOR_DB_DIR = "vectordb"
VECTOR_COLLECTION_NAME = "notes"
CHROMA_CACHE_DIR = os.getenv("CHROMA_CACHE_DIR", r"D:\RAG\cache\chroma")

# Chunking settings
MAX_CHUNK_CHARS = 1200
CHUNK_OVERLAP_CHARS = 150

# Vector search settings
VECTOR_TOP_K = 5
VECTOR_RERANK_CANDIDATES = 20

# Graph search settings
GRAPH_MAX_HOPS = 2

# Entity resolution: how similar two names need to look before we
# guess they mean the same thing, from 0 to 100.
FUZZY_MATCH_THRESHOLD = 85

# Hybrid merge settings
HYBRID_VECTOR_SHARE = 0.6
HYBRID_GRAPH_SHARE = 0.4
MAX_MERGED_CONTEXT_CHARS = 6000