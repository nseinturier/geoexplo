"""
Graph Explorer — Pyvis network with cascade simulation.
"""
import os
import json
import streamlit as st
import streamlit.components.v1 as components
import requests
from pyvis.network import Network

API_URL = os.getenv("API_URL", "http://api:8000")

st.set_page_config(page_title="Graph Explorer", page_icon="🕸️", layout="wide")
st.title("🕸️ Graph Explorer")


def api_get(path, params=None):
    try:
        r = requests.get(f"{API_URL}{path}", params=params, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"API error: {e}")
        return None


def api_post(path, data):
    try:
        r = requests.post(f"{API_URL}{path}", json=data, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"POST error: {e}")
        return None


def score_to_hex(score):
    if score is None:
        return "#64748b"
    s = float(score)
    if s >= 0.7:
        return "#22c55e"
    elif s >= 0.4:
        return "#eab308"
    else:
        return "#ef4444"


# ─── Sidebar controls ─────────────────────────────────────────────────────────

st.sidebar.header("🕸️ Graph Explorer")
rel_filter = st.sidebar.multiselect(
    "Show relationship types",
    ["ALLIED_WITH", "HOSTILE_TO", "DEPENDS_ON", "CAN_STRIKE", "CONTROLS",
     "HOSTS_BASE", "FUNDS", "INVESTS_IN", "RELIGIOUSLY_LOYAL_TO"],
    default=["ALLIED_WITH", "HOSTILE_TO", "DEPENDS_ON", "CAN_STRIKE"],
)

show_labels = st.sidebar.checkbox("Show node labels", value=True)

# ─── Load graph data ──────────────────────────────────────────────────────────

@st.cache_data(ttl=30)
def load_graph():
    nodes = api_get("/objects") or []
    edges = api_get("/objects/edges/all") or []
    return nodes, edges


all_nodes, all_edges = load_graph()

# Build a lookup: uid → node data
node_map = {n["uid"]: n for n in all_nodes if "uid" in n}

# ─── Simulation state ─────────────────────────────────────────────────────────

if "cascade_result" not in st.session_state:
    st.session_state["cascade_result"] = {}

affected_uids = set(st.session_state["cascade_result"].keys())

# ─── Build Pyvis network ──────────────────────────────────────────────────────

net = Network(
    height="600px",
    width="100%",
    bgcolor="#0f172a",
    font_color="white",
    directed=True,
)
net.set_options(json.dumps({
    "physics": {"enabled": True, "stabilization": {"iterations": 100}},
    "edges": {"arrows": {"to": {"enabled": True}}},
    "interaction": {"hover": True},
}))

# Add nodes
for n in all_nodes:
    uid = n.get("uid")
    if not uid:
        continue
    labels = n.get("_labels", [])
    score = n.get("stability_score", 1.0)

    if uid in affected_uids:
        color = "#ef4444"  # red = affected by cascade
        size = 30
    else:
        color = score_to_hex(score)
        size = 20 if "NationState" in labels else 12

    shape = "dot"
    if "NationState" in labels:
        shape = "diamond"
    elif "Infrastructure" in labels:
        shape = "square"

    title = f"{n.get('name', uid)}<br>Score: {score:.2f}<br>Labels: {', '.join(labels)}"
    net.add_node(
        uid,
        label=n.get("name", uid) if show_labels else "",
        color=color,
        size=size,
        shape=shape,
        title=title,
    )

# Add edges from bulk edge query
edge_colors = {
    "ALLIED_WITH": "#22c55e",
    "HOSTILE_TO": "#ef4444",
    "DEPENDS_ON": "#3b82f6",
    "CAN_STRIKE": "#f97316",
    "CONTROLS": "#8b5cf6",
    "CONTROLS_CHOKEPOINT": "#a855f7",
    "HOSTS_BASE": "#06b6d4",
    "FUNDS": "#f59e0b",
    "INVESTS_IN": "#10b981",
    "RELIGIOUSLY_LOYAL_TO": "#ec4899",
}

added_edges = set()
for edge in all_edges:
    rel_type = edge.get("rel_type", "")
    source = edge.get("source_uid")
    target = edge.get("target_uid")
    if not source or not target or rel_type not in rel_filter:
        continue
    # Only add if both nodes exist in our node list
    if source not in node_map or target not in node_map:
        continue
    edge_key = (source, target, rel_type)
    if edge_key in added_edges:
        continue
    added_edges.add(edge_key)

    edge_color = edge_colors.get(rel_type, "#94a3b8")
    props = edge.get("rel_props", {})
    tooltip = f"{rel_type}"
    if props:
        tooltip += "<br>" + "<br>".join(f"{k}: {v}" for k, v in props.items() if v is not None)

    net.add_edge(source, target, color=edge_color, title=tooltip, label=rel_type[:4])

# Render
html_content = net.generate_html()
components.html(html_content, height=620)

# ─── Cascade simulation controls ──────────────────────────────────────────────

st.markdown("---")
st.subheader("⚡ Cascade Simulation")

col1, col2, col3 = st.columns(3)
with col1:
    uid_options = [n["uid"] for n in all_nodes if "uid" in n]
    name_map = {n["uid"]: n.get("name", n["uid"]) for n in all_nodes if "uid" in n}
    selected_source = st.selectbox(
        "Strike target",
        uid_options,
        format_func=lambda x: name_map.get(x, x),
    )
with col2:
    impact_val = st.slider("Impact (0–1)", 0.0, 1.0, 0.7, 0.05)
with col3:
    max_depth = st.slider("Max depth", 1, 10, 6)

col_a, col_b, col_c = st.columns(3)
with col_a:
    persist = st.checkbox("Persist to DB", value=False)
with col_b:
    scenario_id = st.text_input("Scenario ID", value="production")

if st.button("⚡ Simulate Strike", type="primary"):
    result = api_post("/cascade/simulate", {
        "source_uid": selected_source,
        "impact": impact_val,
        "max_depth": max_depth,
        "persist": persist,
        "scenario_id": scenario_id,
    })
    if result:
        affected = result.get("affected", [])
        st.session_state["cascade_result"] = {a["uid"]: a for a in affected}
        st.success(f"Cascade affected {len(affected)} nodes. Graph will re-render.")
        st.rerun()

# Show cascade results table
if st.session_state["cascade_result"]:
    st.subheader("🔴 Cascade Results")
    import pandas as pd
    rows = list(st.session_state["cascade_result"].values())
    df = pd.DataFrame(rows)[["uid", "name", "old_score", "new_score", "depth"]]
    df["delta"] = df["new_score"] - df["old_score"]
    st.dataframe(df.sort_values("delta"), use_container_width=True)

    if st.button("Clear results"):
        st.session_state["cascade_result"] = {}
        st.rerun()

# ─── Path finder ──────────────────────────────────────────────────────────────

st.markdown("---")
st.subheader("🔍 Influence Path")
col1, col2 = st.columns(2)
with col1:
    path_from = st.selectbox("From", uid_options, key="path_from", format_func=lambda x: name_map.get(x, x))
with col2:
    path_to = st.selectbox("To", uid_options, key="path_to", format_func=lambda x: name_map.get(x, x))

if st.button("Find Path"):
    result = api_get("/cascade/path", params={"from": path_from, "to": path_to})
    if result and result.get("path"):
        path_nodes = result["path"]
        steps = []
        for item in path_nodes:
            if item["type"] == "node":
                steps.append(f"**{item.get('name', item.get('uid', ''))}**")
            else:
                steps.append(f"→ _{item.get('rel_type', '')}_ →")
        st.write(" ".join(steps))
    else:
        st.warning("No path found between these nodes.")
