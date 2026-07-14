# SentinelAI - Person A Integration Handoff

## 1. Main dashboard integration function

Person B should import the reusable scoring function using:

```python
from src.scoring_service import score_event
```

Call it using:

```python
result = score_event(event)
```

The function runs the complete hybrid detection pipeline:

1. Eight explainable security rules
2. Isolation Forest behavioural anomaly scoring
3. 60/40 score fusion
4. Risk-tier assignment
5. Recommended response mapping

## 2. Required event fields

```python
event = {
    "user_id": "DBA-001",
    "login_hour": 2,
    "device_id": "UNKNOWN-DEVICE-001",
    "resource": "Core Banking Database",
    "resource_sensitivity": 5,
    "failed_attempts": 4,
    "data_downloaded_mb": 2500,
    "privilege_change": False,
    "audit_log_disabled": False,
    "usual_device": False,
    "usual_resource": False,
    "approved_maintenance_window": False,
}
```

The `user_id` must exist in:

```text
data/users.csv
```

## 3. Returned result

```python
{
    "rule_score": 75.0,
    "ml_score": 100.0,
    "final_score": 85.0,
    "risk_tier": "Critical",
    "reasons": [
        "After-hours login",
        "Unknown or unapproved device",
        "Unusual resource access",
        "Behavioural ML detected a strong anomaly"
    ],
    "recommended_action": (
        "Suspend the session, restrict privileged access "
        "and immediately alert the SOC."
    ),
}
```

## 4. Score fusion

```text
Final Score = 0.60 x Rule Score + 0.40 x ML Score
```

The final score is capped between 0 and 100.

## 5. Risk tiers

| Final score | Risk tier |
|---:|---|
| Below 30 | Low |
| 30 to below 55 | Medium |
| 55 to below 80 | High |
| 80 and above | Critical |

## 6. Response mapping

| Risk tier | Recommended action |
|---|---|
| Low | Allow access and log activity |
| Medium | Continue monitoring and notify the security analyst |
| High | Require step-up MFA and temporarily restrict sensitive actions |
| Critical | Suspend the session, restrict privileged access and immediately alert the SOC |

## 7. Eight rule-based indicators

1. After-hours login
2. Unknown device
3. Unusual resource
4. Repeated failed attempts
5. Mass download
6. Privilege escalation
7. Audit logging disabled
8. Sensitive-resource access

## 8. Tested attack scenarios

| Scenario | Rule score | ML score | Final score | Tier | Result |
|---|---:|---:|---:|---|---|
| Normal User Activity | 20.0 | 42.0 | 28.8 | Low | PASS |
| Compromised Administrator | 90.0 | 100.0 | 94.0 | Critical | PASS |
| Data Exfiltration | 60.0 | 98.67 | 75.47 | High | PASS |
| Privilege Abuse | 80.0 | 100.0 | 88.0 | Critical | PASS |
| Evidence Tampering | 100.0 | 100.0 | 100.0 | Critical | PASS |

All five end-to-end scenario tests passed.

## 9. Model and dataset results

- Privileged users: 30
- User personas: 6
- Normal events: 600
- Suspicious events: 60
- Total labelled events: 660
- Missing values: 0
- Suspicious events classified High/Critical: 60/60
- Normal events classified High/Critical: 0/600
- Average normal final score: 13.99
- Average suspicious final score: 90.98

## 10. Important files

### Integration

```text
src/scoring_service.py
```

### Detection pipeline

```text
src/rule_engine.py
src/preprocess.py
src/train_model.py
src/risk_engine.py
src/response_engine.py
```

### Data generation and testing

```text
src/generate_data.py
src/generate_activity.py
src/inject_anomalies.py
src/test_scenarios.py
```

### Data files

```text
data/users.csv
data/activity_logs.csv
data/labeled_activity_logs.csv
data/final_scored_activity_logs.csv
data/response_scored_activity_logs.csv
data/scenario_test_results.csv
```

## 11. Isolation Forest model

The trained model is expected at:

```text
models/isolation_forest_bundle.pkl
```

If this file is unavailable, `scoring_service.py` automatically retrains the model using the normal records in:

```text
data/labeled_activity_logs.csv
```

## 12. Dashboard usage example

```python
from src.scoring_service import score_event

result = score_event(event)

final_score = result["final_score"]
risk_tier = result["risk_tier"]
reasons = result["reasons"]
recommended_action = result["recommended_action"]
```

Person B can display these values directly on the Live Alerts and Attack Simulation pages.