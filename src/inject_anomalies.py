from __future__ import annotations

import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd


SEED = 84
random.seed(SEED)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"

USERS_PATH = DATA_DIR / "users.csv"
NORMAL_LOGS_PATH = DATA_DIR / "activity_logs.csv"
LABELED_LOGS_PATH = DATA_DIR / "labeled_activity_logs.csv"

REFERENCE_TIME = datetime(2026, 7, 13, 18, 0, 0)


RESOURCE_SENSITIVITY: dict[str, int] = {
    "Core Banking Database": 5,
    "KYC Database": 5,
    "Customer Records Database": 5,
    "Database Backup Server": 4,
    "Identity Server": 5,
    "Linux Production Server": 4,
    "Windows Administration Server": 4,
    "Network Configuration System": 5,
    "SIEM Platform": 4,
    "Firewall Console": 5,
    "Identity and Access Management": 5,
    "Security Incident Repository": 4,
    "Internet Banking Application": 5,
    "Mobile Banking Application": 5,
    "Loan Processing System": 5,
    "Payment Gateway Console": 5,
    "Vendor Support Portal": 2,
    "Application Test Server": 2,
    "Approved Maintenance Server": 3,
    "Audit Log Repository": 4,
    "Compliance Reporting System": 3,
    "Read-Only Customer Records": 4,
    "Access Review Portal": 3,
}


SENSITIVE_RESOURCES = [
    resource
    for resource, sensitivity in RESOURCE_SENSITIVITY.items()
    if sensitivity >= 4
]


def split_pipe_values(value: str) -> list[str]:
    """
    Convert a pipe-separated profile value into a Python list.
    """

    return [
        item.strip()
        for item in value.split("|")
        if item.strip()
    ]


def generate_suspicious_timestamp(
    normal_start: int,
    normal_end: int,
    force_after_hours: bool = True,
) -> datetime:
    """
    Generate a recent suspicious event timestamp.

    When force_after_hours is True, the event occurs outside
    the user's normal login window.
    """

    day_offset = random.randint(0, 6)

    event_date = (
        REFERENCE_TIME - timedelta(days=day_offset)
    ).date()

    if force_after_hours:
        possible_hours = list(
            range(0, max(0, normal_start))
        )

        possible_hours += list(
            range(min(24, normal_end), 24)
        )

        event_hour = random.choice(
            possible_hours or [2, 3, 23]
        )

    else:
        event_hour = random.randint(0, 23)

    return datetime(
        year=event_date.year,
        month=event_date.month,
        day=event_date.day,
        hour=event_hour,
        minute=random.randint(0, 59),
        second=random.randint(0, 59),
    )


def choose_unusual_resource(
    approved_resources: list[str],
) -> str:
    """
    Choose a sensitive resource not normally used by the user.
    """

    candidates = [
        resource
        for resource in SENSITIVE_RESOURCES
        if resource not in approved_resources
    ]

    return random.choice(
        candidates or SENSITIVE_RESOURCES
    )


def build_event(
    user: pd.Series,
    *,
    action: str,
    resource: str,
    timestamp: datetime,
    device_id: str,
    ip_address: str,
    location: str,
    failed_attempts: int,
    data_downloaded_mb: float,
    privilege_change: bool,
    audit_log_disabled: bool,
    usual_device: bool,
    usual_resource: bool,
    approved_maintenance_window: bool,
) -> dict[str, Any]:
    """
    Build one suspicious event using the shared dataset schema.
    """

    return {
        "timestamp": timestamp.isoformat(
            sep=" "
        ),
        "user_id": user["user_id"],
        "user_role": user["user_role"],
        "department": user["department"],
        "action": action,
        "resource": resource,
        "resource_sensitivity": (
            RESOURCE_SENSITIVITY[resource]
        ),
        "login_hour": timestamp.hour,
        "device_id": device_id,
        "ip_address": ip_address,
        "location": location,
        "failed_attempts": failed_attempts,
        "data_downloaded_mb": round(
            float(data_downloaded_mb),
            2,
        ),
        "privilege_change": privilege_change,
        "audit_log_disabled": audit_log_disabled,
        "usual_device": usual_device,
        "usual_resource": usual_resource,
        "approved_maintenance_window": (
            approved_maintenance_window
        ),
        "label": "suspicious",
    }


