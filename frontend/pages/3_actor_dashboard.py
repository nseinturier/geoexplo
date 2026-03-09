"""
Actor Dashboard — Grid of actor cards with writeback.
"""
import os
import streamlit as st
import requests
import pandas as pd

API_URL = os.getenv("API_URL", "http://api:8000")

st.set_page_config(page_title="Actor Dashboard", page_icon="🎯", layout="wide")
st.title("🎯 Actor Dashboard")


def api_get(path, params=None):
    try:
        r = requests.get(f"{API_URL}{path}", params=params, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"API error: {e}")
        return None


def api_patch(path, data):
    try:
        r = requests.patch(f"{API_URL}{path}", json=data, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"PATCH error: {e}")
        return None


def api_post(path, data):
    try:
        r = requests.post(f"{API_URL}{path}", json=data, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"POST error: {e}")
        return None


@st.cache_data(ttl=15)
def load_actors():
    nodes = api_get("/objects") or []
    return [n for n in nodes if any(l in n.get("_labels", []) for l in ["NationState", "MilitaryAlliance", "NonStateActor"])]


@st.cache_data(ttl=30)
def load_snapshots():
    """Get stability snapshots from events endpoint (via analytics)."""
    return api_get("/objects") or []


actors = load_actors()

if not actors:
    st.info("No actors found. Run seed.py to populate data.")
    st.stop()

# ─── Search / filter ──────────────────────────────────────────────────────────

search = st.text_input("🔍 Search actors", "")
if search:
    actors = [a for a in actors if search.lower() in a.get("name", "").lower()]

# ─── Actor grid ───────────────────────────────────────────────────────────────

def stability_emoji(score):
    s = float(score) if score is not None else 1.0
    if s >= 0.7:
        return "🟢"
    elif s >= 0.4:
        return "🟡"
    return "🔴"


COLS = 3
rows = [actors[i:i+COLS] for i in range(0, len(actors), COLS)]

for row in rows:
    cols = st.columns(COLS)
    for col, actor in zip(cols, row):
        uid = actor.get("uid", "")
        name = actor.get("name", uid)
        score = actor.get("stability_score", 1.0)
        labels = actor.get("_labels", [])

        with col:
            with st.container(border=True):
                label_str = " | ".join(labels)
                emoji = stability_emoji(score)
                st.markdown(f"### {emoji} {name}")
                st.caption(label_str)

                # Key metrics
                m1, m2 = st.columns(2)
                m1.metric("Stability", f"{score:.2f}")
                if "NationState" in labels:
                    nuclear = "☢️ Yes" if actor.get("is_nuclear") else "No"
                    m2.metric("Nuclear", nuclear)
                    st.markdown(f"**Regime:** {actor.get('regime_type', 'N/A')}")
                    gdp = actor.get("gdp_usd", 0)
                    if gdp:
                        st.markdown(f"**GDP:** ${gdp/1e12:.2f}T" if gdp > 1e12 else f"**GDP:** ${gdp/1e9:.0f}B")
                    pct_shia = actor.get("pct_shia")
                    if pct_shia:
                        st.markdown(f"**Shia pop:** {pct_shia*100:.0f}%")

                # Notes with save
                with st.expander("📝 Notes & Edit"):
                    with st.form(f"notes_{uid}"):
                        new_notes = st.text_area(
                            "Notes",
                            value=actor.get("notes", ""),
                            key=f"note_{uid}",
                        )
                        new_score = st.slider(
                            "Stability Score",
                            0.0, 1.0,
                            float(score),
                            0.01,
                            key=f"score_{uid}",
                        )
                        if st.form_submit_button("💾 Save"):
                            result = api_patch(f"/objects/{uid}", {
                                "notes": new_notes,
                                "stability_score": new_score,
                            })
                            if result:
                                st.success("Saved!")
                                st.cache_data.clear()
                                st.rerun()

                # Relationships
                with st.expander("🔗 Relationships"):
                    detail = api_get(f"/objects/{uid}")
                    if detail:
                        out_rels = detail.get("outgoing_relationships", [])
                        in_rels = detail.get("incoming_relationships", [])
                        if out_rels:
                            st.markdown("**→ Outgoing:**")
                            for rel in out_rels[:8]:
                                rtype = rel.get("type", "")
                                tname = rel.get("target_name", rel.get("target_uid", ""))
                                st.markdown(f"- {rtype} → {tname}")
                        if in_rels:
                            st.markdown("**← Incoming:**")
                            for rel in in_rels[:8]:
                                rtype = rel.get("type", "")
                                sname = rel.get("source_name", rel.get("source_uid", ""))
                                st.markdown(f"- {sname} → {rtype}")

                # Strategic assessment
                with st.expander("🧠 Strategic Assessment"):
                    # Try to get existing analyst note
                    with st.form(f"assessment_{uid}"):
                        assessment = st.text_area(
                            "Assessment",
                            key=f"assessment_text_{uid}",
                            placeholder="Add strategic assessment...",
                        )
                        if st.form_submit_button("💾 Save Assessment"):
                            api_post("/analytics/notes", {
                                "object_uid": uid,
                                "note": assessment,
                                "author": "analyst",
                            })
                            st.success("Assessment saved!")

# ─── Risk analytics ───────────────────────────────────────────────────────────

st.markdown("---")
st.subheader("📊 Actor Risk Analysis")

risk_uid = st.selectbox(
    "Select actor for risk analysis",
    [a["uid"] for a in actors],
    format_func=lambda x: next((a["name"] for a in actors if a["uid"] == x), x),
)

if st.button("Analyze Risk"):
    risk = api_get(f"/analytics/actor_risk/{risk_uid}")
    if risk:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Composite Risk", f"{risk.get('composite_risk', 0):.2f}")
        c2.metric("Enemy Count", risk.get("enemy_count", 0))
        c3.metric("Exposed Infra", risk.get("exposed_infrastructure", 0))
        c4.metric("Dependencies", risk.get("dependency_count", 0))
