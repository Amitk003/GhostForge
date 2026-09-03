"""Reusable UI components for Streamlit."""

import streamlit as st


def risk_badge(risk: float) -> str:
    """Return color for risk badge."""
    if risk < 0.3:
        return "green"
    if risk < 0.6:
        return "orange"
    return "red"


def stage_bar(stages: list[str], current: str) -> None:
    """Render MITRE stage progress bar."""
    cols = st.columns(len(stages))
    for i, s in enumerate(stages):
        with cols[i]:
            if s == current:
                st.markdown(f"**{s}**")
                st.markdown(":red_circle:")
            elif stages.index(s) < stages.index(current) if current in stages else False:
                st.markdown(f"{s}")
                st.markdown(":white_check_mark:")
            else:
                st.markdown(f"{s}")
                st.markdown(":grey_question:")


def hunt_card(title: str, target: str, before: float, after: float, delta: float) -> None:
    """Render one hunt action card."""
    with st.container(border=True):
        st.write(f"**{title}** - target {target}")
        st.write(f"Risk {before:.2f} -> {after:.2f} (drop {delta:.2f})")
        if st.button(f"Apply {title}", key=title):
            st.success(f"Hunt {title} applied in simulation")
