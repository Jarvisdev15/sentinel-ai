from __future__ import annotations

from html import escape
from textwrap import dedent
from typing import Any

import pandas as pd
import streamlit as st

from app import load_css
from src.dashboard_data import load_dashboard_data


st.set_page_config(
    page_title="Live Alerts - SentinelAI",
    layout="wide",
)

load_css()


def render_html(content: str) -> None:
    """Render multiline HTML without showing it as a code block."""
    st.markdown(
        dedent(content).strip(),
        unsafe_allow_html=True,
    )


def readable_text(value: Any) -> str:
    """Convert snake_case values into readable labels."""
    if value is None:
        return "Unknown"

    return str(value).replace("_", " ").strip().title()


def format_reasons(row: pd.Series) -> str:
    """Return clean readable reasons for CSV or simulated alerts."""

    reasons_text = row.get("reasons_text")

    if isinstance(reasons_text, str) and reasons_text.strip():
        return reasons_text

    reasons = row.get("reasons")

    if isinstance(reasons, list):
        return ", ".join(str(reason) for reason in reasons)

    if reasons is not None and not pd.isna(reasons):
        return str(reasons)

    rule_reasons = row.get("rule_reasons")

    if isinstance(rule_reasons, str) and rule_reasons.strip():
        return rule_reasons

    return "None"


TIER_BADGES = {
    "Low": "badge-low",
    "Medium": "badge-medium",
    "High": "badge-high",
    "Critical": "badge-critical",
}


# ------------------------------------------------------------------
# Load real scored activity data
# ------------------------------------------------------------------
try:
    alerts_df = load_dashboard_data().copy()
except Exception as error:
    st.error("SentinelAI could not load the scored activity dataset.")
    st.code(f"{type(error).__name__}: {error}")
    st.stop()

alerts_df["source"] = "Observed"


# ------------------------------------------------------------------
# Add incidents created from Attack Simulation, when available
# ------------------------------------------------------------------
simulated_alerts = st.session_state.get("simulated_alerts", [])

if simulated_alerts:
    simulated_df = pd.DataFrame(simulated_alerts)
    simulated_df["source"] = "Simulated"
    simulated_df["is_simulated"] = True

    if "timestamp" in simulated_df.columns:
        simulated_df["timestamp"] = pd.to_datetime(
            simulated_df["timestamp"],
            errors="coerce",
        )

    if "employee_name" not in simulated_df.columns:
        simulated_df["employee_name"] = simulated_df.get(
            "user_id",
            "Simulated User",
        )

    if "reasons_text" not in simulated_df.columns:
        simulated_df["reasons_text"] = simulated_df.apply(
            format_reasons,
            axis=1,
        )

    alerts_df = pd.concat(
        [simulated_df, alerts_df],
        ignore_index=True,
        sort=False,
    )


# Ensure timestamp is usable after combining data
alerts_df["timestamp"] = pd.to_datetime(
    alerts_df["timestamp"],
    errors="coerce",
)

alerts_df = alerts_df.sort_values(
    "timestamp",
    ascending=False,
    na_position="last",
)


# ------------------------------------------------------------------
# Page heading
# ------------------------------------------------------------------
st.title("Live Alerts")

st.caption(
    "Review scored privileged-user events, their explanations and "
    "recommended security responses."
)

if simulated_alerts:
    simulation_message, simulation_control = st.columns([4, 1])

    with simulation_message:
        st.info(
            f"{len(simulated_alerts)} simulated alert(s) are active. "
            "They are labelled Simulated in the queue."
        )

    with simulation_control:
        if st.button(
            "End simulated attacks",
            use_container_width=True,
        ):
            st.session_state.simulated_alerts = []
            st.session_state.sim_result = None
            st.session_state.sim_name = None
            st.session_state.sim_evidence = None
            st.rerun()


# ------------------------------------------------------------------
# Filters
# ------------------------------------------------------------------
filter_col1, filter_col2, filter_col3 = st.columns([1.4, 1.4, 1])

with filter_col1:
    selected_tiers = st.multiselect(
        "Risk tier",
        options=["Low", "Medium", "High", "Critical"],
        default=["High", "Critical"],
    )

with filter_col2:
    search_text = st.text_input(
        "Search",
        placeholder="User, role, action or resource",
    )

with filter_col3:
    maximum_rows = st.selectbox(
        "Maximum alerts",
        options=[10, 25, 50, 100],
        index=1,
    )


filtered_df = alerts_df.copy()

if selected_tiers:
    filtered_df = filtered_df[
        filtered_df["risk_tier"].isin(selected_tiers)
    ]

if search_text.strip():
    query = search_text.strip().lower()

    searchable_columns = [
        "user_id",
        "employee_name",
        "user_role",
        "action",
        "resource",
    ]

    search_mask = pd.Series(
        False,
        index=filtered_df.index,
    )

    for column in searchable_columns:
        if column in filtered_df.columns:
            search_mask = search_mask | (
                filtered_df[column]
                .fillna("")
                .astype(str)
                .str.lower()
                .str.contains(
                    query,
                    regex=False,
                )
            )

    filtered_df = filtered_df[search_mask]


display_df = filtered_df.head(maximum_rows)


# ------------------------------------------------------------------
# Alert summary
# ------------------------------------------------------------------
summary_col1, summary_col2, summary_col3 = st.columns(3)

summary_col1.metric(
    "Matching alerts",
    f"{len(filtered_df):,}",
)

