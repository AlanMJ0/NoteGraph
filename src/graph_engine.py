# Knowledge graph engine
# This file builds and searches our knowledge graph: a map of concepts
# and how they relate to each other, using the networkx library.

import json
import networkx as nx
from src import config
from src.gemini_client import generate_json

# One graph object that every function below reads from and writes to.
graph = nx.DiGraph()  # DiGraph = "directed graph": edges point one way, A -> B

def clear():
    global graph
    graph.clear()


EXTRACTION_INSTRUCTIONS = """You are a knowledge-graph extraction engine for technical study notes.
Extract concept relationships as (source, relation, target) triples.

Rules:
- Only extract relationships that are explicitly stated or clearly implied by the text.
- Use short, consistent relation names in snake_case (e.g. requires_understanding_of, is_a_type_of, used_in, has_complexity, part_of).
- Concept names should be concise noun phrases (e.g. "Dynamic Programming", not "the concept of dynamic programming").
- Do not invent relationships that aren't supported by the text.
- If the text has no extractable relationships, return an empty array.

Return ONLY a JSON array in this exact format:
[{"source": "ConceptA", "relation": "relation_name", "target": "ConceptB"}]"""


def extract_triples(chunk_text, chunk_id):
    """
    Asks Gemini to find (source, relation, target) facts inside a piece of text.
    Example: "Dynamic Programming" -- requires_understanding_of --> "Recursion"
    """
    prompt = "Extract relationship triples from this text:\n\n" + chunk_text

    try:
        triples = generate_json(prompt, model=config.MODEL_FAST, system_instruction=EXTRACTION_INSTRUCTIONS)
    except Exception as error:
        print("Triple extraction failed for chunk", chunk_id, ":", error)
        return []

    if not isinstance(triples, list):
        return []

    for triple in triples:
        triple["source_chunk_id"] = chunk_id

    return triples


def normalize_name(name):
    """
    Makes a concept name easier to compare: lowercase, no extra spaces,
    dashes and underscores turned into spaces.
    "Dynamic-Programming" and "dynamic_programming " both become
    "dynamic programming".
    """
    name = name.strip().lower()
    name = name.replace("-", " ")
    name = name.replace("_", " ")
    # Collapse any repeated spaces down to one.
    words = name.split()
    return " ".join(words)


def simple_similarity(name_a, name_b):
    """
    A basic (not fancy) way to measure how similar two names are, from
    0 to 100. We check: are they identical after normalizing? Does one
    contain the other? How many words do they share?
    This isn't as accurate as a real fuzzy-matching library, but it's
    easy to read and good enough to catch obvious near-duplicates.
    """
    a = normalize_name(name_a)
    b = normalize_name(name_b)

    if a == b:
        return 100

    if a in b or b in a:
        return 90

    words_a = set(a.split())
    words_b = set(b.split())
    shared_words = words_a.intersection(words_b)

    if len(words_a) == 0 or len(words_b) == 0:
        return 0

    # What fraction of the total unique words are shared?
    total_unique_words = words_a.union(words_b)
    return int(100 * len(shared_words) / len(total_unique_words))


def resolve_entity(candidate_name, use_llm_fallback=True):
    """
    Figures out what node name we should actually use for candidate_name.
    If something very similar already exists in the graph, reuse it,
    instead of creating a near-duplicate node.
    """
    existing_nodes = list(graph.nodes)
    if len(existing_nodes) == 0:
        return candidate_name

    # Step 1: look for the best match among existing nodes using our
    # simple string similarity function.
    best_match_name = None
    best_match_score = 0

    for existing_name in existing_nodes:
        score = simple_similarity(candidate_name, existing_name)
        if score > best_match_score:
            best_match_score = score
            best_match_name = existing_name

    # Confident match: reuse the existing node.
    if best_match_score >= config.FUZZY_MATCH_THRESHOLD:
        return best_match_name

    # Step 2: if it's a "maybe" (some similarity, but not enough to be sure),
    # ask Gemini to make the judgment call instead of guessing.
    if use_llm_fallback and best_match_score >= 50:
        prompt = (
            'Does the concept "' + candidate_name + '" refer to the same thing as this '
            'existing concept: "' + best_match_name + '"?\n\n'
            'Return ONLY JSON: {"same": true} or {"same": false}'
        )
        try:
            result = generate_json(prompt, model=config.MODEL_FAST)
            if result.get("same") is True:
                return best_match_name
        except Exception as error:
            print("Entity resolution check failed:", error)

    # Not similar enough to anything existing -- treat it as a new concept.
    return candidate_name


