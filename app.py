"""
RAG Study Assistant — Streamlit UI
Handles both ingestion of notes and answering questions.
"""

import os
import streamlit as st
from src import config, graph_engine, vector_engine
from src.chunker import chunk_document
from src.pipeline import run_query
from src.gemini_client import generate_json

# ── page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="RAG Study Assistant",
    page_icon="🧠",
    layout="wide",
)

# ── load graph once per session ───────────────────────────────────────────────
if "graph_loaded" not in st.session_state:
    graph_engine.load_graph()
    st.session_state["graph_loaded"] = True


# ── helper: ingest all markdown files from raw_notes ─────────────────────────
def ingest_notes():
    notes_dir = config.RAW_NOTES_DIR
    files = [f for f in os.listdir(notes_dir) if f.endswith(".md") or f.endswith(".txt")]
    if not files:
        return 0, []

    # Clear old data before ingesting to prevent duplication
    graph_engine.clear()
    vector_engine.clear()

    ingested = []
    for filename in files:
        filepath = os.path.join(notes_dir, filename)
        with open(filepath, "r", encoding="utf-8") as fh:
            text = fh.read()

        chunks = chunk_document(text, source_file=filename)
        vector_engine.upsert_chunks(chunks)

        triples = []
        for chunk in chunks:
            triples.extend(graph_engine.extract_triples(chunk.text, chunk.chunk_id))
        graph_engine.add_triples(triples)
        ingested.append((filename, len(chunks), len(triples)))

    graph_engine.save_graph()
    return len(files), ingested


# ── sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🧠 RAG Assistant")
    st.markdown("---")

    st.subheader("📚 Knowledge Base")
    stats = vector_engine.collection.count()
    gstats = graph_engine.graph_stats()
    col1, col2 = st.columns(2)
    col1.metric("Chunks", stats)
    col2.metric("Graph nodes", gstats["nodes"])

    st.markdown("---")
    st.subheader("⚙️ Ingest Notes")
    notes_dir = config.RAW_NOTES_DIR
    note_files = [f for f in os.listdir(notes_dir) if f.endswith((".md", ".txt"))] if os.path.isdir(notes_dir) else []
    st.caption(f"{len(note_files)} file(s) in `data/raw_notes/`")
    for f in note_files:
        st.markdown(f"- `{f}`")

    if st.button("▶ Ingest all notes", use_container_width=True, type="primary"):
        with st.spinner("Ingesting…"):
            count, details = ingest_notes()
        if count == 0:
            st.warning("No `.md` or `.txt` files found in `data/raw_notes/`.")
        else:
            st.success(f"✅ Ingested {count} file(s)!")
            for fname, n_chunks, n_triples in details:
                st.caption(f"`{fname}` → {n_chunks} chunks, {n_triples} triples")
            st.rerun()

    st.markdown("---")
    st.caption("Add your own `.md` notes to `data/raw_notes/` then click Ingest.")


# ── main chat area ────────────────────────────────────────────────────────────
st.title("🧠 RAG Study Assistant")
st.markdown("Ask anything about your study notes. The assistant uses **vector search** and a **knowledge graph** to answer.")

if stats == 0:
    st.warning("⚠️ Knowledge base is empty! Add notes to `data/raw_notes/` and click **Ingest all notes** in the sidebar.")

# keep chat history
if "messages" not in st.session_state:
    st.session_state["messages"] = []

for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Ask a question about your notes…"):
    st.session_state["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking…"):
            result = run_query(prompt)

        answer = result["answer"]
        route = result["route"]
        st.markdown(answer)

        # ── debug expander ────────────────────────────────────────────────
        with st.expander(f"🔍 Debug — Route: `{route}`", expanded=False):
            if "vector_chunks" in result:
                st.subheader("Vector chunks used")
                for c in result["vector_chunks"]:
                    st.markdown(f"**`{c['chunk_id']}`** (dist `{c['distance']:.3f}`) — *{c['metadata'].get('source_file','')}*")
                    st.code(c["text"][:400])
            if "graph_edges" in result:
                st.subheader("Graph edges used")
                for e in result["graph_edges"]:
                    st.markdown(f"`{e['source']}` —[**{e['relation']}**]→ `{e['target']}`")
            st.subheader("Full context sent to Gemini")
            st.text(result.get("context_used", "(empty)"))

    st.session_state["messages"].append({"role": "assistant", "content": answer})