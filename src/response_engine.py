from __future__ import annotations

from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"

FINAL_SCORED_PATH = (
    DATA_DIR / "final_scored_activity_logs.csv"
)

RESPONSE_SCORED_PATH = (
    DATA_DIR / "response_scored_activity_logs.csv"
)


RESPONSE_MAPPING: dict[str, str] = {
    "Low": (
        "Allow access and log activity."
    ),
    "Medium": (
        "Continue monitoring and notify the security analyst."
    ),
    "High": (
        "Require step-up MFA and temporarily restrict "
        "sensitive actions."
    ),
    "Critical": (
        "Suspend the session, restrict privileged access "
        "and immediately alert the SOC."
    ),
}


def get_recommended_action(
    risk_tier: str,
) -> str:
    """
    Return the response mapped to a risk tier.
    """

    normalized_tier = str(risk_tier).strip().title()

    if normalized_tier not in RESPONSE_MAPPING:
        raise ValueError(
            f"Unknown risk tier: {risk_tier}"
        )

    return RESPONSE_MAPPING[normalized_tier]


def add_recommended_actions(
    scored_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Add the risk-based response to every scored event.
    """

    if "risk_tier" not in scored_df.columns:
        raise ValueError(
            "The dataset does not contain risk_tier."
        )

    result_df = scored_df.copy()

    result_df["recommended_action"] = (
        result_df["risk_tier"].map(
            get_recommended_action
        )
    )

    return result_df


def main() -> None:
    if not FINAL_SCORED_PATH.exists():
        raise FileNotFoundError(
            "data/final_scored_activity_logs.csv "
            "was not found."
        )

    scored_df = pd.read_csv(
        FINAL_SCORED_PATH
    )

    response_df = add_recommended_actions(
        scored_df
    )

    response_df.to_csv(
        RESPONSE_SCORED_PATH,
        index=False,
    )

    print("=" * 60)
    print("SentinelAI response mapping completed")
    print("=" * 60)
    print(f"Events processed: {len(response_df)}")
    print()

    print("Actions by risk tier:")
    print(
        response_df.groupby("risk_tier")[
            "recommended_action"
        ]
        .first()
        .to_string()
    )
    print()

    print(
        f"Saved to: {RESPONSE_SCORED_PATH}"
    )


if __name__ == "__main__":
    main()