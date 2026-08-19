# RAG pipeline orchestration
# This is the file that ties everything together: it takes a question,
# decides which engine(s) to use, gathers the context, and asks Gemini
# to write the final answer.

from src import config, graph_engine, vector_engine, merge
from src.router import classify_intent
from src.gemini_client import generate_text

ANSWER_INSTRUCTIONS = """You are a study assistant. Answer the user's question using ONLY the
provided context. If the context doesn't contain enough information to answer confidently,
say so explicitly rather than guessing.

After your answer, add a "Sources:" line listing which chunk files or graph relationships
you used."""


def answer_from_context(question, context):
    prompt = "Context:\n" + context + "\n\nQuestion: " + question
    return generate_text(prompt, model=config.MODEL_STRONG, system_instruction=ANSWER_INSTRUCTIONS)


def run_query(question):
    """
    The main function app.py and evaluate.py will call.
    Returns a dictionary with the route taken, the raw context retrieved,
    and the final answer -- so the UI can show all of it, not just the answer.
    """
    route = classify_intent(question)
    debug_info = {"route": route}

    if route == "VECTOR":
        chunks = vector_engine.query_similarity(question)
        context = merge.format_vector_context(chunks, config.MAX_MERGED_CONTEXT_CHARS)
        debug_info["vector_chunks"] = chunks

    elif route == "GRAPH":
        # NOTE: this passes the raw question straight into get_neighbors(),
        # which only works well if the question happens to closely match an
        # actual concept name in the graph. A good improvement to try later:
        # first ask Gemini to pull out the core concept from the question,
        # then look THAT up instead.
        edges = graph_engine.get_neighbors(question)
        context = merge.format_graph_context(edges, config.MAX_MERGED_CONTEXT_CHARS)
        debug_info["graph_edges"] = edges

    else:  # route == "HYBRID"
        chunks = vector_engine.query_similarity(question)
        edges = graph_engine.get_neighbors(question)
        context = merge.merge_context(chunks, edges)
        debug_info["vector_chunks"] = chunks
        debug_info["graph_edges"] = edges

    if context.strip() == "":
        answer = "I don't have enough information in the knowledge base to answer that."
    else:
        answer = answer_from_context(question, context)

    debug_info["answer"] = answer
    debug_info["context_used"] = context
    return debug_info


# Quick manual test -- run with: python -m src.pipeline
if __name__ == "__main__":
    result = run_query("What is the time complexity of QuickSort?")
    print("Route:", result["route"])
    print("Answer:", result["answer"])