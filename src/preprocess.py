from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


NUMERIC_FEATURES = [
    "login_hour",
    "resource_sensitivity",
    "failed_attempts",
    "data_downloaded_mb",
    "privilege_change",
    "audit_log_disabled",
    "usual_device",
    "usual_resource",
    "approved_maintenance_window",
]


def to_binary(value: Any) -> int:
    """
    Convert booleans and CSV boolean strings into 0 or 1.
    """

    if isinstance(value, bool):
        return int(value)

    if pd.isna(value):
        return 0

    return int(
        str(value).strip().lower()
        in {"true", "1", "yes"}
    )


def build_ml_features(
    events_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Convert activity-log fields into numerical ML features.
    """

    required_columns = set(NUMERIC_FEATURES)

    missing_columns = required_columns.difference(
        events_df.columns
    )

    if missing_columns:
        raise ValueError(
            "Missing required ML columns: "
            f"{sorted(missing_columns)}"
        )

    features_df = pd.DataFrame(
        index=events_df.index
    )

    features_df["login_hour"] = pd.to_numeric(
        events_df["login_hour"],
        errors="coerce",
    ).fillna(0)

    features_df[
        "resource_sensitivity"
    ] = pd.to_numeric(
        events_df["resource_sensitivity"],
        errors="coerce",
    ).fillna(0)

    features_df[
        "failed_attempts"
    ] = pd.to_numeric(
        events_df["failed_attempts"],
        errors="coerce",
    ).fillna(0)

    features_df[
        "data_downloaded_mb"
    ] = pd.to_numeric(
        events_df["data_downloaded_mb"],
        errors="coerce",
    ).fillna(0)

    for column in [
        "privilege_change",
        "audit_log_disabled",
        "usual_device",
        "usual_resource",
        "approved_maintenance_window",
    ]:
        features_df[column] = events_df[
            column
        ].map(to_binary)

    # Invert normality indicators so larger values mean higher risk.
    features_df["unknown_device"] = (
        1 - features_df["usual_device"]
    )

    features_df["unusual_resource"] = (
        1 - features_df["usual_resource"]
    )

    features_df[
        "outside_maintenance_window"
    ] = (
        1
        - features_df[
            "approved_maintenance_window"
        ]
    )

    # Cyclical hour representation:
    # 23:00 and 00:00 should be close together.
    features_df["login_hour_sin"] = np.sin(
        2
        * np.pi
        * features_df["login_hour"]
        / 24
    )

    features_df["login_hour_cos"] = np.cos(
        2
        * np.pi
        * features_df["login_hour"]
        / 24
    )

    # Reduce extreme scale while preserving anomaly ordering.
    features_df[
        "log_download_mb"
    ] = np.log1p(
        features_df["data_downloaded_mb"]
        .clip(lower=0)
    )

    model_columns = [
        "login_hour_sin",
        "login_hour_cos",
        "resource_sensitivity",
        "failed_attempts",
        "log_download_mb",
        "privilege_change",
        "audit_log_disabled",
        "unknown_device",
        "unusual_resource",
        "outside_maintenance_window",
    ]

    model_features = features_df[
        model_columns
    ].astype(float)

    if model_features.isnull().any().any():
        raise ValueError(
            "ML feature matrix contains missing values."
        )

    return model_features