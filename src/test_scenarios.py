from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

try:
    from .scoring_service import score_event
except ImportError:
    from scoring_service import score_event


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"

LABELED_LOGS_PATH = DATA_DIR / "labeled_activity_logs.csv"
TEST_RESULTS_PATH = DATA_DIR / "scenario_test_results.csv"


ATTACK_SCENARIOS = {
    "Compromised Administrator": "suspicious_remote_login",
    "Data Exfiltration": "bulk_customer_data_export",
    "Privilege Abuse": "privilege_escalation_attempt",
    "Evidence Tampering": "disable_audit_logging",
}


def test_event(
    scenario_name: str,
    event: dict[str, Any],
    expected_tiers: set[str],
) -> dict[str, Any]:
    """
    Score one event and check whether its risk tier is expected.
    """

    result = score_event(event)

    passed = result["risk_tier"] in expected_tiers

    return {
        "scenario": scenario_name,
        "user_id": event["user_id"],
        "action": event["action"],
        "rule_score": result["rule_score"],
        "ml_score": result["ml_score"],
        "final_score": result["final_score"],
        "risk_tier": result["risk_tier"],
        "recommended_action": result[
            "recommended_action"
        ],
        "reasons": json.dumps(result["reasons"]),
        "test_status": "PASS" if passed else "FAIL",
    }


def main() -> None:
    if not LABELED_LOGS_PATH.exists():
        raise FileNotFoundError(
            "data/labeled_activity_logs.csv was not found."
        )

    events_df = pd.read_csv(LABELED_LOGS_PATH)

    test_results: list[dict[str, Any]] = []

    # Test one normal activity record.
    normal_event = (
        events_df[
            events_df["label"] == "normal"
        ]
        .iloc[0]
        .to_dict()
    )

    test_results.append(
        test_event(
            scenario_name="Normal User Activity",
            event=normal_event,
            expected_tiers={"Low", "Medium"},
        )
    )

    # Test all four attack scenarios.
    for scenario_name, action in ATTACK_SCENARIOS.items():
        matching_events = events_df[
            events_df["action"] == action
        ]

        if matching_events.empty:
            raise ValueError(
                f"No event found for scenario: {scenario_name}"
            )

        event = matching_events.iloc[0].to_dict()

        test_results.append(
            test_event(
                scenario_name=scenario_name,
                event=event,
                expected_tiers={"High", "Critical"},
            )
        )

    results_df = pd.DataFrame(test_results)

    results_df.to_csv(
        TEST_RESULTS_PATH,
        index=False,
    )

    print("=" * 75)
    print("SentinelAI end-to-end scenario tests")
    print("=" * 75)

    print(
        results_df[
            [
                "scenario",
                "rule_score",
                "ml_score",
                "final_score",
                "risk_tier",
                "test_status",
            ]
        ].to_string(index=False)
    )

    print()

    passed_tests = (
        results_df["test_status"] == "PASS"
    ).sum()

    print(
        f"Tests passed: {passed_tests}/{len(results_df)}"
    )

    print(f"Saved to: {TEST_RESULTS_PATH}")

    if passed_tests != len(results_df):
        raise RuntimeError(
            "One or more scenario tests failed."
        )


if __name__ == "__main__":
    main()