summary_col2.metric(
    "Critical",
    f"{int((filtered_df['risk_tier'] == 'Critical').sum()):,}",
)

summary_col3.metric(
    "High",
    f"{int((filtered_df['risk_tier'] == 'High').sum()):,}",
)

st.write("")


# ------------------------------------------------------------------
# Alerts table
# ------------------------------------------------------------------
render_html(
    """
    <p class="panel-title">Analyst alert queue</p>
    """
)

header_columns = st.columns(
    [1.15, 1.05, 1.05, 1.3, 1.3, 0.65, 0.75, 0.8]
)

headings = [
    "Time",
    "User",
    "Role",
    "Activity",
    "Resource",
    "Score",
    "Tier",
    "Source",
]

for column, heading in zip(header_columns, headings):
    with column:
        render_html(
            f"""
            <span style="
                font-size:12px;
                color:#6B7280;
                font-weight:600;
            ">
                {escape(heading)}
            </span>
            """
        )


if display_df.empty:
    st.info("No alerts match the selected filters.")

else:
    for row_number, (_, alert) in enumerate(
        display_df.iterrows(),
        start=1,
    ):
        timestamp = alert.get("timestamp")

        if pd.notna(timestamp):
            time_text = timestamp.strftime("%b %d, %H:%M")
        else:
            time_text = "Unknown"

        user_id = str(alert.get("user_id", "Unknown"))

        employee_name = alert.get("employee_name", user_id)

        if pd.isna(employee_name):
            employee_name = user_id

        role_text = str(
            alert.get("user_role", "Unknown")
        )

        action_text = readable_text(
            alert.get("action", "Unknown")
        )

        resource_text = readable_text(
            alert.get("resource", "Unknown")
        )

        final_score = float(
            alert.get("final_score", 0)
        )

        risk_tier = str(
            alert.get("risk_tier", "Medium")
        )

        source = str(alert.get("source", "Observed"))

        recommended_action = str(
            alert.get(
                "recommended_action",
                "No response recommendation available.",
            )
        )

        reasons_text = format_reasons(alert)

        row_columns = st.columns(
            [1.15, 1.05, 1.05, 1.3, 1.3, 0.65, 0.75, 0.8]
        )

        row_values = [
            time_text,
            employee_name,
            role_text,
            action_text,
            resource_text,
        ]

        for column, value in zip(
            row_columns[:5],
            row_values,
        ):
            with column:
                render_html(
                    f"""
                    <span style="font-size:13px;">
                        {escape(str(value))}
                    </span>
                    """
                )

        with row_columns[5]:
            render_html(
                f"""
                <span style="
                    font-size:13px;
                    font-weight:700;
                ">
                    {final_score:.1f}
                </span>
                """
            )

        with row_columns[6]:
            badge_class = TIER_BADGES.get(
                risk_tier,
                "badge-medium",
            )

            render_html(
                f"""
                <span class="badge {badge_class}">
                    {escape(risk_tier)}
                </span>
                """
            )

        with row_columns[7]:
            if source == "Simulated":
                render_html(
                    """
                    <span class="badge badge-medium">
                        Simulated
                    </span>
                    """
                )
            else:
                render_html(
                    """
                    <span style="font-size:12px;color:#6B7280;">
                        Observed
                    </span>
                    """
                )

        with st.expander(
            f"Alert details — {employee_name} · {time_text}",
            expanded=False,
        ):
            detail_col1, detail_col2 = st.columns(2)

            with detail_col1:
                st.markdown("#### Incident")

                st.write(f"**User ID:** {user_id}")
                st.write(f"**Role:** {role_text}")
                st.write(f"**Action:** {action_text}")
                st.write(f"**Resource:** {resource_text}")
                st.write(f"**Final risk score:** {final_score:.1f}")
                st.write(f"**Risk tier:** {risk_tier}")
                st.write(f"**Source:** {source}")

                incident_id = alert.get("incident_id")
                if incident_id is not None and not pd.isna(incident_id):
                    st.write(f"**Incident ID:** {incident_id}")

            with detail_col2:
                st.markdown("#### Analyst explanation")

                st.write(f"**Reasons:** {reasons_text}")
                st.write(
                    f"**Recommended action:** "
                    f"{recommended_action}"
                )

                if source == "Simulated":
                    original_verified = alert.get(
                        "evidence_original_verified"
                    )
                    tampered_verified = alert.get(
                        "evidence_tampered_verified"
                    )

                    if original_verified and tampered_verified is False:
                        integrity_text = (
                            "Original verified; tampered copy rejected"
                        )
                    elif original_verified and tampered_verified is None:
                        integrity_text = (
                            "Original verified; tamper test not run"
                        )
                    else:
                        integrity_text = "Evidence verification needs review"

                    st.write(f"**Evidence integrity:** {integrity_text}")

            rule_score = alert.get("rule_score")
            ml_score = alert.get("ml_score")

            score_col1, score_col2 = st.columns(2)

            with score_col1:
                if rule_score is not None and not pd.isna(rule_score):
                    st.metric(
                        "Rule score",
                        f"{float(rule_score):.1f}",
                    )

            with score_col2:
                if ml_score is not None and not pd.isna(ml_score):
                    st.metric(
                        "ML anomaly score",
                        f"{float(ml_score):.1f}",
                    )


if len(filtered_df) > maximum_rows:
    st.caption(
        f"Showing the latest {maximum_rows} of "
        f"{len(filtered_df):,} matching alerts."
    )
