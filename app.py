"""
RAG Study Assistant — Streamlit UI (Connected via FastAPI Backend)
"""

import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000"

# ── page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="NoteGraph RAG Assistant",
    page_icon="🧠",
    layout="wide",
)

# Initialize Session State
if "messages" not in st.session_state:
    st.session_state["messages"] = []

if "session_id" not in st.session_state:
    st.session_state["session_id"] = None


# Helper function to check API availability
def check_api_health():
    try:
        res = requests.get(f"{API_URL}/health", timeout=2)
        return res.status_code == 200
    except Exception:
        return False


api_online = check_api_health()

# ── sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🧠 NoteGraph")
    st.markdown("---")

    if not api_online:
        st.error("⚠️ FastAPI backend offline! Run: `uvicorn api.main:app --reload`")
    else:
        st.success("🟢 Connected to FastAPI backend")

    st.markdown("---")
    st.subheader("⚙️ Session Controls")
    if st.button("➕ New Chat Session", use_container_width=True):
        st.session_state["messages"] = []
        st.session_state["session_id"] = None
        st.rerun()

    if st.session_state["session_id"]:
        st.caption(f"Active Session ID: `{st.session_state['session_id']}`")


# ── main chat area ────────────────────────────────────────────────────────────
st.title("🧠 NoteGraph RAG Assistant")
st.markdown("Ask technical questions from your study notes. Powered by **Vector Search**, **Knowledge Graph**, and **PostgreSQL**.")

# Display Chat History
for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat Input Handler
if prompt := st.chat_input("Ask a question about your notes…", disabled=not api_online):
    # Append user question to UI
    st.session_state["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Process via FastAPI Backend
    with st.chat_message("assistant"):
        with st.spinner("Thinking…"):
            try:
                payload = {
                    "question": prompt,
                    "session_id": st.session_state["session_id"]
                }
                
                response = requests.post(f"{API_URL}/chat/query", json=payload)
                
                if response.status_code == 200:
                    data = response.json()
                    answer = data["answer"]
                    route = data["route"]
                    concept = data.get("extracted_concept")
                    latency = data.get("latency_ms")
                    
                    # Store session ID returned by backend
                    st.session_state["session_id"] = data["session_id"]

                    st.markdown(answer)

                    # Debug expander showing API metadata
                    with st.expander(f"🔍 Route: `{route}` | Latency: `{latency}ms`", expanded=False):
                        st.markdown(f"**Extracted Concept:** `{concept}`")
                        st.markdown(f"**Saved Session ID:** `{data['session_id']}`")
                        
                    st.session_state["messages"].append({"role": "assistant", "content": answer})
                else:
                    st.error(f"API Error ({response.status_code}): {response.text}")

            except Exception as e:
                st.error(f"Failed to communicate with FastAPI backend: {e}")