def compromised_admin_event(
    user: pd.Series,
    event_number: int,
) -> dict[str, Any]:
    """
    Scenario 1:
    A privileged account logs in after hours from an
    unknown device and accesses an unusual sensitive system.
    """

    approved_resources = split_pipe_values(
        user["approved_resources"]
    )

    resource = choose_unusual_resource(
        approved_resources
    )

    timestamp = generate_suspicious_timestamp(
        normal_start=int(
            user["normal_login_start"]
        ),
        normal_end=int(
            user["normal_login_end"]
        ),
    )

    return build_event(
        user,
        action="suspicious_remote_login",
        resource=resource,
        timestamp=timestamp,
        device_id=(
            f"UNKNOWN-DEVICE-{event_number:03d}"
        ),
        ip_address=(
            f"185.220."
            f"{random.randint(1, 254)}."
            f"{random.randint(1, 254)}"
        ),
        location=random.choice(
            [
                "Unknown Foreign Location",
                "Unapproved Remote Network",
            ]
        ),
        failed_attempts=random.randint(2, 5),
        data_downloaded_mb=random.uniform(
            10,
            80,
        ),
        privilege_change=False,
        audit_log_disabled=False,
        usual_device=False,
        usual_resource=False,
        approved_maintenance_window=False,
    )


def data_exfiltration_event(
    user: pd.Series,
    event_number: int,
) -> dict[str, Any]:
    """
    Scenario 2:
    The user exports an abnormally large amount of
    sensitive customer information.
    """

    approved_devices = split_pipe_values(
        user["approved_devices"]
    )

    approved_locations = split_pipe_values(
        user["approved_locations"]
    )

    approved_resources = split_pipe_values(
        user["approved_resources"]
    )

    preferred_resources = [
        "KYC Database",
        "Customer Records Database",
        "Core Banking Database",
    ]

    resource = random.choice(
        preferred_resources
    )

    timestamp = generate_suspicious_timestamp(
        normal_start=int(
            user["normal_login_start"]
        ),
        normal_end=int(
            user["normal_login_end"]
        ),
        force_after_hours=random.choice(
            [True, True, False]
        ),
    )

    baseline_mean = float(
        user["normal_download_mean_mb"]
    )

    huge_download = max(
        baseline_mean * random.uniform(20, 60),
        random.uniform(1500, 5000),
    )

    return build_event(
        user,
        action="bulk_customer_data_export",
        resource=resource,
        timestamp=timestamp,
        device_id=random.choice(
            approved_devices
        ),
        ip_address=(
            f"10.90."
            f"{random.randint(1, 254)}."
            f"{random.randint(1, 254)}"
        ),
        location=random.choice(
            approved_locations
        ),
        failed_attempts=random.randint(0, 2),
        data_downloaded_mb=huge_download,
        privilege_change=False,
        audit_log_disabled=False,
        usual_device=True,
        usual_resource=(
            resource in approved_resources
        ),
        approved_maintenance_window=False,
    )


def privilege_abuse_event(
    user: pd.Series,
    event_number: int,
) -> dict[str, Any]:
    """
    Scenario 3:
    A privileged user repeatedly attempts access and
    changes account permissions.
    """

    approved_devices = split_pipe_values(
        user["approved_devices"]
    )

    resource = random.choice(
        [
            "Identity and Access Management",
            "Access Review Portal",
        ]
    )

    timestamp = generate_suspicious_timestamp(
        normal_start=int(
            user["normal_login_start"]
        ),
        normal_end=int(
            user["normal_login_end"]
        ),
    )

    return build_event(
        user,
        action="privilege_escalation_attempt",
        resource=resource,
        timestamp=timestamp,
        device_id=random.choice(
            approved_devices
        ),
        ip_address=(
            f"10.91."
            f"{random.randint(1, 254)}."
            f"{random.randint(1, 254)}"
        ),
        location=(
            "Unapproved Administrative Network"
        ),
        failed_attempts=random.randint(4, 9),
        data_downloaded_mb=random.uniform(
            1,
            20,
        ),
        privilege_change=True,
        audit_log_disabled=False,
        usual_device=True,
        usual_resource=(
            resource
            in split_pipe_values(
                user["approved_resources"]
            )
        ),
        approved_maintenance_window=False,
    )


