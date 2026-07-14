from __future__ import annotations

from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"

RULE_SCORED_PATH = (
    DATA_DIR / "rule_scored_activity_logs.csv"
)

ML_SCORED_PATH = (
    DATA_DIR / "ml_scored_activity_logs.csv"
)

FINAL_SCORED_PATH = (
    DATA_DIR / "final_scored_activity_logs.csv"
)


RULE_WEIGHT = 0.60
ML_WEIGHT = 0.40


IDENTITY_COLUMNS = [
    "timestamp",
    "user_id",
    "action",
    "resource",
    "label",
]


def fuse_scores(
    rule_score: float,
    ml_score: float,
) -> float:
    """
    Combine explainable rules and behavioural ML.

    Final score:
    60% rule score + 40% ML anomaly score.
    """

    final_score = (
        RULE_WEIGHT * float(rule_score)
        + ML_WEIGHT * float(ml_score)
    )

    return round(
        min(max(final_score, 0.0), 100.0),
        2,
    )


def score_to_risk_tier(
    final_score: float,
) -> str:
    """
    Convert the final numerical score into a risk tier.
    """

    if final_score < 30:
        return "Low"

    if final_score < 55:
        return "Medium"

    if final_score < 80:
        return "High"

    return "Critical"


def combine_rule_and_ml_scores(
    rule_df: pd.DataFrame,
    ml_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Combine rule-engine and ML outputs.

    Both files originate from the same labelled dataset,
    so the event order and identity fields must match.
    """

    if len(rule_df) != len(ml_df):
        raise ValueError(
            "Rule and ML datasets have different "
            "numbers of events."
        )

    missing_rule_columns = set(
        IDENTITY_COLUMNS
        + [
            "rule_score",
            "rule_reasons",
            "triggered_rules",
        ]
    ).difference(rule_df.columns)

    if missing_rule_columns:
        raise ValueError(
            "Missing rule columns: "
            f"{sorted(missing_rule_columns)}"
        )

    missing_ml_columns = set(
        IDENTITY_COLUMNS
        + [
            "ml_score",
            "ml_prediction",
            "ml_anomaly_strength",
        ]
    ).difference(ml_df.columns)

    if missing_ml_columns:
        raise ValueError(
            "Missing ML columns: "
            f"{sorted(missing_ml_columns)}"
        )

    rule_identity = rule_df[
        IDENTITY_COLUMNS
    ].astype(str)

    ml_identity = ml_df[
        IDENTITY_COLUMNS
    ].astype(str)

    if not rule_identity.equals(ml_identity):
        raise ValueError(
            "Rule and ML datasets do not contain "
            "the same events in the same order."
        )

    final_df = rule_df.copy()

    final_df["ml_anomaly_strength"] = ml_df[
        "ml_anomaly_strength"
    ]

    final_df["ml_score"] = ml_df[
        "ml_score"
    ]

    final_df["ml_prediction"] = ml_df[
        "ml_prediction"
    ]

    final_df["final_score"] = [
        fuse_scores(
            rule_score=rule_score,
            ml_score=ml_score,
        )
        for rule_score, ml_score in zip(
            final_df["rule_score"],
            final_df["ml_score"],
        )
    ]

    final_df["risk_tier"] = final_df[
        "final_score"
    ].map(score_to_risk_tier)

    return final_df


def main() -> None:
    if not RULE_SCORED_PATH.exists():
        raise FileNotFoundError(
            "data/rule_scored_activity_logs.csv "
            "was not found."
        )

    if not ML_SCORED_PATH.exists():
        raise FileNotFoundError(
            "data/ml_scored_activity_logs.csv "
            "was not found."
        )

    rule_df = pd.read_csv(
        RULE_SCORED_PATH
    )

    ml_df = pd.read_csv(
        ML_SCORED_PATH
    )

    final_df = combine_rule_and_ml_scores(
        rule_df=rule_df,
        ml_df=ml_df,
    )

    final_df.to_csv(
        FINAL_SCORED_PATH,
        index=False,
    )

    print("=" * 60)
    print("SentinelAI score fusion completed")
    print("=" * 60)
    print(f"Events fused: {len(final_df)}")
    print(
        f"Formula: {RULE_WEIGHT:.0%} rules + "
        f"{ML_WEIGHT:.0%} ML"
    )
    print()

    print("Average final score by label:")
    print(
        final_df.groupby("label")[
            "final_score"
        ]
        .mean()
        .round(2)
        .to_string()
    )
    print()

    print("Risk-tier distribution:")
    print(
        pd.crosstab(
            final_df["label"],
            final_df["risk_tier"],
        ).to_string()
    )
    print()

    suspicious_df = final_df[
        final_df["label"] == "suspicious"
    ]

    normal_df = final_df[
        final_df["label"] == "normal"
    ]

    suspicious_high_or_critical = (
        suspicious_df["risk_tier"].isin(
            ["High", "Critical"]
        )
    ).sum()

    normal_high_or_critical = (
        normal_df["risk_tier"].isin(
            ["High", "Critical"]
        )
    ).sum()

    print(
        "Suspicious events classified "
        "High/Critical: "
        f"{suspicious_high_or_critical}/"
        f"{len(suspicious_df)}"
    )

    print(
        "Normal events classified "
        "High/Critical: "
        f"{normal_high_or_critical}/"
        f"{len(normal_df)}"
    )
    print()

    print("Suspicious events by scenario:")
    print(
        suspicious_df.groupby("action")[
            "final_score"
        ]
        .agg(
            [
                "count",
                "min",
                "mean",
                "max",
            ]
        )
        .round(2)
        .to_string()
    )
    print()

    print(
        f"Saved to: {FINAL_SCORED_PATH}"
    )


if __name__ == "__main__":
    main()