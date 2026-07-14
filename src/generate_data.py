from __future__ import annotations

import random
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from faker import Faker

# ---------------------------------------------------------
# Reproducibility
# ---------------------------------------------------------

SEED = 42

random.seed(SEED)
np.random.seed(SEED)

fake = Faker("en_IN")
Faker.seed(SEED)


# ---------------------------------------------------------
# Project paths
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"

DATA_DIR.mkdir(parents=True, exist_ok=True)
# ---------------------------------------------------------
# Banking privileged-user persona templates
# ---------------------------------------------------------

PERSONA_TEMPLATES: dict[str, dict[str, Any]] = {
    "Database Administrator": {
        "prefix": "DBA",
        "department": "Database Operations",
        "login_window": (8, 18),
        "locations": ["Mumbai HQ", "Pune Data Centre"],
        "resources": [
            "Core Banking Database",
            "KYC Database",
            "Customer Records Database",
            "Database Backup Server",
        ],
        "devices_per_user": 2,
        "download_mean_mb": 75,
        "download_std_mb": 25,
        "maintenance_window": "Sunday 01:00-05:00",
    },

    "System Administrator": {
        "prefix": "SYS",
        "department": "Infrastructure Operations",
        "login_window": (7, 19),
        "locations": ["Mumbai HQ", "Pune Data Centre"],
        "resources": [
            "Identity Server",
            "Linux Production Server",
            "Windows Administration Server",
            "Network Configuration System",
        ],
        "devices_per_user": 2,
        "download_mean_mb": 40,
        "download_std_mb": 15,
        "maintenance_window": "Saturday 22:00-Sunday 04:00",
    },

    "Security Administrator": {
        "prefix": "SEC",
        "department": "Cyber Security Operations",
        "login_window": (6, 22),
        "locations": ["Mumbai SOC", "Pune Data Centre"],
        "resources": [
            "SIEM Platform",
            "Firewall Console",
            "Identity and Access Management",
            "Security Incident Repository",
        ],
        "devices_per_user": 2,
        "download_mean_mb": 25,
        "download_std_mb": 10,
        "maintenance_window": "Any approved incident window",
    },

    "Application Administrator": {
        "prefix": "APP",
        "department": "Application Operations",
        "login_window": (8, 20),
        "locations": ["Mumbai HQ", "Pune Technology Centre"],
        "resources": [
            "Internet Banking Application",
            "Mobile Banking Application",
            "Loan Processing System",
            "Payment Gateway Console",
        ],
        "devices_per_user": 2,
        "download_mean_mb": 35,
        "download_std_mb": 12,
        "maintenance_window": "Saturday 23:00-Sunday 03:00",
    },

    "External Vendor": {
        "prefix": "VEN",
        "department": "Third-Party Services",
        "login_window": (10, 17),
        "locations": ["Approved Vendor Network"],
        "resources": [
            "Vendor Support Portal",
            "Application Test Server",
            "Approved Maintenance Server",
        ],
        "devices_per_user": 1,
        "download_mean_mb": 15,
        "download_std_mb": 7,
        "maintenance_window": "Sunday 10:00-14:00",
    },

    "Privileged Auditor": {
        "prefix": "AUD",
        "department": "Internal Audit",
        "login_window": (9, 18),
        "locations": ["Mumbai HQ", "Regional Audit Office"],
        "resources": [
            "Audit Log Repository",
            "Compliance Reporting System",
            "Read-Only Customer Records",
            "Access Review Portal",
        ],
        "devices_per_user": 1,
        "download_mean_mb": 50,
        "download_std_mb": 18,
        "maintenance_window": "Not applicable",
    },
}

def create_device_ids(
    prefix: str,
    user_number: int,
    count: int,
) -> list[str]:
    """
    Create approved device IDs for one privileged user.
    """

    return [
        f"{prefix}-{user_number:03d}-DEV-{device_number:02d}"
        for device_number in range(1, count + 1)
    ]


def generate_users(users_per_persona: int = 5) -> pd.DataFrame:
    """
    Generate individual privileged users from the persona templates.
    """

    users: list[dict[str, Any]] = []

    for role, template in PERSONA_TEMPLATES.items():
        prefix = template["prefix"]
        base_login_start, base_login_end = template["login_window"]

        for user_number in range(1, users_per_persona + 1):
            # Give each user a slightly different normal login window.
            login_start = max(
                0,
                base_login_start + random.choice([-1, 0, 0, 0, 1]),
            )

            login_end = min(
                23,
                base_login_end + random.choice([-1, 0, 0, 0, 1]),
            )

            device_ids = create_device_ids(
                prefix=prefix,
                user_number=user_number,
                count=template["devices_per_user"],
            )

            # Slightly personalise the normal download behaviour.
            download_mean = max(
                1,
                round(
                    template["download_mean_mb"]
                    * random.uniform(0.85, 1.15),
                    2,
                ),
            )

            download_std = max(
                1,
                round(
                    template["download_std_mb"]
                    * random.uniform(0.85, 1.15),
                    2,
                ),
            )

            user = {
                "user_id": f"{prefix}-{user_number:03d}",
                "employee_name": fake.name(),
                "user_role": role,
                "department": template["department"],
                "normal_login_start": login_start,
                "normal_login_end": login_end,
                "approved_locations": "|".join(
                    template["locations"]
                ),
                "approved_resources": "|".join(
                    template["resources"]
                ),
                "approved_devices": "|".join(device_ids),
                "normal_download_mean_mb": download_mean,
                "normal_download_std_mb": download_std,
                "approved_maintenance_window": template[
                    "maintenance_window"
                ],
                "account_status": "active",
            }

            users.append(user)

    return pd.DataFrame(users)
    
    
def save_users(users_df: pd.DataFrame) -> Path:
    """
    Save the generated privileged-user profiles to data/users.csv.
    """

    output_path = DATA_DIR / "users.csv"
    users_df.to_csv(output_path, index=False)

    return output_path


def main() -> None:
    users_df = generate_users(users_per_persona=5)
    output_path = save_users(users_df)

    print("=" * 60)
    print("SentinelAI privileged-user profiles generated")
    print("=" * 60)
    print(f"Total users: {len(users_df)}")
    print(f"Total personas: {users_df['user_role'].nunique()}")
    print(f"Saved to: {output_path}")
    print()

    print("Users by persona:")
    print(users_df["user_role"].value_counts().to_string())
    print()

    print("Sample profiles:")
    print(
        users_df[
            [
                "user_id",
                "user_role",
                "normal_login_start",
                "normal_login_end",
                "approved_devices",
            ]
        ]
        .head(10)
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()