def evidence_tampering_event(
    user: pd.Series,
    event_number: int,
) -> dict[str, Any]:
    """
    Scenario 4:
    A user disables audit logging before accessing
    security evidence.
    """

    timestamp = generate_suspicious_timestamp(
        normal_start=int(
            user["normal_login_start"]
        ),
        normal_end=int(
            user["normal_login_end"]
        ),
    )

    resource = "Audit Log Repository"

    return build_event(
        user,
        action="disable_audit_logging",
        resource=resource,
        timestamp=timestamp,
        device_id=(
            f"UNKNOWN-FORENSIC-"
            f"{event_number:03d}"
        ),
        ip_address=(
            f"203.0.113."
            f"{random.randint(1, 254)}"
        ),
        location="Unknown Remote Session",
        failed_attempts=random.randint(1, 4),
        data_downloaded_mb=random.uniform(
            20,
            150,
        ),
        privilege_change=random.choice(
            [False, True]
        ),
        audit_log_disabled=True,
        usual_device=False,
        usual_resource=(
            resource
            in split_pipe_values(
                user["approved_resources"]
            )
        ),
        approved_maintenance_window=False,
    )


def generate_suspicious_events(
    users_df: pd.DataFrame,
    events_per_scenario: int = 15,
) -> pd.DataFrame:
    """
    Generate four attack scenarios.

    Four scenarios x 15 events = 60 suspicious events.
    """

    eligible_admins = users_df[
        users_df["user_role"].isin(
            [
                "Database Administrator",
                "System Administrator",
                "Security Administrator",
                "Application Administrator",
            ]
        )
    ]

    events: list[dict[str, Any]] = []

    scenario_builders = [
        compromised_admin_event,
        data_exfiltration_event,
        privilege_abuse_event,
        evidence_tampering_event,
    ]

    for builder in scenario_builders:
        for event_number in range(
            1,
            events_per_scenario + 1,
        ):
            user = eligible_admins.sample(
                n=1,
                random_state=SEED + len(events),
            ).iloc[0]

            event = builder(
                user=user,
                event_number=event_number,
            )

            events.append(event)

    return pd.DataFrame(events)


def main() -> None:
    if not USERS_PATH.exists():
        raise FileNotFoundError(
            "data/users.csv not found. "
            "Run python src/generate_data.py first."
        )

    if not NORMAL_LOGS_PATH.exists():
        raise FileNotFoundError(
            "data/activity_logs.csv not found. "
            "Run python src/generate_activity.py first."
        )

    users_df = pd.read_csv(
        USERS_PATH
    )

    normal_df = pd.read_csv(
        NORMAL_LOGS_PATH
    )

    suspicious_df = generate_suspicious_events(
        users_df=users_df,
        events_per_scenario=15,
    )

    combined_df = pd.concat(
        [
            normal_df,
            suspicious_df,
        ],
        ignore_index=True,
    )

    combined_df["timestamp"] = pd.to_datetime(
        combined_df["timestamp"]
    )

    combined_df = combined_df.sort_values(
        by="timestamp"
    ).reset_index(drop=True)

    combined_df["timestamp"] = combined_df[
        "timestamp"
    ].dt.strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    combined_df.to_csv(
        LABELED_LOGS_PATH,
        index=False,
    )

    print("=" * 60)
    print(
        "SentinelAI suspicious events injected"
    )
    print("=" * 60)
    print(f"Normal events: {len(normal_df)}")
    print(
        f"Suspicious events: "
        f"{len(suspicious_df)}"
    )
    print(
        f"Combined events: "
        f"{len(combined_df)}"
    )
    print()

    print("Labels:")
    print(
        combined_df["label"]
        .value_counts()
        .to_string()
    )
    print()

    print("Suspicious scenarios:")
    print(
        suspicious_df["action"]
        .value_counts()
        .to_string()
    )
    print()

    print(
        f"Saved to: {LABELED_LOGS_PATH}"
    )


if __name__ == "__main__":
    main()