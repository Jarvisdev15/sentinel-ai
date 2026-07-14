from __future__ import annotations

import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


SEED = 42

random.seed(SEED)
np.random.seed(SEED)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"

USERS_PATH = DATA_DIR / "users.csv"
ACTIVITY_LOGS_PATH = DATA_DIR / "activity_logs.csv"

REFERENCE_TIME = datetime(2026, 7, 13, 18, 0, 0)


ACTIONS_BY_ROLE: dict[str, list[str]] = {
    "Database Administrator": [
        "database_login",
        "run_query",
        "backup_database",
        "review_database_logs",
        "download_report",
    ],
    "System Administrator": [
        "server_login",
        "check_server_health",
        "update_configuration",
        "review_system_logs",
        "download_report",
    ],
    "Security Administrator": [
        "review_security_alert",
        "investigate_incident",
        "update_firewall_rule",
        "review_access_logs",
        "download_report",
    ],
    "Application Administrator": [
        "application_login",
        "review_application_logs",
        "update_application_config",
        "check_service_health",
        "download_report",
    ],
    "External Vendor": [
        "vendor_portal_login",
        "perform_maintenance",
        "review_test_logs",
        "upload_patch",
        "download_report",
    ],
    "Privileged Auditor": [
        "audit_login",
        "review_audit_logs",
        "review_access_records",
        "generate_compliance_report",
        "download_report",
    ],
}


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


def split_pipe_values(value: str) -> list[str]:
    return [
        item.strip()
        for item in value.split("|")
        if item.strip()
    ]


def generate_private_ip(user_id: str) -> str:
    role_octets = {
        "DBA": 10,
        "SYS": 20,
        "SEC": 30,
        "APP": 40,
        "VEN": 50,
        "AUD": 60,
    }

    prefix, user_number_text = user_id.split("-")
    user_number = int(user_number_text)

    return (
        f"10.{role_octets[prefix]}."
        f"{user_number}.{random.randint(10, 240)}"
    )


def generate_normal_timestamp(
    login_start: int,
    login_end: int,
    days_back: int = 14,
) -> datetime:
    day_offset = random.randint(0, days_back - 1)

    event_date = (
        REFERENCE_TIME - timedelta(days=day_offset)
    ).date()

    latest_valid_hour = max(
        login_start,
        login_end - 1,
    )

    event_hour = random.randint(
        login_start,
        latest_valid_hour,
    )

    return datetime(
        year=event_date.year,
        month=event_date.month,
        day=event_date.day,
        hour=event_hour,
        minute=random.randint(0, 59),
        second=random.randint(0, 59),
    )


def generate_normal_activity(
    users_df: pd.DataFrame,
    events_per_user: int = 20,
) -> pd.DataFrame:
    events: list[dict[str, Any]] = []

    for _, user in users_df.iterrows():
        approved_devices = split_pipe_values(
            user["approved_devices"]
        )

        approved_resources = split_pipe_values(
            user["approved_resources"]
        )

        approved_locations = split_pipe_values(
            user["approved_locations"]
        )

        normal_actions = ACTIONS_BY_ROLE[
            user["user_role"]
        ]

        for _ in range(events_per_user):
            timestamp = generate_normal_timestamp(
                login_start=int(
                    user["normal_login_start"]
                ),
                login_end=int(
                    user["normal_login_end"]
                ),
            )

            action = random.choice(normal_actions)
            resource = random.choice(
                approved_resources
            )

            if action == "download_report":
                data_downloaded_mb = np.random.normal(
                    loc=float(
                        user["normal_download_mean_mb"]
                    ),
                    scale=float(
                        user["normal_download_std_mb"]
                    ),
                )

                data_downloaded_mb = max(
                    0.1,
                    data_downloaded_mb,
                )

            else:
                data_downloaded_mb = max(
                    0.0,
                    np.random.normal(
                        loc=2.0,
                        scale=1.0,
                    ),
                )

            event = {
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
                "device_id": random.choice(
                    approved_devices
                ),
                "ip_address": generate_private_ip(
                    user["user_id"]
                ),
                "location": random.choice(
                    approved_locations
                ),
                "failed_attempts": random.choices(
                    population=[0, 1],
                    weights=[95, 5],
                    k=1,
                )[0],
                "data_downloaded_mb": round(
                    float(data_downloaded_mb),
                    2,
                ),
                "privilege_change": False,
                "audit_log_disabled": False,
                "usual_device": True,
                "usual_resource": True,
                "approved_maintenance_window": True,
                "label": "normal",
            }

            events.append(event)

    events_df = pd.DataFrame(events)

    return events_df.sort_values(
        by="timestamp"
    ).reset_index(drop=True)


def main() -> None:
    if not USERS_PATH.exists():
        raise FileNotFoundError(
            "data/users.csv was not found. "
            "Run python src/generate_data.py first."
        )

    users_df = pd.read_csv(USERS_PATH)

    events_df = generate_normal_activity(
        users_df=users_df,
        events_per_user=20,
    )

    events_df.to_csv(
        ACTIVITY_LOGS_PATH,
        index=False,
    )

    print("=" * 60)
    print("SentinelAI normal activity logs generated")
    print("=" * 60)
    print(f"Users loaded: {len(users_df)}")
    print(f"Events generated: {len(events_df)}")
    print(f"Unique users: {events_df['user_id'].nunique()}")
    print(f"Labels: {events_df['label'].value_counts().to_dict()}")
    print(f"Saved to: {ACTIVITY_LOGS_PATH}")


if __name__ == "__main__":
    main()