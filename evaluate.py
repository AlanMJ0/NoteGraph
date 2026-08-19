# RAG pipeline evaluation
# This script checks how well the system is working.
# Run it with: python evaluate.py
# Run it again after building each new part -- it will tell you what's
# missing so far, and later, how accurate your router and retrieval are.

import json
from src import config


def load_eval_set():
    file = open(config.EVAL_SET_PATH, "r")
    data = json.load(file)
    file.close()
    return data


def evaluate_router(eval_set):
    # We import router.py here, inside the function, instead of at the
    # top of the file. That way this script still runs even before
    # router.py exists -- it'll just skip this check.
    try:
        from src.router import classify_intent
    except ImportError:
        return {"status": "skipped", "reason": "router.py not built yet"}

    correct_count = 0
    total_count = len(eval_set)

    for item in eval_set:
        predicted_route = classify_intent(item["question"])
        expected_route = item["expected_route"]
        if predicted_route == expected_route:
            correct_count = correct_count + 1

    if total_count == 0:
        accuracy = 0
    else:
        accuracy = correct_count / total_count

    return {"status": "ok", "accuracy": accuracy}


def evaluate_vector_retrieval(eval_set):
    try:
        from src.vector_engine import query_similarity
    except ImportError:
        return {"status": "skipped", "reason": "vector_engine.py not built yet"}

    hit_count = 0
    checked_count = 0

    for item in eval_set:
        if item["expected_route"] not in ("VECTOR", "HYBRID"):
            continue

        checked_count = checked_count + 1
        retrieved_chunks = query_similarity(item["question"], top_k=config.VECTOR_TOP_K)

        # Combine all retrieved text into one lowercase string, so we can
        # check if the expected keywords show up anywhere in it.
        combined_text = ""
        for chunk in retrieved_chunks:
            combined_text = combined_text + " " + chunk["text"].lower()

        hint_words = item["gold_source_hint"].lower().split()
        matched_words = 0
        for word in hint_words:
            if word in combined_text:
                matched_words = matched_words + 1

        # Count it as a hit if at least half the hint words showed up.
        if matched_words >= len(hint_words) / 2:
            hit_count = hit_count + 1

    if checked_count == 0:
        hit_rate = 0
    else:
        hit_rate = hit_count / checked_count

    return {"status": "ok", "hit_rate": hit_rate}


def evaluate_graph_retrieval(eval_set):
    try:
        from src.graph_engine import get_neighbors
    except ImportError:
        return {"status": "skipped", "reason": "graph_engine.py not built yet"}

    hit_count = 0
    checked_count = 0

    for item in eval_set:
        if item["expected_route"] not in ("GRAPH", "HYBRID"):
            continue

        checked_count = checked_count + 1

        # NOTE: just like pipeline.py's GRAPH route, this passes the raw
        # question straight into get_neighbors(). It will only find edges
        # if the question happens to closely match an actual concept name
        # in the graph. Once you improve pipeline.py to extract the concept
        # first, come back and update this the same way so the two stay
        # consistent with each other.
        retrieved_edges = get_neighbors(item["question"])

        combined_text = ""
        for edge in retrieved_edges:
            combined_text = combined_text + " " + edge["source"].lower()
            combined_text = combined_text + " " + edge["relation"].lower()
            combined_text = combined_text + " " + edge["target"].lower()

        hint_words = item["gold_source_hint"].lower().split()
        matched_words = 0
        for word in hint_words:
            if word in combined_text:
                matched_words = matched_words + 1

        if matched_words >= len(hint_words) / 2:
            hit_count = hit_count + 1

    if checked_count == 0:
        hit_rate = 0
    else:
        hit_rate = hit_count / checked_count

    return {"status": "ok", "hit_rate": hit_rate}


def evaluate_hybrid_retrieval(eval_set):
    # This one needs all three pieces working together, so it needs all
    # three imports to succeed before it can run.
    try:
        from src.vector_engine import query_similarity
        from src.graph_engine import get_neighbors
        from src.merge import merge_context
    except ImportError:
        return {"status": "skipped", "reason": "vector_engine.py, graph_engine.py, or merge.py not built yet"}

    hit_count = 0
    checked_count = 0

    for item in eval_set:
        # Only HYBRID questions get tested here -- this is the check that
        # was missing before. evaluate_vector_retrieval and
        # evaluate_graph_retrieval each test one engine alone, even on
        # HYBRID questions. This function is the only one that actually
        # calls merge_context(), which is what pipeline.py really uses
        # for HYBRID questions.
        if item["expected_route"] != "HYBRID":
            continue

        checked_count = checked_count + 1

        retrieved_chunks = query_similarity(item["question"], top_k=config.VECTOR_TOP_K)
        retrieved_edges = get_neighbors(item["question"])
        combined_context = merge_context(retrieved_chunks, retrieved_edges)

        combined_text = combined_context.lower()

        hint_words = item["gold_source_hint"].lower().split()
        matched_words = 0
        for word in hint_words:
            if word in combined_text:
                matched_words = matched_words + 1

        if matched_words >= len(hint_words) / 2:
            hit_count = hit_count + 1

    if checked_count == 0:
        hit_rate = 0
    else:
        hit_rate = hit_count / checked_count

    return {"status": "ok", "hit_rate": hit_rate}


def main():
    eval_set = load_eval_set()
    print("Loaded", len(eval_set), "eval questions.")
    print("")

    router_result = evaluate_router(eval_set)
    print("=== Router accuracy ===")
    if router_result["status"] == "ok":
        print("Accuracy:", round(router_result["accuracy"] * 100), "%")
    else:
        print(router_result["reason"])

    print("")

    vector_result = evaluate_vector_retrieval(eval_set)
    print("=== Vector retrieval hit rate ===")
    if vector_result["status"] == "ok":
        print("Hit rate:", round(vector_result["hit_rate"] * 100), "%")
    else:
        print(vector_result["reason"])

    print("")

    graph_result = evaluate_graph_retrieval(eval_set)
    print("=== Graph retrieval hit rate ===")
    if graph_result["status"] == "ok":
        print("Hit rate:", round(graph_result["hit_rate"] * 100), "%")
    else:
        print(graph_result["reason"])

    print("")

    hybrid_result = evaluate_hybrid_retrieval(eval_set)
    print("=== Hybrid retrieval hit rate ===")
    if hybrid_result["status"] == "ok":
        print("Hit rate:", round(hybrid_result["hit_rate"] * 100), "%")
    else:
        print(hybrid_result["reason"])


if __name__ == "__main__":
    main()