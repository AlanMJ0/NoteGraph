# Result merging logic
# This file combines results from the vector engine and the graph engine
# into one block of text we can hand to Gemini for the final answer.
# We keep a character budget so the combined text doesn't get too long,
# and we label each part clearly so it's obvious what kind of information
# it is (a graph relationship vs. an exact passage of text).

from src import config


def format_vector_context(chunks, char_budget):
    lines = []
    used_so_far = 0

    for chunk in chunks:
        entry = "[Source: " + chunk["metadata"]["source_file"] + ", chunk " + chunk["chunk_id"] + "]\n"
        entry = entry + chunk["text"] + "\n"

        if used_so_far + len(entry) > char_budget:
            break

        lines.append(entry)
        used_so_far = used_so_far + len(entry)

    return "\n".join(lines)


def format_graph_context(edges, char_budget):
    lines = []
    used_so_far = 0

    for edge in edges:
        entry = edge["source"] + " --[" + edge["relation"] + "]--> " + edge["target"]

        if used_so_far + len(entry) + 1 > char_budget:
            break

        lines.append(entry)
        used_so_far = used_so_far + len(entry) + 1

    return "\n".join(lines)


def merge_context(vector_chunks, graph_edges):
    """
    Combines vector chunks and graph edges into one labeled block of text,
    splitting the total character budget between them according to
    config.HYBRID_VECTOR_SHARE and config.HYBRID_GRAPH_SHARE.
    """
    total_budget = config.MAX_MERGED_CONTEXT_CHARS
    graph_budget = int(total_budget * config.HYBRID_GRAPH_SHARE)
    vector_budget = int(total_budget * config.HYBRID_VECTOR_SHARE)

    graph_text = format_graph_context(graph_edges, graph_budget)
    vector_text = format_vector_context(vector_chunks, vector_budget)

    sections = []
    if graph_text != "":
        sections.append("=== Concept Relationships (from knowledge graph) ===\n" + graph_text)
    if vector_text != "":
        sections.append("=== Relevant Passages (from notes) ===\n" + vector_text)

    return "\n\n".join(sections)


# Quick manual test -- run with: python -m src.merge
if __name__ == "__main__":
    fake_chunks = [
        {"chunk_id": "abc123", "metadata": {"source_file": "notes.md"}, "text": "QuickSort has average complexity O(n log n)."}
    ]
    fake_edges = [
        {"source": "Recursion", "relation": "requires_understanding_of", "target": "Function Calls"}
    ]
    print(merge_context(fake_chunks, fake_edges))