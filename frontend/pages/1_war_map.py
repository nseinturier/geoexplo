"""
War Map — Pydeck map of nation states and infrastructure.
"""
import os
import json
import streamlit as st
import requests
import pandas as pd
import pydeck as pdk

API_URL = os.getenv("API_URL", "http://api:8000")

st.set_page_config(page_title="War Map", page_icon="🗺️", layout="wide")
st.title("🗺️ War Map")


def api_get(path, params=None):
    try:
        r = requests.get(f"{API_URL}{path}", params=params, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"API error {path}: {e}")
        return []


def api_patch(path, data):
    try:
        r = requests.patch(f"{API_URL}{path}", json=data, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"PATCH error: {e}")
        return None


def score_to_color(score):
    """Return RGBA color based on stability score."""
    if score is None:
        return [128, 128, 128, 180]
    s = float(score)
    if s >= 0.7:
        return [34, 197, 94, 200]   # green
    elif s >= 0.4:
        return [234, 179, 8, 200]   # yellow
    else:
        return [239, 68, 68, 200]   # red


# ─── Layer toggles ────────────────────────────────────────────────────────────

st.sidebar.header("🗺️ War Map")
show_nations = st.sidebar.checkbox("Nation States", value=True)
show_military = st.sidebar.checkbox("Military Bases", value=True)
show_infra = st.sidebar.checkbox("Infrastructure", value=True)
show_chokepoints = st.sidebar.checkbox("Chokepoints", value=True)

# ─── Load data ────────────────────────────────────────────────────────────────

all_nodes = api_get("/objects") or []

nation_rows = []
infra_rows = []

for n in all_nodes:
    labels = n.get("_labels", [])
    lat = n.get("latitude")
    lon = n.get("longitude")
    if lat is None or lon is None:
        continue
    score = n.get("stability_score", 1.0)
    color = score_to_color(score)
    row = {
        "uid": n.get("uid", ""),
        "name": n.get("name", ""),
        "lat": lat,
        "lon": lon,
        "score": score,
        "color": color,
        "type": n.get("type", ""),
        "operational": n.get("operational", True),
        "labels": labels,
    }
    if "NationState" in labels:
        nation_rows.append(row)
    elif "Infrastructure" in labels:
        infra_rows.append(row)

# ─── Build pydeck layers ──────────────────────────────────────────────────────

layers = []

if show_nations and nation_rows:
    df_nations = pd.DataFrame(nation_rows)
    df_nations["color"] = df_nations["color"].apply(lambda c: c)
    layers.append(
        pdk.Layer(
            "ScatterplotLayer",
            data=df_nations,
            get_position="[lon, lat]",
            get_fill_color="color",
            get_radius=80000,
            pickable=True,
            auto_highlight=True,
            id="nations",
        )
    )

infra_type_filters = []
if show_military:
    infra_type_filters.append("military_base")
if show_infra:
    infra_type_filters.extend(["desalination", "oil_field", "power_plant", "port", "dam", "financial_market"])
if show_chokepoints:
    infra_type_filters.append("chokepoint")

if infra_rows:
    filtered_infra = [r for r in infra_rows if r["type"] in infra_type_filters] if infra_type_filters else infra_rows
    if filtered_infra:
        df_infra = pd.DataFrame(filtered_infra)
        layers.append(
            pdk.Layer(
                "ScatterplotLayer",
                data=df_infra,
                get_position="[lon, lat]",
                get_fill_color="color",
                get_radius=40000,
                pickable=True,
                auto_highlight=True,
                id="infra",
            )
        )

view_state = pdk.ViewState(latitude=25.0, longitude=52.0, zoom=4, pitch=0)

tooltip = {
    "html": "<b>{name}</b><br/>Stability: {score}<br/>Type: {type}<br/>Operational: {operational}",
    "style": {"backgroundColor": "#1e293b", "color": "white"},
}

deck = pdk.Deck(
    layers=layers,
    initial_view_state=view_state,
    tooltip=tooltip,
    map_style="mapbox://styles/mapbox/dark-v10",
)

event = st.pydeck_chart(deck, on_select="rerun", selection_mode="single-object")

# ─── Selected node panel ──────────────────────────────────────────────────────

selected_uid = None
if event and hasattr(event, "selection") and event.selection:
    sel = event.selection
    if sel.get("objects"):
        first = list(sel["objects"].values())[0]
        if first:
            selected_uid = first[0].get("uid")

if selected_uid:
    st.sidebar.markdown("---")
    st.sidebar.subheader("Selected Object")
    node_detail = api_get(f"/objects/{selected_uid}")
    if node_detail:
        score = node_detail.get("stability_score", 1.0)
        color_name = "🟢" if score >= 0.7 else "🟡" if score >= 0.4 else "🔴"
        st.sidebar.markdown(f"**{node_detail.get('name')}** {color_name}")

        for k, v in node_detail.items():
            if k.startswith("_") or k in ("outgoing_relationships", "incoming_relationships"):
                continue
            st.sidebar.write(f"**{k}:** {v}")

        if st.sidebar.button("✏️ Edit"):
            st.session_state["editing_uid"] = selected_uid

if st.session_state.get("editing_uid"):
    uid = st.session_state["editing_uid"]
    node_detail = api_get(f"/objects/{uid}") or {}
    st.subheader(f"✏️ Edit: {node_detail.get('name', uid)}")

    with st.form(f"edit_{uid}"):
        col1, col2 = st.columns(2)
        with col1:
            new_score = st.slider(
                "Stability Score",
                0.0, 1.0,
                float(node_detail.get("stability_score", 1.0)),
                0.01,
            )
            new_notes = st.text_area("Notes", value=node_detail.get("notes", ""))
        with col2:
            new_confidence = st.slider(
                "Confidence",
                0.0, 1.0,
                float(node_detail.get("confidence", 1.0)),
                0.01,
            )
            if "Infrastructure" in node_detail.get("_labels", []):
                new_operational = st.checkbox(
                    "Operational",
                    value=bool(node_detail.get("operational", True)),
                )
            else:
                new_operational = None

        submitted = st.form_submit_button("💾 Save")
        cancelled = st.form_submit_button("Cancel")

        if submitted:
            patch_data = {
                "stability_score": new_score,
                "notes": new_notes,
                "confidence": new_confidence,
            }
            if new_operational is not None:
                patch_data["operational"] = new_operational
            result = api_patch(f"/objects/{uid}", patch_data)
            if result:
                st.success("Saved!")
                del st.session_state["editing_uid"]
                st.rerun()

        if cancelled:
            del st.session_state["editing_uid"]
            st.rerun()

# ─── Legend ───────────────────────────────────────────────────────────────────

st.markdown("---")
col1, col2, col3 = st.columns(3)
col1.markdown("🟢 Stability > 0.7 (Stable)")
col2.markdown("🟡 Stability 0.4–0.7 (Stressed)")
col3.markdown("🔴 Stability < 0.4 (Critical)")
