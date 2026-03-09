"""
Raw Cypher traversal functions using the Neo4j Python driver.
"""
import os
from neo4j import GraphDatabase

_driver = None


def get_driver():
    global _driver
    if _driver is None:
        url = os.getenv("NEO4J_URL", "bolt://neo4j:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "password")
        _driver = GraphDatabase.driver(url, auth=(user, password))
    return _driver


def _record_to_dict(record):
    """Convert a Neo4j Record to a plain dict."""
    return dict(record)


def get_all_nodes(node_type: str | None = None) -> list[dict]:
    driver = get_driver()
    if node_type:
        label_map = {
            "NationState": "NationState",
            "Infrastructure": "Infrastructure",
            "MilitaryAlliance": "MilitaryAlliance",
            "NonStateActor": "NonStateActor",
            "Resource": "Resource",
            "WeaponSystem": "WeaponSystem",
        }
        label = label_map.get(node_type, node_type)
        query = f"MATCH (n:{label}) RETURN n"
    else:
        query = "MATCH (n) WHERE n.uid IS NOT NULL RETURN n"

    with driver.session() as session:
        result = session.run(query)
        nodes = []
        for record in result:
            node = record["n"]
            d = dict(node.items())
            d["_labels"] = list(node.labels)
            nodes.append(d)
        return nodes


def get_node_by_uid(uid: str) -> dict | None:
    driver = get_driver()
    query = "MATCH (n {uid: $uid}) RETURN n"
    with driver.session() as session:
        result = session.run(query, uid=uid)
        record = result.single()
        if not record:
            return None
        node = record["n"]
        d = dict(node.items())
        d["_labels"] = list(node.labels)
        return d


def get_node_with_relationships(uid: str) -> dict:
    driver = get_driver()
    query = """
    MATCH (n {uid: $uid})
    OPTIONAL MATCH (n)-[r]->(m)
    RETURN n,
           collect({
               type: type(r),
               props: properties(r),
               target_uid: m.uid,
               target_name: m.name,
               target_labels: labels(m)
           }) AS out_rels
    """
    in_query = """
    MATCH (n {uid: $uid})
    OPTIONAL MATCH (m)-[r]->(n)
    RETURN collect({
               type: type(r),
               props: properties(r),
               source_uid: m.uid,
               source_name: m.name,
               source_labels: labels(m)
           }) AS in_rels
    """
    with driver.session() as session:
        result = session.run(query, uid=uid)
        record = result.single()
        if not record:
            return {}
        node = record["n"]
        out_rels = record["out_rels"]

        in_result = session.run(in_query, uid=uid)
        in_record = in_result.single()
        in_rels = in_record["in_rels"] if in_record else []

        d = dict(node.items())
        d["_labels"] = list(node.labels)
        d["outgoing_relationships"] = [r for r in out_rels if r.get("target_uid")]
        d["incoming_relationships"] = [r for r in in_rels if r.get("source_uid")]
        return d


def get_neighbors(uid: str) -> list[dict]:
    driver = get_driver()
    query = """
    MATCH (n {uid: $uid})-[r]-(m)
    RETURN m, type(r) as rel_type, properties(r) as rel_props
    """
    with driver.session() as session:
        result = session.run(query, uid=uid)
        neighbors = []
        for record in result:
            node = record["m"]
            d = dict(node.items())
            d["_labels"] = list(node.labels)
            d["_rel_type"] = record["rel_type"]
            d["_rel_props"] = dict(record["rel_props"])
            neighbors.append(d)
        return neighbors


def update_node_properties(uid: str, props: dict) -> dict | None:
    driver = get_driver()
    # Build SET clauses dynamically
    set_clause = ", ".join(f"n.{k} = ${k}" for k in props)
    query = f"MATCH (n {{uid: $uid}}) SET {set_clause} RETURN n"
    params = {"uid": uid, **props}
    with driver.session() as session:
        result = session.run(query, **params)
        record = result.single()
        if not record:
            return None
        node = record["n"]
        d = dict(node.items())
        d["_labels"] = list(node.labels)
        return d


def get_shortest_path(from_uid: str, to_uid: str) -> list[dict]:
    driver = get_driver()
    query = """
    MATCH (a {uid: $from_uid}), (b {uid: $to_uid}),
          p = shortestPath((a)-[*..10]-(b))
    RETURN [n in nodes(p) | {uid: n.uid, name: n.name, labels: labels(n)}] AS path_nodes,
           [r in relationships(p) | type(r)] AS rel_types
    """
    with driver.session() as session:
        result = session.run(query, from_uid=from_uid, to_uid=to_uid)
        record = result.single()
        if not record:
            return []
        path_nodes = list(record["path_nodes"])
        rel_types = list(record["rel_types"])
        # Interleave nodes and relationship types
        path = []
        for i, node in enumerate(path_nodes):
            path.append({"type": "node", **dict(node)})
            if i < len(rel_types):
                path.append({"type": "relationship", "rel_type": rel_types[i]})
        return path


def get_all_graph_for_simulation() -> dict:
    """Return all nodes + DEPENDS_ON + CAN_STRIKE edges for NetworkX loading."""
    driver = get_driver()
    node_query = """
    MATCH (n) WHERE n.uid IS NOT NULL
    RETURN n.uid AS uid, n.name AS name,
           coalesce(n.stability_score, 1.0) AS stability_score,
           coalesce(n.collapse_impact, 0.5) AS collapse_impact,
           coalesce(n.operational, true) AS operational,
           labels(n) AS labels
    """
    edge_query = """
    MATCH (a)-[r:DEPENDS_ON|CAN_STRIKE]->(b)
    WHERE a.uid IS NOT NULL AND b.uid IS NOT NULL
    RETURN a.uid AS source, b.uid AS target, type(r) AS rel_type,
           coalesce(r.pct_dependency, 0.5) AS weight,
           coalesce(r.collapse_impact, 0.5) AS collapse_impact
    """
    with driver.session() as session:
        nodes = []
        for record in session.run(node_query):
            nodes.append(dict(record))
        edges = []
        for record in session.run(edge_query):
            edges.append(dict(record))
    return {"nodes": nodes, "edges": edges}


def get_all_edges() -> list[dict]:
    """Return all relationships for graph rendering."""
    driver = get_driver()
    query = """
    MATCH (a)-[r]->(b)
    WHERE a.uid IS NOT NULL AND b.uid IS NOT NULL
    RETURN a.uid AS source_uid,
           b.uid AS target_uid,
           type(r) AS rel_type,
           properties(r) AS rel_props
    """
    with driver.session() as session:
        return [dict(r) for r in session.run(query)]


def get_most_vulnerable_infrastructure() -> list[dict]:
    driver = get_driver()
    query = """
    MATCH (n:Infrastructure)
    WHERE n.attack_difficulty > 0
    RETURN n.uid AS uid, n.name AS name,
           n.collapse_impact AS collapse_impact,
           n.attack_difficulty AS attack_difficulty,
           n.operational AS operational,
           n.type AS type,
           (n.collapse_impact / n.attack_difficulty) AS vulnerability_score
    ORDER BY vulnerability_score DESC
    LIMIT 10
    """
    with driver.session() as session:
        return [dict(r) for r in session.run(query)]


def get_chokepoints_with_dependency_count() -> list[dict]:
    driver = get_driver()
    query = """
    MATCH (n:Infrastructure {type: 'chokepoint'})
    OPTIONAL MATCH (dep)-[:DEPENDS_ON]->(n)
    RETURN n.uid AS uid, n.name AS name,
           n.collapse_impact AS collapse_impact,
           n.operational AS operational,
           n.latitude AS latitude, n.longitude AS longitude,
           count(dep) AS dependency_count
    ORDER BY dependency_count DESC
    """
    with driver.session() as session:
        return [dict(r) for r in session.run(query)]


def get_actor_risk_score(uid: str) -> dict:
    driver = get_driver()
    query = """
    MATCH (a {uid: $uid})
    OPTIONAL MATCH (a)-[:HOSTILE_TO]->(enemy)
    OPTIONAL MATCH (attacker)-[:CAN_STRIKE]->(infra)<-[:CONTROLS|HOSTS_BASE]-(a)
    OPTIONAL MATCH (a)-[:DEPENDS_ON]->(r)
    RETURN a.uid AS uid,
           a.name AS name,
           a.stability_score AS stability_score,
           count(DISTINCT enemy) AS enemy_count,
           count(DISTINCT attacker) AS attacker_count,
           count(DISTINCT infra) AS exposed_infrastructure,
           count(DISTINCT r) AS dependency_count,
           (1.0 - coalesce(a.stability_score, 1.0)) * 0.4
               + count(DISTINCT enemy) * 0.1
               + count(DISTINCT attacker) * 0.15
               + count(DISTINCT infra) * 0.1
               + count(DISTINCT r) * 0.05 AS composite_risk
    """
    with driver.session() as session:
        result = session.run(query, uid=uid)
        record = result.single()
        if not record:
            return {}
        return dict(record)


def update_stability_score(uid: str, new_score: float):
    driver = get_driver()
    query = "MATCH (n {uid: $uid}) SET n.stability_score = $score"
    with driver.session() as session:
        session.run(query, uid=uid, score=new_score)


def set_operational(uid: str, operational: bool):
    driver = get_driver()
    query = "MATCH (n {uid: $uid}) SET n.operational = $operational"
    with driver.session() as session:
        session.run(query, uid=uid, operational=operational)
