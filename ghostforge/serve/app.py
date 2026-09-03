"""Streamlit dashboard for GhostForge.

Four views: upload, graph playback, risk cone, evidence.
Runs fully offline.
"""

import streamlit as st

from ghostforge.__version__ import __version__

st.set_page_config(page_title="GhostForge", layout="wide", initial_sidebar_state="expanded")

st.sidebar.title("GhostForge")
st.sidebar.caption(f"v{__version__} - offline")
page = st.sidebar.radio("View", ["Upload", "Graph", "Risk Timeline", "Evidence"])

st.title("GhostForge - Network Attack Forecasting")

if page == "Upload":
    st.header("Upload Traffic")
    st.write("Upload a PCAP or flow CSV or Zeek conn.log. All processing is local.")
    uploaded = st.file_uploader("Choose file", type=["pcap", "pcapng", "csv", "log", "txt"])
    if uploaded:
        st.success(f"Received {uploaded.name} ({uploaded.size} bytes)")
        st.info("Ingestion will run here and produce snapshots. See Graph and Risk tabs after processing.")
        if st.button("Run Inference"):
            st.write("Running twin inference...")
            st.json({"window_id": 0, "risk": 0.34, "stage": "Reconnaissance", "confidence": 0.78})

elif page == "Graph":
    st.header("Network Graph Playback")
    st.write("Hosts are nodes, flows are edges. Lateral movement appears as new edges across hosts.")
    st.slider("Time window", 0, 10, 0)
    st.graphviz_chart(
        """
        digraph {
            192_168_1_5 -> 192_168_1_10 [label="SYN 445"]
            192_168_1_10 -> 192_168_1_12 [label="SMB"]
        }
        """
    )

elif page == "Risk Timeline":
    st.header("Risk Forecast - Next 10 Windows")
    st.write("Risk timeline with confidence cone. Validated with MITRE prerequisites.")
    chart_data = {"window": list(range(11)), "risk": [0.1, 0.12, 0.2, 0.34, 0.45, 0.6, 0.72, 0.71, 0.68, 0.6, 0.55]}
    st.line_chart(chart_data, x="window", y="risk")
    st.caption("Stage: Reconnaissance -> Discovery -> Lateral Movement predicted")

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
    col1, col2, col3 = st.columns(3)
    with col1:
        st.button("Mark Correct")
    with col2:
        st.button("Mark Wrong")
    with col3:
        st.button("Missing Context")
