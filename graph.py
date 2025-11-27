# graph.py
import networkx as nx


def build_graph(entries, relationships):
    """
    Build a directed NetworkX graph from database rows.

    Nodes: entry id
      attrs:
        - label: title
        - category: category string (Character, Location, etc.)

    Edges: one per relationship row.
    """
    G = nx.DiGraph()

    # Nodes
    for e in entries:
        entry_id = e["id"]
        title = e["title"] or f"ID {entry_id}"
        category = e["category"] or "default"

        G.add_node(entry_id, label=title, category=category)

    # Edges
    for r in relationships:
        a = r["entry_a"]
        b = r["entry_b"]
        rel_type = r["type"] or "relationship"

        if a in G.nodes and b in G.nodes:
            G.add_edge(a, b, label=rel_type)

    return G






