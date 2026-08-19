import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from db import get_stats

# Shared animation config applied to every chart.
# - duration: how long the animation runs in ms
# - easing: the motion curve
#   "elastic" = overshoots slightly then settles (bouncy, energetic)
#   "cubic-in-out" = smooth acceleration + deceleration (professional)
#   "bounce" = bounces at the end (playful, better for bars)
ANIM = dict(duration=800, easing="cubic-in-out")


def _apply_animation(fig):
    """Applies entrance animation + hover polish to any Plotly figure."""
    fig.update_layout(
        transition=ANIM,
        hoverlabel=dict(bgcolor="rgba(30,30,30,0.9)", font_size=13),
        margin=dict(t=30, b=10, l=10, r=10),
    )
    return fig


def render():
    st.title("📊 Dashboard")
    st.caption("An overview of everything you've saved: usage patterns, top tags, providers, and activity over time.")
    user_id = st.session_state.user_id
    stats = get_stats(user_id)

    # ---------- Metric Cards ----------
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Entries", stats["total"])
    with col2:
        num_fields = len(stats["by_field"])
        st.metric("Field Types Used", num_fields)
    with col3:
        top_field = max(stats["by_field"], key=lambda r: r["count"])["field"] if stats["by_field"] else "—"
        st.metric("Most Filled Field", top_field)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Most Used Provider", stats["top_provider"] or "—")
    with col2:
        st.metric("Most Used Tag", stats["top_category"] or "—")
    with col3:
        last_saved = stats["last_saved"]
        last_saved_display = str(last_saved).split(".")[0] if last_saved else "—"
        st.metric("Last Saved", last_saved_display)

    st.divider()

    if stats["total"] == 0:
        st.info("No data yet. Head to the Storage page to add your first entry!")
        return

    col1, col2 = st.columns(2)

    # ---------- Bar chart: Entries by Field ----------
    with col1:
        st.subheader("Entries by Field")
        df_field = pd.DataFrame(
            [{"Field": r["field"], "Count": r["count"]} for r in stats["by_field"]]
        )
        fig = px.bar(df_field, x="Field", y="Count", color="Field")
        # Bars grow upward from zero
        fig.update_traces(
            marker_line_width=0,
        )
        fig.update_layout(
            yaxis=dict(range=[0, df_field["Count"].max() * 1.2]),
            bargap=0.3,
            showlegend=False,
        )
        _apply_animation(fig)
        st.plotly_chart(fig, use_container_width=True)

    # ---------- Pie chart: Entries by Tag ----------
    with col2:
        st.subheader("Entries by Tag")
        if stats["by_category"]:
            df_cat = pd.DataFrame(
                [{"Tag": r["category"], "Count": r["count"]} for r in stats["by_category"]]
            )
            fig = px.pie(
                df_cat,
                names="Tag",
                values="Count",
                hole=0.4,  # donut style — more modern than a full pie
            )
            # Slices fan in one by one
            fig.update_traces(
                textposition="inside",
                textinfo="percent+label",
                pull=[0.03] * len(df_cat),  # slight separation between slices
            )
            _apply_animation(fig)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No categories assigned yet.")

    # ---------- Bar chart: Entries by Provider ----------
    st.subheader("Entries by Provider")
    if stats["by_provider"]:
        df_provider = pd.DataFrame(
            [{"Provider": r["provider"], "Count": r["count"]} for r in stats["by_provider"]]
        )
        fig = px.bar(
            df_provider,
            x="Provider",
            y="Count",
            color="Provider",
            text="Count",  # show count label on each bar
        )
        fig.update_traces(
            textposition="outside",
            marker_line_width=0,
        )
        fig.update_layout(
            yaxis=dict(range=[0, df_provider["Count"].max() * 1.3]),
            bargap=0.3,
            showlegend=False,
        )
        _apply_animation(fig)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No providers assigned yet.")

    # ---------- Line chart: Entries over Time ----------
    st.subheader("Entries Added Over Time")
    if stats["over_time"]:
        df_time = pd.DataFrame(
            [{"Date": r["day"], "Count": r["count"]} for r in stats["over_time"]]
        )
        fig = px.line(df_time, x="Date", y="Count", markers=True)
        # Line draws itself left to right
        fig.update_traces(
            line=dict(width=2.5),
            marker=dict(size=8, symbol="circle"),
            # Fill area under the line for better visual weight
            fill="tozeroy",
            fillcolor="rgba(99,102,241,0.15)",
        )
        fig.update_layout(
            xaxis=dict(showgrid=False),
            yaxis=dict(
                showgrid=True,
                gridcolor="rgba(200,200,200,0.1)",
                range=[0, df_time["Count"].max() * 1.3],
            ),
        )
        _apply_animation(fig)
        st.plotly_chart(fig, use_container_width=True)