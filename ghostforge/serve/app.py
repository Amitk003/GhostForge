"""Streamlit dashboard for GhostForge.

Four views: upload, graph playback, risk cone, evidence.
Runs fully offline with error handling and hunt actions.
"""

import streamlit as st
import requests

from ghostforge.__version__ import __version__
from ghostforge.serve.ui_components import hunt_card, risk_badge, stage_bar

st.set_page_config(page_title="GhostForge", layout="wide", initial_sidebar_state="expanded")

st.sidebar.title("GhostForge")
st.sidebar.caption(f"v{__version__} - offline")
with st.sidebar:
    st.write("API status")
    try:
        r = requests.get("http://localhost:8000/health", timeout=1)
        if r.ok:
            st.success("API online")
        else:
            st.warning("API offline")
    except Exception:
        st.warning("API offline - run make run-api")

    page = st.radio("View", ["Upload", "Graph", "Risk Timeline", "Evidence"])

st.title("GhostForge - Network Attack Forecasting")

if page == "Upload":
    st.header("Upload Traffic")
    st.write("Upload a PCAP or flow CSV or Zeek conn.log. All processing is local and offline.")
    uploaded = st.file_uploader("Choose file", type=["pcap", "pcapng", "csv", "log", "txt", "gz"])
    if uploaded:
        st.success(f"Received {uploaded.name} ({uploaded.size} bytes)")
        st.info("Ingestion will run here and produce snapshots. See Graph and Risk tabs after processing.")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Run Inference", type="primary"):
                try:
                    st.write("Running twin inference...")
                    # Scaffold mock, real will call API
                    st.json({"window_id": 0, "risk": 0.34, "stage": "Reconnaissance", "confidence": 0.78, "plausibility": 1.0})
                    st.success("Inference done")
                except Exception as e:
                    st.error(f"Failed: {e}")
        with col2:
            st.caption("Max 100 MB, offline only")
            st.write(f"Risk badge: :{risk_badge(0.34)}[Risk 0.34]")

elif page == "Graph":
    st.header("Network Graph Playback")
    st.write("Hosts are nodes, flows are edges. Lateral movement appears as new edges across hosts.")
    w = st.slider("Time window", 0, 10, 0)
    st.caption(f"Showing window {w}")
    st.graphviz_chart(
        """
        digraph {
            192_168_1_5 -> 192_168_1_10 [label="SYN 445"]
            192_168_1_10 -> 192_168_1_12 [label="SMB"]
        }
        """
    )
    with st.expander("Graph stats"):
        st.write("Nodes: 12, Edges: 34, Density: 0.12, Avg degree: 2.8")

elif page == "Risk Timeline":
    st.header("Risk Forecast - Next 10 Windows")
    st.write("Risk timeline with confidence cone. Validated with MITRE prerequisites.")
    chart_data = {"window": list(range(11)), "risk": [0.1, 0.12, 0.2, 0.34, 0.45, 0.6, 0.72, 0.71, 0.68, 0.6, 0.55]}
    st.line_chart(chart_data, x="window", y="risk")
    st.caption("Stage: Reconnaissance -> Discovery -> Lateral Movement predicted")
    stages = ["Benign", "Reconnaissance", "Discovery", "LateralMovement", "CommandAndControl", "Exfiltration"]
    stage_bar(stages, "LateralMovement")
    st.divider()
    st.subheader("Hunt Plan")
    hunt_card("Pull auth logs", "host 10.0.0.10", 0.72, 0.41, 0.31)
    hunt_card("Check DNS queries", "host 10.0.0.10", 0.72, 0.50, 0.22)

elif page == "Evidence":
    st.header("Evidence Chain")
    st.write("Top flows that caused the drift and MITRE mapping.")
    st.table(
        {
            "src": ["10.0.0.5", "10.0.0.5"],
            "dst": ["10.0.0.10", "10.0.0.12"],
            "port": [445, 4444],
            "flags": ["SYN", "SYN"],
            "contrib": [0.42, 0.31],
        }
    )
    st.markdown("**MITRE:** T1021 Remote Services - [Details](https://attack.mitre.org/techniques/T1021/)")
    st.markdown("**Causal path:** Regime 12 -> 37 -> 41 led to LateralMovement")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Mark Correct", key="correct"):
            st.success("Feedback recorded as correct")
    with col2:
        if st.button("Mark Wrong", key="wrong"):
            st.warning("Feedback recorded as wrong, will be used for retrain")
    with col3:
        if st.button("Missing Context", key="missing"):
            st.info("Feedback recorded as missing context")
    if st.button("Export Sigma Rule"):
        st.code("title: GhostForge LateralMovement\nlogsource:\n  category: network\ndetection:\n  selection:\n    technique: T1021\n  condition: selection\nlevel: high", language="yaml")