def add_triples(triples):
    """Resolves entity names and adds the triples into the graph."""
    for triple in triples:
        source = resolve_entity(triple["source"])
        target = resolve_entity(triple["target"])

        if source not in graph:
            graph.add_node(source, type="concept")
        if target not in graph:
            graph.add_node(target, type="concept")

        graph.add_edge(
            source,
            target,
            relation_type=triple["relation"],
            source_chunk_id=triple.get("source_chunk_id", ""),
        )


def save_graph(path=None):
    if path is None:
        path = config.GRAPH_PATH
    data = nx.node_link_data(graph, edges="edges")
    file = open(path, "w")
    json.dump(data, file, indent=2)
    file.close()


def load_graph(path=None):
    global graph
    if path is None:
        path = config.GRAPH_PATH
    try:
        file = open(path, "r")
        data = json.load(file)
        file.close()
        # KeyError means the file exists but isn't a valid node-link graph
        # (e.g. it's an empty {} written before any ingestion ran).
        graph = nx.node_link_graph(data, directed=True, edges="edges")
    except (FileNotFoundError, KeyError, ValueError):
        graph = nx.DiGraph()


def graph_stats():
    node_count = graph.number_of_nodes()
    edge_count = graph.number_of_edges()
    if node_count == 0:
        avg_degree = 0
    else:
        avg_degree = round(2 * edge_count / node_count, 2)
    return {"nodes": node_count, "edges": edge_count, "avg_degree": avg_degree}


def get_neighbors(concept_name, hops=None):
    """
    Returns all edges within a few "hops" (steps) of concept_name,
    in both directions.
    """
    if hops is None:
        hops = config.GRAPH_MAX_HOPS

    resolved_name = resolve_entity(concept_name, use_llm_fallback=False)
    if resolved_name not in graph:
        return []

    visited = set()
    visited.add(resolved_name)
    frontier = set()
    frontier.add(resolved_name)
    found_edges = []

    for step in range(hops):
        next_frontier = set()

        for node in frontier:
            # Edges going out from this node.
            for source, target, data in graph.out_edges(node, data=True):
                found_edges.append({"source": source, "relation": data["relation_type"], "target": target})
                if target not in visited:
                    next_frontier.add(target)

            # Edges coming into this node.
            for source, target, data in graph.in_edges(node, data=True):
                found_edges.append({"source": source, "relation": data["relation_type"], "target": target})
                if source not in visited:
                    next_frontier.add(source)

        visited = visited.union(next_frontier)
        frontier = next_frontier

    return found_edges


def find_path(concept_a, concept_b):
    """Returns the shortest chain of concepts connecting A to B, or an empty list if none exists."""
    a = resolve_entity(concept_a, use_llm_fallback=False)
    b = resolve_entity(concept_b, use_llm_fallback=False)
    try:
        return nx.shortest_path(graph, source=a, target=b)
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return []


def get_prerequisite_chain(concept_name):
    """
    Returns everything concept_name depends on (transitively), by only
    following "requires_understanding_of" edges.
    """
    resolved_name = resolve_entity(concept_name, use_llm_fallback=False)
    if resolved_name not in graph:
        return []

    prereq_graph = nx.DiGraph()
    for source, target, data in graph.edges(data=True):
        if data["relation_type"] == "requires_understanding_of":
            prereq_graph.add_edge(source, target)

    if resolved_name not in prereq_graph:
        return []

    return list(nx.ancestors(prereq_graph, resolved_name))


# Quick manual test -- run with: python -m src.graph_engine
if __name__ == "__main__":
    sample_text = "Dynamic Programming requires understanding of Recursion. Recursion requires understanding of Function Calls."
    triples = extract_triples(sample_text, chunk_id="test_chunk_1")
    print("Extracted:", triples)

    add_triples(triples)
    print("Stats:", graph_stats())
    print("Neighbors of Recursion:", get_neighbors("Recursion"))
