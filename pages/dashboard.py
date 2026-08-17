import streamlit as st
import plotly.express as px
import pandas as pd
from db import get_stats


def render():
    st.title("📊 Dashboard")

    user_id = st.session_state.user_id
    stats = get_stats(user_id)

    # Top-level metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Entries", stats["total"])
    with col2:
        num_fields = len(stats["by_field"])
        st.metric("Field Types Used", num_fields)
    with col3:
        top_field = max(stats["by_field"], key=lambda r: r["count"])["field"] if stats["by_field"] else "—"
        st.metric("Most Filled Field", top_field)

    st.divider()

    if stats["total"] == 0:
        st.info("No data yet. Head to the Storage page to add your first entry!")
        return

    col1, col2 = st.columns(2)

    # Bar chart: how many entries have each field filled in
    with col1:
        st.subheader("Entries by Field")
        df_field = pd.DataFrame(
            [{"Field": r["field"], "Count": r["count"]} for r in stats["by_field"]]
        )
        fig = px.bar(df_field, x="Field", y="Count", color="Field")
        st.plotly_chart(fig, use_container_width=True)

    # Pie chart: entries by category
    with col2:
        st.subheader("Entries by Category")
        if stats["by_category"]:
            df_cat = pd.DataFrame(
                [{"Category": r["category"], "Count": r["count"]} for r in stats["by_category"]]
            )
            fig = px.pie(df_cat, names="Category", values="Count")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No categories assigned yet.")

    # Bar chart: entries by AI provider
    st.subheader("Entries by Provider")
    if stats["by_provider"]:
        df_provider = pd.DataFrame(
            [{"Provider": r["provider"], "Count": r["count"]} for r in stats["by_provider"]]
        )
        fig = px.bar(df_provider, x="Provider", y="Count", color="Provider")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No providers assigned yet.")

    # Line chart: entries over time
    st.subheader("Entries Added Over Time")
    if stats["over_time"]:
        df_time = pd.DataFrame(
            [{"Date": r["day"], "Count": r["count"]} for r in stats["over_time"]]
        )
        fig = px.line(df_time, x="Date", y="Count", markers=True)
        st.plotly_chart(fig, use_container_width=True)