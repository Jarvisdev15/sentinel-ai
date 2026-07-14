import pandas as pd
import streamlit as st

# This must run before other Streamlit commands.
st.set_page_config(
    page_title="Overview - SentinelAI",
    layout="wide",
)

import plotly.graph_objects as go

from app import load_css
from src.dashboard_data import load_dashboard_data


load_css()


def compact_html(markup: str) -> str:
    """Keep indented HTML from being parsed as a Markdown code block."""

    return "".join(line.strip() for line in markup.splitlines())


# -------------------------------------------------------------------
# Load the real scored activity dataset
# -------------------------------------------------------------------
try:
    df = load_dashboard_data()
except Exception as error:
    st.error("SentinelAI could not load the scored activity dataset.")
    st.code(f"{type(error).__name__}: {error}")
    st.stop()


# -------------------------------------------------------------------
# Constants used only for visual styling
# -------------------------------------------------------------------
TIER_ORDER = ["Low", "Medium", "High", "Critical"]

TIER_COLORS = {
    "Low": "#16A34A",
    "Medium": "#CA8A04",
    "High": "#EA580C",
    "Critical": "#DC2626",
}

TIER_BADGE = {
    "Low": "badge-low",
    "Medium": "badge-medium",
    "High": "badge-high",
    "Critical": "badge-critical",
}


# -------------------------------------------------------------------
# Real KPI calculations
# -------------------------------------------------------------------
total_activities = len(df)

high_critical_alerts = int(
    df["risk_tier"].isin(["High", "Critical"]).sum()
)

average_risk_score = round(
    float(df["final_score"].mean()),
    1,
)

critical_incidents = int(
    (df["risk_tier"] == "Critical").sum()
)


# -------------------------------------------------------------------
# Real risk-tier distribution
# -------------------------------------------------------------------
tier_counts = (
    df["risk_tier"]
    .value_counts()
    .reindex(TIER_ORDER, fill_value=0)
)

tier_percentages = (
    tier_counts / tier_counts.sum() * 100
).round(1)


# -------------------------------------------------------------------
# Real daily average risk trend
# -------------------------------------------------------------------
trend_df = (
    df.dropna(subset=["timestamp"])
    .assign(day=lambda data: data["timestamp"].dt.date)
    .groupby("day", as_index=False)["final_score"]
    .mean()
    .sort_values("day")
)

trend_days = (
    pd.to_datetime(trend_df["day"])
    .dt.strftime("%b %d")
    .tolist()
)

trend_scores = (
    trend_df["final_score"]
    .round(1)
    .tolist()
)


# -------------------------------------------------------------------
# Five most recent High and Critical alerts
# -------------------------------------------------------------------
recent_alerts_df = (
    df[df["risk_tier"].isin(["High", "Critical"])]
    .sort_values("timestamp", ascending=False)
    .head(5)
    .copy()
)


# -------------------------------------------------------------------
# Five users with the highest observed score
# -------------------------------------------------------------------
top_users_df = (
    df.groupby(
        ["user_id", "employee_name", "user_role"],
        as_index=False,
        dropna=False,
    )["final_score"]
    .max()
    .sort_values("final_score", ascending=False)
    .head(5)
)


# -------------------------------------------------------------------
# Page title
# -------------------------------------------------------------------
st.title("Overview")
st.caption(
    f"Monitoring {total_activities:,} synthetic privileged-user "
    "activities through explainable rules and behavioural anomaly detection."
)


# -------------------------------------------------------------------
# KPI cards
# -------------------------------------------------------------------
kpi_cols = st.columns(4)

kpis = [
    {
        "label": "Total activities",
        "value": f"{total_activities:,}",
        "description": "Current scored dataset",
        "danger": False,
    },
    {
        "label": "High / critical alerts",
        "value": f"{high_critical_alerts:,}",
        "description": "Require analyst review",
        "danger": True,
    },
    {
        "label": "Average risk score",
        "value": f"{average_risk_score:.1f}",
        "description": "Across all activities",
        "danger": False,
    },
    {
        "label": "Critical incidents",
        "value": f"{critical_incidents:,}",
        "description": "Immediate response recommended",
        "danger": True,
    },
]

