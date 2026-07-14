from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCORED_DATA_PATH = (
    PROJECT_ROOT / "data" / "response_scored_activity_logs.csv"
)
USERS_DATA_PATH = PROJECT_ROOT / "data" / "users.csv"


def parse_reasons(value: Any) -> list[str]:
    """Convert the CSV rule_reasons value into a clean Python list."""

    if isinstance(value, list):
        return [str(reason) for reason in value]

    if pd.isna(value):
        return []

    try:
        parsed = json.loads(str(value))

        if isinstance(parsed, list):
            return [str(reason) for reason in parsed]
    except (json.JSONDecodeError, TypeError):
        pass

    return [str(value)]


@st.cache_data
def load_dashboard_data() -> pd.DataFrame:
    """Load and prepare the main scored activity dataset."""

    if not SCORED_DATA_PATH.exists():
        raise FileNotFoundError(
            f"Scored dataset not found: {SCORED_DATA_PATH}"
        )

    df = pd.read_csv(SCORED_DATA_PATH)

    required_columns = {
        "timestamp",
        "user_id",
        "user_role",
        "action",
        "resource",
        "rule_score",
        "ml_score",
        "final_score",
        "risk_tier",
        "rule_reasons",
        "recommended_action",
    }

    missing_columns = required_columns.difference(df.columns)

    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Dataset is missing columns: {missing}")

    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        errors="coerce",
    )

    df["reasons_list"] = df["rule_reasons"].apply(parse_reasons)

    df["reasons_text"] = df["reasons_list"].apply(
        lambda reasons: ", ".join(reasons) if reasons else "None"
    )

    # Add employee names from users.csv when available.
    if USERS_DATA_PATH.exists():
        users_df = pd.read_csv(USERS_DATA_PATH)

        if {"user_id", "employee_name"}.issubset(users_df.columns):
            df = df.merge(
                users_df[["user_id", "employee_name"]],
                on="user_id",
                how="left",
            )

    if "employee_name" not in df.columns:
        df["employee_name"] = df["user_id"]

    df["employee_name"] = df["employee_name"].fillna(df["user_id"])

    return df