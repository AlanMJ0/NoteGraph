# 🧠 NoteGraph: Hybrid RAG Study Assistant

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Google Gemini API](https://img.shields.io/badge/Gemini-3.6%20Flash-orange.svg)](https://ai.google.dev/)
[![Vector DB](https://img.shields.io/badge/ChromaDB-v0.5%2B-purple.svg)](https://www.trychroma.com/)
[![Graph Framework](https://img.shields.io/badge/NetworkX-v3.3%2B-green.svg)](https://networkx.org/)
[![Streamlit UI](https://img.shields.io/badge/Streamlit-v1.37%2B-FF4B4B.svg)](https://streamlit.io/)

**NoteGraph** is a hybrid Retrieval-Augmented Generation (RAG) study assistant designed to answer complex questions over markdown notes and technical documentation. By fusing **dense vector search** with an LLM-extracted **Knowledge Graph**, NoteGraph delivers precise factual lookups alongside deep relational reasoning and prerequisite mapping.

---

## 🌟 Key Features

- 🔍 **Dense Vector Retrieval + LLM Reranking**: Efficient semantic search with ChromaDB (`ONNXMiniLM_L6_V2` embeddings) paired with Gemini-powered candidate re-ranking for ultra-precise context selection.
- 🕸️ **Knowledge Graph Engine**: Automated extraction of `(source, relation, target)` entity triples using Gemini, NetworkX graph storage, fuzzy name normalization, and LLM entity resolution.
- 🔀 **Adaptive Intent Routing**: Automatically routes user queries to `VECTOR` (factual details), `GRAPH` (connections/relationships), or `HYBRID` (broad synthesis) pipelines.
- ⚡ **Hybrid Context Fusion**: Combines vector chunks and graph edges seamlessly into unified prompt context window using Reciprocal Rank Fusion principles.
- 🖥️ **Interactive Streamlit UI**: Sleek chat interface featuring real-time knowledge base statistics, single-click note ingestion, and full transparency via interactive debug expanders.
- 📊 **Automated Benchmark Suite**: Built-in evaluation pipeline testing router accuracy and retrieval hit rates across vector, graph, and hybrid modes.

---

## 🏗️ System Architecture

```
                                  ┌──────────────────────────┐
                                  │   User Query / Question  │
                                  └─────────────┬────────────┘
                                                │
                                      ┌─────────▼────────┐
                                      │   Query Router   │
                                      └────┬────┬────┬───┘
                                           │    │    │
                  ┌────────────────────────┘    │    └────────────────────────┐
                  │                             │                             │
          [ VECTOR Route ]              [ HYBRID Route ]               [ GRAPH Route ]
                  │                             │                             │
      ┌───────────▼───────────┐                 │                 ┌───────────▼───────────┐
      │ ChromaDB Vector Search│                 │                 │ NetworkX Graph Search │
      └───────────┬───────────┘                 │                 └───────────┬───────────┘
                  │                             │                             │
      ┌───────────▼───────────┐                 │                 ┌───────────▼───────────┐
      │  Gemini Re-ranking    │                 │                 │ Multi-Hop Traversal   │
      └───────────┬───────────┘                 │                 └───────────┬───────────┘
                  │                             │                             │
                  └─────────────────────┐       │       ┌─────────────────────┘
                                        ▼       ▼       ▼
                                ┌───────────────────────────────┐
                                │ Hybrid Context Fusion & Merge │
                                └───────────────┬───────────────┘
                                                │
                                ┌───────────────▼───────────────┐
                                │ Gemini Generation & Citations │
                                └───────────────────────────────┘
```

---

## 📁 Repository Structure

```
NoteGraph/
├── app.py                  # Streamlit web application & chat interface
├── evaluate.py             # RAG evaluation benchmark script
├── requirements.txt        # Python package dependencies
├── .env                    # Environment variables (API Keys & configuration)
├── .gitignore              # Git ignore configuration
├── README.md               # Project documentation
│
├── data/                   # Persistent data directory
│   ├── raw_notes/          # Markdown (.md) and text (.txt) study notes
│   ├── knowledge_graph.json# Saved NetworkX knowledge graph structure
│   └── eval_set.json       # Benchmark questions & expected evaluation criteria
│
├── vectordb/               # Persistent ChromaDB vector database directory
│
└── src/                    # Source code package
    ├── config.py           # Centralized configuration settings & constants
    ├── chunker.py          # Header-aware document chunking engine
    ├── gemini_client.py    # Google GenAI API client & retry logic wrapper
    ├── vector_engine.py    # Vector indexing, retrieval & Gemini reranking
    ├── graph_engine.py     # Triple extraction, entity resolution & graph search
    ├── router.py           # Intent classification heuristic router
    ├── merge.py            # Hybrid context formatting and merge logic
    └── pipeline.py         # End-to-end RAG orchestrator
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10 or higher
- A **Google Gemini API Key** ([Get your API key here](https://aistudio.google.com/))

### Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/AlanMJ0/NoteGraph.git
   cd NoteGraph
   ```

2. **Create and Activate a Virtual Environment**
   - **Windows (PowerShell):**
     ```powershell
     python -m venv .venv
     .\.venv\Scripts\Activate.ps1
     ```
   - **macOS / Linux:**
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables**
   Create a `.env` file in the root directory:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

---

## 💡 Usage

### 1. Running the Web Application

Launch the Streamlit interface:
```bash
streamlit run app.py
```

- Add your `.md` or `.txt` notes to `data/raw_notes/`.
- Open your browser at `http://localhost:8501`.
- Click **▶ Ingest all notes** in the sidebar to process document chunks and extract graph relationships.
- Start asking questions in the chat! Expand the **🔍 Debug** panel under any response to inspect vector distances, graph paths, and raw prompt context.

### 2. Running Pipeline Programmatically

You can invoke the RAG orchestrator directly from Python:

```python
from src.pipeline import run_query

result = run_query("How does Dynamic Programming relate to Recursion?")

print("Selected Route:", result["route"])
print("Generated Answer:\n", result["answer"])
```

### 3. Evaluating Performance

Run the evaluation benchmark suite against `data/eval_set.json`:

```bash
python evaluate.py
```

Sample Evaluation Output:
```text
Loaded 10 eval questions.

=== Router accuracy ===
Accuracy: 90 %

=== Vector retrieval hit rate ===
Hit rate: 100 %

=== Graph retrieval hit rate ===
Hit rate: 85 %

=== Hybrid retrieval hit rate ===
Hit rate: 90 %
```

---

## ⚙️ Configuration Parameters

All pipeline defaults can be customized in [`src/config.py`](file:///d:/RAG/src/config.py):

| Parameter | Default | Description |
|---|---|---|
| `MODEL_FAST` | `gemini-3.1-flash-lite` | Lightweight model used for reranking & entity extraction |
| `MODEL_STRONG` | `gemini-3.6-flash` | High-capability model used for final response generation |
| `MAX_CHUNK_CHARS` | `1200` | Target maximum character size per document chunk |
| `CHUNK_OVERLAP_CHARS` | `150` | Overlap window between consecutive text chunks |
| `VECTOR_TOP_K` | `5` | Final top-K chunks passed to LLM context |
| `VECTOR_RERANK_CANDIDATES` | `20` | Initial candidate pool fetched prior to Gemini reranking |
| `GRAPH_MAX_HOPS` | `2` | Hop limit for graph relationship traversal |
| `FUZZY_MATCH_THRESHOLD` | `85` | Similarity score threshold for entity resolution |

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the [Issues page](https://github.com/AlanMJ0/NoteGraph/issues).

---

## 📜 License

Distributed under the [MIT License](LICENSE).

