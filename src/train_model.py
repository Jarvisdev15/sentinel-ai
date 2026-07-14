from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

try:
    from .preprocess import build_ml_features
except ImportError:
    from preprocess import build_ml_features


SEED = 42

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
MODELS_DIR = PROJECT_ROOT / "models"

LABELED_LOGS_PATH = DATA_DIR / "labeled_activity_logs.csv"
ML_SCORED_PATH = DATA_DIR / "ml_scored_activity_logs.csv"
MODEL_PATH = MODELS_DIR / "isolation_forest_bundle.pkl"

SCORE_TAIL_START = 0.75


def train_isolation_forest(
    normal_events_df: pd.DataFrame,
) -> dict[str, Any]:
    """
    Train Isolation Forest using only normal activity.

    This teaches the model what normal privileged-user
    behaviour looks like without using suspicious labels
    during model fitting.
    """

    normal_features = build_ml_features(
        normal_events_df
    )

    scaler = StandardScaler()

    scaled_normal_features = scaler.fit_transform(
        normal_features
    )

    model = IsolationForest(
        n_estimators=300,
        contamination=0.05,
        random_state=SEED,
        n_jobs=-1,
    )

    model.fit(scaled_normal_features)

    # score_samples returns smaller values for
    # more anomalous events. Negating it means
    # larger values represent greater anomaly strength.
    normal_strengths = -model.score_samples(
        scaled_normal_features
    )

    bundle = {
        "model": model,
        "scaler": scaler,
        "feature_columns": list(
            normal_features.columns
        ),
        "normal_strengths": np.sort(
            normal_strengths
        ),
        "score_tail_start": SCORE_TAIL_START,
    }

    return bundle


def strength_to_ml_score(
    anomaly_strengths: np.ndarray,
    normal_strengths: np.ndarray,
    tail_start: float = SCORE_TAIL_START,
) -> np.ndarray:
    """
    Convert anomaly strength into a 0-100 score.

    An event is compared against the distribution of
    normal training behaviour.

    The lowest 75% of normal-like behaviour scores 0.
    Events in the most unusual 25% rise toward 100.
    Events more unusual than all normal training data
    receive 100.
    """

    percentiles = np.searchsorted(
        normal_strengths,
        anomaly_strengths,
        side="right",
    ) / len(normal_strengths)

    scores = (
        (percentiles - tail_start)
        / (1.0 - tail_start)
        * 100.0
    )

    return np.clip(
        scores,
        0,
        100,
    )


def score_events_with_model(
    events_df: pd.DataFrame,
    bundle: dict[str, Any],
) -> pd.DataFrame:
    """
    Apply the trained Isolation Forest to activity events.
    """

    features_df = build_ml_features(events_df)

    expected_columns = bundle[
        "feature_columns"
    ]

    features_df = features_df[
        expected_columns
    ]

    scaled_features = bundle[
        "scaler"
    ].transform(
        features_df
    )

    model = bundle["model"]

    anomaly_strengths = -model.score_samples(
        scaled_features
    )

    ml_scores = strength_to_ml_score(
        anomaly_strengths=anomaly_strengths,
        normal_strengths=bundle[
            "normal_strengths"
        ],
        tail_start=bundle[
            "score_tail_start"
        ],
    )

    predictions = model.predict(
        scaled_features
    )

    scored_df = events_df.copy()

    scored_df["ml_anomaly_strength"] = (
        anomaly_strengths
    )

    scored_df["ml_score"] = np.round(
        ml_scores,
        2,
    )

    scored_df["ml_prediction"] = np.where(
        predictions == -1,
        "anomaly",
        "normal",
    )

    return scored_df


def main() -> None:
    if not LABELED_LOGS_PATH.exists():
        raise FileNotFoundError(
            "data/labeled_activity_logs.csv "
            "was not found."
        )

    events_df = pd.read_csv(
        LABELED_LOGS_PATH
    )

    normal_events_df = events_df[
        events_df["label"] == "normal"
    ].copy()

    if normal_events_df.empty:
        raise ValueError(
            "No normal events were available "
            "for model training."
        )

    bundle = train_isolation_forest(
        normal_events_df
    )

    MODELS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    joblib.dump(
        bundle,
        MODEL_PATH,
    )

    scored_df = score_events_with_model(
        events_df=events_df,
        bundle=bundle,
    )

    scored_df.to_csv(
        ML_SCORED_PATH,
        index=False,
    )

    print("=" * 60)
    print("SentinelAI Isolation Forest completed")
    print("=" * 60)

    print(
        f"Normal training events: "
        f"{len(normal_events_df)}"
    )

    print(
        f"Total events scored: "
        f"{len(scored_df)}"
    )

    print()

    print("Average ML score by label:")
    print(
        scored_df.groupby("label")[
            "ml_score"
        ]
        .mean()
        .round(2)
        .to_string()
    )

    print()

    print("ML score distribution by label:")
    print(
        scored_df.groupby("label")[
            "ml_score"
        ]
        .describe()
        .round(2)
        .to_string()
    )

    print()

    print("Model predictions:")
    print(
        pd.crosstab(
            scored_df["label"],
            scored_df["ml_prediction"],
        ).to_string()
    )

    print()

    suspicious_high_ml = (
        scored_df[
            scored_df["label"] == "suspicious"
        ]["ml_score"]
        >= 55
    ).sum()

    print(
        "Suspicious events with "
        f"ML score >= 55: "
        f"{suspicious_high_ml}"
    )

    print(f"Model saved to: {MODEL_PATH}")
    print(f"Scored data saved to: {ML_SCORED_PATH}")


if __name__ == "__main__":
    main()