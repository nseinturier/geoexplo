"""
Geopolitical Intelligence Platform — Streamlit entrypoint.
"""
import os
import streamlit as st
import requests

API_URL = os.getenv("API_URL", "http://api:8000")

st.set_page_config(
    page_title="GeoIntel Platform",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)


def api_get(path: str, params: dict = None):
    try:
        r = requests.get(f"{API_URL}{path}", params=params, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"API error: {e}")
        return None


# ─── Global sidebar ───────────────────────────────────────────────────────────

st.sidebar.title("🌍 GeoIntel Platform")
st.sidebar.markdown("---")

# Scenario selector
scenarios_data = api_get("/scenarios") or []
scenario_ids = ["production"] + [s["id"] for s in scenarios_data if not s.get("is_production")]
scenario_labels = {"production": "Production"} | {s["id"]: s["name"] for s in scenarios_data}

if "scenario_id" not in st.session_state:
    st.session_state["scenario_id"] = "production"

selected = st.sidebar.selectbox(
    "Active Scenario",
    options=scenario_ids,
    format_func=lambda x: scenario_labels.get(x, x),
    index=scenario_ids.index(st.session_state["scenario_id"]) if st.session_state["scenario_id"] in scenario_ids else 0,
)
st.session_state["scenario_id"] = selected

st.sidebar.markdown("---")
st.sidebar.markdown("**Navigation**")
st.sidebar.page_link("pages/1_war_map.py", label="🗺️ War Map")
st.sidebar.page_link("pages/2_graph_explorer.py", label="🕸️ Graph Explorer")
st.sidebar.page_link("pages/3_actor_dashboard.py", label="🎯 Actor Dashboard")
st.sidebar.page_link("pages/4_event_log.py", label="📋 Event Log")

# ─── Home page ────────────────────────────────────────────────────────────────

st.title("🌍 Geopolitical Intelligence Platform")
st.markdown(
    """
    A Palantir Foundry-inspired conflict scenario modelling platform for the US-Iran geopolitical situation.

    **Select a page from the sidebar to begin.**
    """
)

col1, col2, col3, col4 = st.columns(4)

health = api_get("/health")
with col1:
    st.metric("API Status", "✅ Online" if health else "❌ Offline")

nodes = api_get("/objects") or []
with col2:
    st.metric("Graph Nodes", len(nodes))

events = api_get("/events") or []
with col3:
    confirmed = sum(1 for e in events if e.get("confirmed"))
    st.metric("Confirmed Events", confirmed)

with col4:
    st.metric("Active Scenario", scenario_labels.get(selected, selected))

st.markdown("---")
st.subheader("📊 Quick Stats")

if nodes:
    nation_states = [n for n in nodes if "NationState" in n.get("_labels", [])]
    infra = [n for n in nodes if "Infrastructure" in n.get("_labels", [])]
    operational = [n for n in infra if n.get("operational", True)]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Nation States", len(nation_states))
    c2.metric("Infrastructure Nodes", len(infra))
    c3.metric("Operational Infra", len(operational))
    c4.metric("Compromised Infra", len(infra) - len(operational))
