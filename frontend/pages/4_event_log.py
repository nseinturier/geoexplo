"""
Event Log — Filterable event table with cascade trigger and stability charts.
"""
import os
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

API_URL = os.getenv("API_URL", "http://api:8000")

st.set_page_config(page_title="Event Log", page_icon="📋", layout="wide")
st.title("📋 Event Log")


def api_get(path, params=None):
    try:
        r = requests.get(f"{API_URL}{path}", params=params, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"API error: {e}")
        return None


def api_post(path, data):
    try:
        r = requests.post(f"{API_URL}{path}", json=data, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"POST error: {e}")
        return None


def api_patch(path, data):
    try:
        r = requests.patch(f"{API_URL}{path}", json=data, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"PATCH error: {e}")
        return None


# ─── Filters ──────────────────────────────────────────────────────────────────

st.sidebar.header("📋 Event Log Filters")
scenario_id = st.sidebar.text_input("Scenario ID", value="production")

event_types = ["", "strike", "political", "economic", "social", "diplomatic"]
event_type_filter = st.sidebar.selectbox("Event Type", event_types)

confirmed_filter = st.sidebar.selectbox("Confirmed", ["All", "Yes", "No"])

# Load all nodes for actor dropdown
all_nodes = api_get("/objects") or []
actor_options = {"": "All Actors"} | {n["uid"]: n.get("name", n["uid"]) for n in all_nodes if "uid" in n}
actor_filter = st.sidebar.selectbox(
    "Actor",
    list(actor_options.keys()),
    format_func=lambda x: actor_options.get(x, x),
)

# ─── Load events ──────────────────────────────────────────────────────────────

params = {}
if scenario_id:
    params["scenario_id"] = scenario_id
if event_type_filter:
    params["event_type"] = event_type_filter
if confirmed_filter == "Yes":
    params["confirmed"] = "true"
elif confirmed_filter == "No":
    params["confirmed"] = "false"
if actor_filter:
    params["actor_uid"] = actor_filter

events = api_get("/events", params=params) or []

# ─── Event table ──────────────────────────────────────────────────────────────

st.subheader(f"📜 Events ({len(events)})")

if events:
    df = pd.DataFrame(events)
    # Display columns
    display_cols = ["timestamp", "event_type", "actor_uid", "target_uid",
                    "description", "confirmed", "confidence", "casualties", "scenario_id", "id"]
    display_cols = [c for c in display_cols if c in df.columns]
    df_display = df[display_cols].copy()

    # Enrich with names
    node_name_map = {n["uid"]: n.get("name", n["uid"]) for n in all_nodes if "uid" in n}
    if "actor_uid" in df_display.columns:
        df_display["actor"] = df_display["actor_uid"].map(lambda x: node_name_map.get(x, x))
    if "target_uid" in df_display.columns:
        df_display["target"] = df_display["target_uid"].map(lambda x: node_name_map.get(x, x))

    st.dataframe(df_display, use_container_width=True, height=350)

    # Confirm buttons for unconfirmed events
    unconfirmed = [e for e in events if not e.get("confirmed")]
    if unconfirmed:
        st.subheader("⚠️ Unconfirmed Events — Confirm to Trigger Cascade")
        for ev in unconfirmed:
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.markdown(
                    f"**{ev.get('event_type', '')}** — "
                    f"{node_name_map.get(ev.get('actor_uid'), ev.get('actor_uid'))} → "
                    f"{node_name_map.get(ev.get('target_uid'), ev.get('target_uid'))} | "
                    f"_{ev.get('description', '')}_"
                )
            with col2:
                st.markdown(f"Confidence: {ev.get('confidence', 0):.0%}")
            with col3:
                if st.button("✅ Confirm", key=f"confirm_{ev['id']}"):
                    result = api_patch(f"/events/{ev['id']}", {"confirmed": True})
                    if result:
                        st.success(f"Event confirmed! Cascade triggered on {ev.get('target_uid')}")
                        st.rerun()
else:
    st.info("No events found with current filters.")

# ─── Add Event form ───────────────────────────────────────────────────────────

st.markdown("---")
st.subheader("➕ Add New Event")

with st.form("add_event"):
    col1, col2 = st.columns(2)
    with col1:
        ev_type = st.selectbox("Event Type", ["strike", "political", "economic", "social", "diplomatic"])
        actor_uid = st.selectbox(
            "Actor",
            list(actor_options.keys())[1:],  # skip empty
            format_func=lambda x: actor_options.get(x, x),
        )
        target_uid = st.selectbox(
            "Target",
            list(actor_options.keys())[1:],
            format_func=lambda x: actor_options.get(x, x),
            key="target_select",
        )
    with col2:
        description = st.text_area("Description")
        confidence = st.slider("Confidence", 0.0, 1.0, 0.8, 0.05)
        casualties = st.number_input("Casualties", min_value=0, value=0)
        is_confirmed = st.checkbox("Confirmed (triggers cascade)")
        ev_scenario = st.text_input("Scenario", value="production")

    if st.form_submit_button("📤 Submit Event", type="primary"):
        payload = {
            "event_type": ev_type,
            "actor_uid": actor_uid,
            "target_uid": target_uid,
            "description": description,
            "confidence": confidence,
            "casualties": casualties if casualties > 0 else None,
            "confirmed": is_confirmed,
            "scenario_id": ev_scenario,
        }
        result = api_post("/events", payload)
        if result:
            st.success("Event created!")
            if is_confirmed:
                st.info(f"Cascade triggered on {target_uid}")
            st.rerun()

# ─── Stability time-series ────────────────────────────────────────────────────

st.markdown("---")
st.subheader("📈 Stability Score Over Time")

uid_options = {n["uid"]: n.get("name", n["uid"]) for n in all_nodes if "uid" in n}
selected_obj = st.selectbox(
    "Select object",
    list(uid_options.keys()),
    format_func=lambda x: uid_options.get(x, x),
    key="stability_chart_uid",
)

if selected_obj and st.button("📊 Load Chart"):
    # Fetch snapshots through a direct DB query via a dedicated endpoint
    snapshots = api_get(f"/scenarios/snapshots/{selected_obj}")
    if snapshots:
        df_snap = pd.DataFrame(snapshots)
        df_snap["timestamp"] = pd.to_datetime(df_snap["timestamp"])
        fig = px.line(
            df_snap,
            x="timestamp",
            y="stability_score",
            color="scenario_id",
            title=f"Stability: {uid_options.get(selected_obj, selected_obj)}",
            labels={"stability_score": "Stability Score", "timestamp": "Time"},
        )
        fig.update_yaxes(range=[0, 1])
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No stability snapshots found for this object. Confirm events to generate data.")
