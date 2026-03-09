"""
NetworkX-based cascade simulation engine.
"""
import networkx as nx
from datetime import datetime
from graph.queries import (
    get_all_graph_for_simulation,
    update_stability_score,
    set_operational,
)


def build_graph() -> nx.DiGraph:
    """Load Neo4j graph data into a NetworkX DiGraph."""
    data = get_all_graph_for_simulation()
    G = nx.DiGraph()

    for node in data["nodes"]:
        G.add_node(
            node["uid"],
            name=node.get("name", node["uid"]),
            stability_score=float(node.get("stability_score", 1.0)),
            collapse_impact=float(node.get("collapse_impact", 0.5)),
            operational=bool(node.get("operational", True)),
            labels=node.get("labels", []),
        )

    for edge in data["edges"]:
        G.add_edge(
            edge["source"],
            edge["target"],
            rel_type=edge.get("rel_type", "DEPENDS_ON"),
            weight=float(edge.get("weight", 0.5)),
            collapse_impact=float(edge.get("collapse_impact", 0.5)),
        )

    return G


def _propagate(
    G: nx.DiGraph,
    uid: str,
    impact: float,
    affected: dict,
    depth: int,
    max_depth: int,
):
    """Recursive cascade propagation."""
    if depth > max_depth or uid not in G:
        return

    node = G.nodes[uid]
    old_score = node.get("stability_score", 1.0)
    new_score = max(0.0, old_score - impact)
    node["stability_score"] = new_score

    operational = new_score >= 0.2
    node["operational"] = operational

    if uid not in affected or affected[uid]["depth"] > depth:
        affected[uid] = {
            "uid": uid,
            "name": node.get("name", uid),
            "old_score": old_score,
            "new_score": new_score,
            "depth": depth,
            "operational": operational,
        }

    # Propagate downstream
    for _, neighbor_uid, edge_data in G.out_edges(uid, data=True):
        rel_type = edge_data.get("rel_type", "DEPENDS_ON")
        if rel_type not in ("DEPENDS_ON",):
            continue
        edge_weight = edge_data.get("weight", 0.5)
        neighbor_collapse = G.nodes[neighbor_uid].get("collapse_impact", 0.5)
        downstream_impact = impact * edge_weight * neighbor_collapse
        if downstream_impact > 0.01:  # Skip negligible cascades
            _propagate(G, neighbor_uid, downstream_impact, affected, depth + 1, max_depth)


def run_cascade(
    source_uid: str,
    impact: float,
    max_depth: int = 6,
    persist: bool = False,
    scenario_id: str = "production",
    db=None,
) -> list[dict]:
    """
    Run cascade simulation from source_uid with given impact.
    Returns list of affected nodes sorted by impact severity.
    """
    G = build_graph()

    if source_uid not in G:
        return []

    # Record initial scores
    initial_scores = {uid: G.nodes[uid].get("stability_score", 1.0) for uid in G}

    affected = {}
    _propagate(G, source_uid, impact, affected, depth=0, max_depth=max_depth)

    results = sorted(affected.values(), key=lambda x: x["old_score"] - x["new_score"], reverse=True)

    if persist and db is not None:
        from relational.models import StabilitySnapshot
        for node_result in results:
            uid = node_result["uid"]
            new_score = node_result["new_score"]

            if scenario_id == "production":
                update_stability_score(uid, new_score)
                if new_score < 0.2:
                    set_operational(uid, False)

            # Always write snapshot
            snapshot = StabilitySnapshot(
                timestamp=datetime.utcnow(),
                scenario_id=scenario_id,
                object_uid=uid,
                stability_score=new_score,
                notes=f"Cascade from {source_uid}, impact={impact:.2f}",
            )
            db.add(snapshot)
        db.commit()

    return results