for column, kpi in zip(kpi_cols, kpis):
    value_class = (
        "metric-value danger"
        if kpi["danger"]
        else "metric-value"
    )

    column.markdown(
        f"""
        <div class="metric-card">
            <p class="metric-label">{kpi["label"]}</p>
            <p class="{value_class}">{kpi["value"]}</p>
            <p class="metric-delta">{kpi["description"]}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


st.write("")


# -------------------------------------------------------------------
# Tier-distribution and trend charts
# -------------------------------------------------------------------
distribution_column, trend_column = st.columns([1, 1.6])


with distribution_column:
    st.markdown(
        """
        <div class="panel">
            <p class="panel-title">Risk tier distribution</p>
        """,
        unsafe_allow_html=True,
    )

    distribution_chart = go.Figure(
        data=[
            go.Pie(
                labels=TIER_ORDER,
                values=[
                    int(tier_counts[tier])
                    for tier in TIER_ORDER
                ],
                hole=0.65,
                marker={
                    "colors": [
                        TIER_COLORS[tier]
                        for tier in TIER_ORDER
                    ]
                },
                textinfo="none",
                hovertemplate=(
                    "%{label}: %{value} activities"
                    "<br>%{percent}<extra></extra>"
                ),
            )
        ]
    )

    distribution_chart.update_layout(
        height=210,
        margin={"t": 0, "b": 0, "l": 0, "r": 0},
        showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)",
        annotations=[
            {
                "text": f"<b>{total_activities}</b><br>Total",
                "x": 0.5,
                "y": 0.5,
                "font": {"size": 14},
                "showarrow": False,
            }
        ],
    )

    st.plotly_chart(
        distribution_chart,
        width="stretch",
        config={"displayModeBar": False},
    )

    for tier in TIER_ORDER:
        count = int(tier_counts[tier])
        percentage = float(tier_percentages[tier])

        st.markdown(
            compact_html(
                f"""
            <div style="
                display:flex;
                align-items:center;
                gap:8px;
                font-size:12px;
                margin-bottom:5px;
            ">
                <span style="
                    width:8px;
                    height:8px;
                    border-radius:50%;
                    background:{TIER_COLORS[tier]};
                "></span>

                <span style="
                    flex:1;
                    color:#6B7280;
                ">
                    {tier}
                </span>

                <span style="font-weight:600;">
                    {count} ({percentage:.1f}%)
                </span>
            </div>
            """
            ),
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)


with trend_column:
    st.markdown(
        """
        <div class="panel">
            <p class="panel-title">Average risk score by day</p>
        """,
        unsafe_allow_html=True,
    )

    trend_chart = go.Figure(
        data=[
            go.Scatter(
                x=trend_days,
                y=trend_scores,
                mode="lines+markers",
                line={
                    "color": "#2563EB",
                    "width": 2,
                },
                marker={
                    "size": 5,
                    "color": "#2563EB",
                },
                hovertemplate=(
                    "%{x}<br>"
                    "Average score: %{y:.1f}"
                    "<extra></extra>"
                ),
            )
        ]
    )

    trend_chart.update_layout(
        height=260,
        margin={"t": 10, "b": 10, "l": 10, "r": 10},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis={
            "showgrid": False,
            "color": "#6B7280",
            "title": None,
        },
        yaxis={
            "showgrid": True,
            "gridcolor": "#F3F4F6",
            "color": "#6B7280",
            "title": "Average score",
            "rangemode": "tozero",
        },
    )

    st.plotly_chart(
        trend_chart,
        width="stretch",
        config={"displayModeBar": False},
    )

    st.markdown("</div>", unsafe_allow_html=True)


st.write("")


# -------------------------------------------------------------------
# Recent alerts and highest-risk users
# -------------------------------------------------------------------
alerts_column, users_column = st.columns([1.6, 1])


with alerts_column:
    st.markdown(
        """
        <div class="panel">
            <p class="panel-title">
                Recent high and critical alerts
            </p>
        """,
        unsafe_allow_html=True,
    )

    table_header = st.columns(
        [1.4, 1.2, 1.2, 1.6, 0.7, 0.8]
    )

    headers = [
        "Time",
        "User",
        "Role",
        "Activity",
        "Score",
        "Tier",
    ]

    for column, heading in zip(table_header, headers):
        column.markdown(
            f"""
            <span style="
                font-size:12px;
                color:#6B7280;
            ">
                {heading}
            </span>
            """,
            unsafe_allow_html=True,
        )

    if recent_alerts_df.empty:
        st.info("No High or Critical alerts were found.")

    else:
        for _, alert in recent_alerts_df.iterrows():
            if pd.notna(alert["timestamp"]):
                time_text = alert["timestamp"].strftime(
                    "%b %d, %H:%M"
                )
            else:
                time_text = "Unknown"

            user_text = str(
                alert.get(
                    "employee_name",
                    alert["user_id"],
                )
            )

            role_text = str(alert["user_role"])

            activity_text = (
                str(alert["action"])
                .replace("_", " ")
                .title()
            )

            score = round(
                float(alert["final_score"]),
                1,
            )

            tier = str(alert["risk_tier"])

            row = st.columns(
                [1.4, 1.2, 1.2, 1.6, 0.7, 0.8]
            )

            row[0].markdown(
                f'<span style="font-size:13px">{time_text}</span>',
                unsafe_allow_html=True,
            )

            row[1].markdown(
                f'<span style="font-size:13px">{user_text}</span>',
                unsafe_allow_html=True,
            )

            row[2].markdown(
                f'<span style="font-size:13px">{role_text}</span>',
                unsafe_allow_html=True,
            )

            row[3].markdown(
                f'<span style="font-size:13px">{activity_text}</span>',
                unsafe_allow_html=True,
            )

            row[4].markdown(
                f"""
                <span style="
                    font-size:13px;
                    font-weight:600;
                ">
                    {score}
                </span>
                """,
                unsafe_allow_html=True,
            )

            row[5].markdown(
                f"""
                <span class="
                    badge {TIER_BADGE.get(tier, "badge-medium")}
                ">
                    {tier}
                </span>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("</div>", unsafe_allow_html=True)


with users_column:
    st.markdown(
        """
        <div class="panel">
            <p class="panel-title">
                Users with highest observed risk
            </p>
        """,
        unsafe_allow_html=True,
    )

    if top_users_df.empty:
        st.info("No user-risk records were found.")

    else:
        for _, user_row in top_users_df.iterrows():
            employee_name = str(
                user_row.get(
                    "employee_name",
                    user_row["user_id"],
                )
            )

            user_id = str(user_row["user_id"])
            user_role = str(user_row["user_role"])

            score = round(
                float(user_row["final_score"]),
                1,
            )

            bar_width = min(max(score, 0), 100)

            if score >= 80:
                bar_color = "#DC2626"
            elif score >= 55:
                bar_color = "#EA580C"
            elif score >= 30:
                bar_color = "#CA8A04"
            else:
                bar_color = "#16A34A"

            st.markdown(
                compact_html(
                    f"""
                <div style="margin-bottom:14px;">
                    <div style="
                        display:flex;
                        justify-content:space-between;
                        align-items:flex-start;
                        font-size:13px;
                        margin-bottom:4px;
                    ">
                        <div>
                            <span style="font-weight:600;">
                                {employee_name}
                            </span>

                            <br>

                            <span style="
                                color:#6B7280;
                                font-size:11px;
                            ">
                                {user_id} · {user_role}
                            </span>
                        </div>

                        <span style="font-weight:700;">
                            {score}
                        </span>
                    </div>

                    <div class="bar-track">
                        <div
                            class="bar-fill"
                            style="
                                width:{bar_width}%;
                                background:{bar_color};
                            "
                        ></div>
                    </div>
                </div>
                """
                ),
                unsafe_allow_html=True,
            )

    st.markdown("</div>", unsafe_allow_html=True)
