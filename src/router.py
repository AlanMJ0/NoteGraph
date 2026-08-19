# Query routing logic
# Decides whether a question is best answered by the vector store (semantic
# similarity), the knowledge graph (relationships / "how does X connect to Y"),
# or both (hybrid). The logic here is intentionally simple — keyword heuristics
# work well enough for a study assistant and are easy to extend later.

GRAPH_KEYWORDS = [
    "relate", "relation", "relationship",
    "connect", "connection",
    "link", "linked",
    "depend", "dependency",
    "difference between", "compare", "comparison",
    "versus", "vs",
    "how does", "how do",
    "why does", "why do",
    "cause", "effect",
    "graph", "knowledge graph",
]

HYBRID_KEYWORDS = [
    "explain", "overview", "summarize", "summary",
    "describe", "tell me about",
    "what is", "what are",
]


def classify_intent(question: str) -> str:
    """
    Returns one of three routing strings:
      "GRAPH"  — question is about relationships / connections
      "VECTOR" — question is a factual / detail lookup
      "HYBRID" — question needs both broad context and relational info
    """
    lowered = question.lower()

    # Check for graph-specific relationship keywords first (highest priority).
    for keyword in GRAPH_KEYWORDS:
        if keyword in lowered:
            return "GRAPH"

    # Check for broad explanatory questions that benefit from hybrid retrieval.
    for keyword in HYBRID_KEYWORDS:
        if keyword in lowered:
            return "HYBRID"

    # Default: straight vector similarity search.
    return "VECTOR"
