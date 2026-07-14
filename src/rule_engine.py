from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"

USERS_PATH = DATA_DIR / "users.csv"
LABELED_LOGS_PATH = DATA_DIR / "labeled_activity_logs.csv"
RULE_SCORED_PATH = DATA_DIR / "rule_scored_activity_logs.csv"


RULE_WEIGHTS: dict[str, int] = {
    "after_hours_login": 15,
    "unknown_device": 20,
    "unusual_resource": 20,
    "repeated_failed_attempts": 15,
    "mass_download": 25,
    "privilege_escalation": 30,
    "audit_logging_disabled": 35,
    "sensitive_data_access": 20,
}


def split_pipe_values(value: str) -> list[str]:
    """
    Convert pipe-separated profile values into a list.
    """

    return [
        item.strip()
        for item in str(value).split("|")
        if item.strip()
    ]


def to_bool(value: Any) -> bool:
    """
    Safely convert CSV boolean values to Python booleans.
    """

    if isinstance(value, bool):
        return value

    if pd.isna(value):
        return False

    return str(value).strip().lower() in {
        "true",
        "1",
        "yes",
    }


def calculate_rule_score(
    event: Mapping[str, Any],
    user_profile: Mapping[str, Any],
) -> dict[str, Any]:
    """
    Evaluate the eight explainable security rules.

    Returns:
    - capped rule score
    - triggered-rule reasons
    - individual rule flags
    """

    reasons: list[str] = []
    triggered_rules: dict[str, bool] = {
        rule_name: False
        for rule_name in RULE_WEIGHTS
    }

    login_hour = int(event["login_hour"])

    normal_start = int(
        user_profile["normal_login_start"]
    )
    normal_end = int(
        user_profile["normal_login_end"]
    )

    approved_devices = set(
        split_pipe_values(
            user_profile["approved_devices"]
        )
    )

    approved_resources = set(
        split_pipe_values(
            user_profile["approved_resources"]
        )
    )

    event_device = str(event["device_id"])
    event_resource = str(event["resource"])

    # Rule 1: After-hours login
    if not normal_start <= login_hour < normal_end:
        triggered_rules["after_hours_login"] = True
        reasons.append(
            f"After-hours login at {login_hour}:00; "
            f"normal window is "
            f"{normal_start}:00-{normal_end}:00"
        )

    # Rule 2: Unknown device
    usual_device = to_bool(
        event.get(
            "usual_device",
            event_device in approved_devices,
        )
    )

    if (
        not usual_device
        or event_device not in approved_devices
    ):
        triggered_rules["unknown_device"] = True
        reasons.append(
            f"Unknown or unapproved device: "
            f"{event_device}"
        )

    # Rule 3: Unusual resource
    usual_resource = to_bool(
        event.get(
            "usual_resource",
            event_resource in approved_resources,
        )
    )

    if (
        not usual_resource
        or event_resource not in approved_resources
    ):
        triggered_rules["unusual_resource"] = True
        reasons.append(
            f"Unusual resource access: "
            f"{event_resource}"
        )

    # Rule 4: Repeated failed attempts
    failed_attempts = int(
        event.get("failed_attempts", 0)
    )

    if failed_attempts >= 3:
        triggered_rules[
            "repeated_failed_attempts"
        ] = True

        reasons.append(
            f"{failed_attempts} failed access attempts"
        )

    # Rule 5: Mass download
    download_mb = float(
        event.get("data_downloaded_mb", 0)
    )

    baseline_mean = float(
        user_profile[
            "normal_download_mean_mb"
        ]
    )

    baseline_std = float(
        user_profile[
            "normal_download_std_mb"
        ]
    )

    mass_download_threshold = max(
        baseline_mean * 3,
        baseline_mean + (3 * baseline_std),
    )

    if download_mb > mass_download_threshold:
        triggered_rules["mass_download"] = True

        reasons.append(
            f"Abnormal download of "
            f"{download_mb:.2f} MB; "
            f"threshold is "
            f"{mass_download_threshold:.2f} MB"
        )

    # Rule 6: Privilege escalation
    if to_bool(
        event.get("privilege_change", False)
    ):
        triggered_rules[
            "privilege_escalation"
        ] = True

        reasons.append(
            "Privilege escalation or permission "
            "change detected"
        )

    # Rule 7: Audit logging disabled
    if to_bool(
        event.get(
            "audit_log_disabled",
            False,
        )
    ):
        triggered_rules[
            "audit_logging_disabled"
        ] = True

        reasons.append(
            "Audit logging was disabled"
        )

    # Rule 8: Sensitive-data access
    resource_sensitivity = int(
        event.get(
            "resource_sensitivity",
            0,
        )
    )

    if resource_sensitivity >= 4:
        triggered_rules[
            "sensitive_data_access"
        ] = True

        reasons.append(
            f"Accessed high-sensitivity resource: "
            f"{event_resource}"
        )

    raw_score = sum(
        RULE_WEIGHTS[rule_name]
        for rule_name, triggered
        in triggered_rules.items()
        if triggered
    )

    rule_score = min(raw_score, 100)

    if not reasons:
        reasons.append(
            "No rule-based risk indicators detected"
        )

    return {
        "rule_score": rule_score,
        "reasons": reasons,
        "triggered_rules": triggered_rules,
    }


def score_all_events(
    events_df: pd.DataFrame,
    users_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Apply the rule engine to every activity record.
    """

    user_lookup = users_df.set_index(
        "user_id"
    ).to_dict(
        orient="index"
    )

    scored_rows: list[dict[str, Any]] = []

    for _, event in events_df.iterrows():
        user_id = str(event["user_id"])

        if user_id not in user_lookup:
            raise KeyError(
                f"No user profile found for {user_id}"
            )

        result = calculate_rule_score(
            event=event.to_dict(),
            user_profile=user_lookup[user_id],
        )

        scored_event = event.to_dict()

        scored_event["rule_score"] = result[
            "rule_score"
        ]

        scored_event["rule_reasons"] = json.dumps(
            result["reasons"]
        )

        scored_event["triggered_rules"] = json.dumps(
            result["triggered_rules"]
        )

        scored_rows.append(scored_event)

    return pd.DataFrame(scored_rows)


def main() -> None:
    if not USERS_PATH.exists():
        raise FileNotFoundError(
            "data/users.csv not found."
        )

    if not LABELED_LOGS_PATH.exists():
        raise FileNotFoundError(
            "data/labeled_activity_logs.csv "
            "not found."
        )

    users_df = pd.read_csv(USERS_PATH)

    events_df = pd.read_csv(
        LABELED_LOGS_PATH
    )

    scored_df = score_all_events(
        events_df=events_df,
        users_df=users_df,
    )

    scored_df.to_csv(
        RULE_SCORED_PATH,
        index=False,
    )

    print("=" * 60)
    print("SentinelAI rule engine completed")
    print("=" * 60)
    print(f"Events scored: {len(scored_df)}")
    print()

    print("Average rule score by label:")
    print(
        scored_df.groupby("label")[
            "rule_score"
        ]
        .mean()
        .round(2)
        .to_string()
    )
    print()

    print("Maximum rule score by label:")
    print(
        scored_df.groupby("label")[
            "rule_score"
        ]
        .max()
        .to_string()
    )
    print()

    high_risk_count = (
        scored_df["rule_score"] >= 55
    ).sum()

    print(
        f"Events with rule score >= 55: "
        f"{high_risk_count}"
    )
    print(f"Saved to: {RULE_SCORED_PATH}")


if __name__ == "__main__":
    main()