from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

import joblib
import pandas as pd

try:
    from .response_engine import get_recommended_action
    from .risk_engine import fuse_scores, score_to_risk_tier
    from .rule_engine import calculate_rule_score
    from .train_model import (
        score_events_with_model,
        train_isolation_forest,
    )
except ImportError:
    from response_engine import get_recommended_action
    from risk_engine import fuse_scores, score_to_risk_tier
    from rule_engine import calculate_rule_score
    from train_model import (
        score_events_with_model,
        train_isolation_forest,
    )


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
MODELS_DIR = PROJECT_ROOT / "models"

USERS_PATH = DATA_DIR / "users.csv"

LABELED_LOGS_PATH = (
    DATA_DIR / "labeled_activity_logs.csv"
)

MODEL_PATH = (
    MODELS_DIR / "isolation_forest_bundle.pkl"
)


USER_LOOKUP: dict[str, dict[str, Any]] | None = None
MODEL_BUNDLE: dict[str, Any] | None = None


def load_user_lookup() -> dict[str, dict[str, Any]]:
    """
    Load privileged-user behavioural profiles.

    The lookup is cached after the first call.
    """

    global USER_LOOKUP

    if USER_LOOKUP is not None:
        return USER_LOOKUP

    if not USERS_PATH.exists():
        raise FileNotFoundError(
            "data/users.csv was not found."
        )

    users_df = pd.read_csv(USERS_PATH)

    USER_LOOKUP = users_df.set_index(
        "user_id"
    ).to_dict(
        orient="index"
    )

    return USER_LOOKUP


def load_model_bundle() -> dict[str, Any]:
    """
    Load the trained Isolation Forest model.

    If the model file is missing, rebuild it automatically
    from the normal labelled activity records.
    """

    global MODEL_BUNDLE

    if MODEL_BUNDLE is not None:
        return MODEL_BUNDLE

    if MODEL_PATH.exists():
        MODEL_BUNDLE = joblib.load(
            MODEL_PATH
        )

        return MODEL_BUNDLE

    if not LABELED_LOGS_PATH.exists():
        raise FileNotFoundError(
            "Neither the trained model nor "
            "data/labeled_activity_logs.csv was found."
        )

    events_df = pd.read_csv(
        LABELED_LOGS_PATH
    )

    normal_events_df = events_df[
        events_df["label"] == "normal"
    ].copy()

    if normal_events_df.empty:
        raise ValueError(
            "No normal events are available "
            "for automatic model training."
        )

    MODEL_BUNDLE = train_isolation_forest(
        normal_events_df
    )

    MODELS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    joblib.dump(
        MODEL_BUNDLE,
        MODEL_PATH,
    )

    return MODEL_BUNDLE


def validate_event(
    event: Mapping[str, Any],
) -> None:
    """
    Confirm that the event contains the fields required
    by the rule and ML detection systems.
    """

    required_fields = {
        "user_id",
        "login_hour",
        "device_id",
        "resource",
        "resource_sensitivity",
        "failed_attempts",
        "data_downloaded_mb",
        "privilege_change",
        "audit_log_disabled",
        "usual_device",
        "usual_resource",
        "approved_maintenance_window",
    }

    missing_fields = required_fields.difference(
        event.keys()
    )

    if missing_fields:
        raise ValueError(
            "Event is missing required fields: "
            f"{sorted(missing_fields)}"
        )


def score_event(
    event: Mapping[str, Any],
) -> dict[str, Any]:
    """
    Score one privileged-user activity event.

    This is the integration function used by the
    Streamlit dashboard and attack simulator.
    """

    validate_event(event)

    user_id = str(
        event["user_id"]
    ).strip()

    user_lookup = load_user_lookup()

    if user_id not in user_lookup:
        raise KeyError(
            f"No behavioural profile found for {user_id}"
        )

    user_profile = user_lookup[user_id]

    rule_result = calculate_rule_score(
        event=event,
        user_profile=user_profile,
    )

    event_df = pd.DataFrame(
        [dict(event)]
    )

    model_bundle = load_model_bundle()

    ml_result_df = score_events_with_model(
        events_df=event_df,
        bundle=model_bundle,
    )

    ml_score = float(
        ml_result_df.iloc[0]["ml_score"]
    )

    rule_score = float(
        rule_result["rule_score"]
    )

    final_score = fuse_scores(
        rule_score=rule_score,
        ml_score=ml_score,
    )

    risk_tier = score_to_risk_tier(
        final_score
    )

    reasons = list(
        rule_result["reasons"]
    )

    if ml_score >= 55:
        reasons.append(
            "Behavioural ML detected a strong anomaly "
            f"with score {ml_score:.2f}/100"
        )

    elif ml_score >= 30:
        reasons.append(
            "Behavioural ML detected a moderate anomaly "
            f"with score {ml_score:.2f}/100"
        )

    return {
        "rule_score": round(
            rule_score,
            2,
        ),
        "ml_score": round(
            ml_score,
            2,
        ),
        "final_score": final_score,
        "risk_tier": risk_tier,
        "reasons": reasons,
        "recommended_action": (
            get_recommended_action(
                risk_tier
            )
        ),
    }


def main() -> None:
    """
    Test the reusable function using one normal event
    and one suspicious bulk-export event.
    """

    if not LABELED_LOGS_PATH.exists():
        raise FileNotFoundError(
            "data/labeled_activity_logs.csv "
            "was not found."
        )

    events_df = pd.read_csv(
        LABELED_LOGS_PATH
    )

    normal_event = events_df[
        events_df["label"] == "normal"
    ].iloc[0].to_dict()

    suspicious_event = events_df[
        events_df["action"]
        == "bulk_customer_data_export"
    ].iloc[0].to_dict()

    print("=" * 60)
    print("Normal event test")
    print("=" * 60)

    print(
        json.dumps(
            score_event(normal_event),
            indent=2,
        )
    )

    print()

    print("=" * 60)
    print("Suspicious event test")
    print("=" * 60)

    print(
        json.dumps(
            score_event(suspicious_event),
            indent=2,
        )
    )


if __name__ == "__main__":
    main()