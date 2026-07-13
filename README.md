# SentinelAI

## Explainable Insider Threat Detection for Privileged Banking Accounts

SentinelAI is a banking cybersecurity prototype created for the FinSpark Hackathon 2026.

It detects suspicious behaviour performed through privileged employee, administrator, vendor, or compromised internal accounts.

Unlike traditional access control, SentinelAI does not only ask:

> Is this user authorised?

It also asks:

> Is this authorised user behaving normally?

---

## Problem Statement

Privileged banking users can access sensitive systems such as:

- Core banking databases
- KYC databases
- Customer records
- Identity and access-management systems
- Audit-log repositories
- Payment and banking applications

A malicious insider or compromised account may have valid credentials and permissions, allowing suspicious activity to bypass ordinary authentication checks.

SentinelAI detects behaviour such as:

- After-hours login
- Unknown device usage
- Access to unusual resources
- Repeated failed attempts
- Abnormally large data downloads
- Privilege escalation
- Audit-log disabling
- Sensitive-data access

---

## Solution Overview

SentinelAI combines:

1. Explainable rule-based detection
2. Isolation Forest behavioural anomaly detection
3. Hybrid risk-score fusion
4. Risk-tier classification
5. Recommended security responses

The complete flow is:

```text
Privileged-user activity logs
        ↓
Behavioural baseline comparison
        ↓
Rule-based risk detection
        +
Isolation Forest anomaly detection
        ↓
60/40 score fusion
        ↓
Low / Medium / High / Critical
        ↓
Recommended security response
```

---

## Key Features

- Persona-based synthetic banking dataset
- Thirty privileged-user profiles
- Six banking personas
- Individual login, device, resource and download baselines
- Eight explainable security rules
- Isolation Forest anomaly detection
- Risk score from 0 to 100
- Four risk tiers
- Recommended response mapping
- Reusable `score_event(event)` integration function
- Four injected insider-threat scenarios
- End-to-end automated scenario testing

---

## Banking Personas

The prototype contains thirty users across six privileged roles:

| Persona | Users |
|---|---:|
| Database Administrator | 5 |
| System Administrator | 5 |
| Security Administrator | 5 |
| Application Administrator | 5 |
| External Vendor | 5 |
| Privileged Auditor | 5 |

Every user has an individual behavioural baseline containing:

- Normal login hours
- Approved devices
- Approved locations
- Approved resources
- Typical download volume
- Approved maintenance window

---

## Dataset

The generated dataset contains:

| Category | Count |
|---|---:|
| Normal events | 600 |
| Suspicious events | 60 |
| Total labelled events | 660 |
| Missing values | 0 |

The suspicious records are divided across four attack scenarios:

| Scenario | Events |
|---|---:|
| Compromised administrator | 15 |
| Data exfiltration | 15 |
| Privilege abuse | 15 |
| Evidence tampering | 15 |

---

## Detection Rules

| Rule | Weight |
|---|---:|
| After-hours login | +15 |
| Unknown device | +20 |
| Unusual resource | +20 |
| Repeated failed attempts | +15 |
| Mass download | +25 |
| Privilege escalation | +30 |
| Audit logging disabled | +35 |
| Sensitive-resource access | +20 |

The rule score is capped at 100.

---

## Behavioural Machine Learning

SentinelAI uses an Isolation Forest trained only on normal activity.

The model analyses numerical behavioural features including:

- Login time
- Resource sensitivity
- Failed attempts
- Download volume
- Privilege changes
- Audit-log status
- Unknown-device usage
- Unusual-resource access
- Maintenance-window violations

The model converts behavioural anomaly strength into an ML score between 0 and 100.

---

## Hybrid Risk Score

```text
Final Score = 60% Rule Score + 40% ML Score
```

This hybrid method combines:

- Explainability from fixed security rules
- Behavioural intelligence from machine learning

An activity can therefore be detected even when it triggers only a small number of fixed rules but is extremely abnormal for that user.

---

## Risk Tiers

| Final score | Tier | Response |
|---:|---|---|
| Below 30 | Low | Allow access and log activity |
| 30 to below 55 | Medium | Continue monitoring and notify analyst |
| 55 to below 80 | High | Require step-up MFA and restrict sensitive actions |
| 80 and above | Critical | Suspend session and immediately alert the SOC |

---

## Results

| Metric | Result |
|---|---:|
| Suspicious events classified High/Critical | 60/60 |
| Normal events classified High/Critical | 0/600 |
| Average suspicious final score | 90.98 |
| Average normal final score | 13.99 |
| End-to-end scenario tests passed | 5/5 |

### Scenario Test Results

| Scenario | Final score | Risk tier | Result |
|---|---:|---|---|
| Normal User Activity | 28.80 | Low | PASS |
| Compromised Administrator | 94.00 | Critical | PASS |
| Data Exfiltration | 75.47 | High | PASS |
| Privilege Abuse | 88.00 | Critical | PASS |
| Evidence Tampering | 100.00 | Critical | PASS |

---

## Technology Stack

- Python 3.12
- Pandas
- NumPy
- Scikit-learn
- Isolation Forest
- Faker
- Joblib
- Streamlit
- Plotly
- GitHub

---

## Repository Structure

```text
sentinel-ai/
│
├── data/
│   ├── users.csv
│   ├── activity_logs.csv
│   ├── labeled_activity_logs.csv
│   ├── final_scored_activity_logs.csv
│   ├── response_scored_activity_logs.csv
│   └── scenario_test_results.csv
│
├── models/
│   └── isolation_forest_bundle.pkl
│
├── src/
│   ├── generate_data.py
│   ├── generate_activity.py
│   ├── inject_anomalies.py
│   ├── preprocess.py
│   ├── rule_engine.py
│   ├── train_model.py
│   ├── risk_engine.py
│   ├── response_engine.py
│   ├── scoring_service.py
│   └── test_scenarios.py
│
├── docs/
│   ├── shared_contract.md
│   └── person_a_handoff.md
│
├── pages/
├── diagrams/
├── screenshots/
├── app.py
├── requirements.txt
└── README.md
```

---

## Installation

Clone the repository:

```bash
git clone https://github.com/Jarvisdev15/sentinel-ai.git
cd sentinel-ai
```

Create a virtual environment:

```bash
py -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

---

## Run the Detection Pipeline

Generate privileged-user profiles:

```bash
python src/generate_data.py
```

Generate normal user activity:

```bash
python src/generate_activity.py
```

Inject suspicious scenarios:

```bash
python src/inject_anomalies.py
```

Run the explainable rule engine:

```bash
python src/rule_engine.py
```

Train the Isolation Forest model:

```bash
python src/train_model.py
```

Fuse rule and ML scores:

```bash
python src/risk_engine.py
```

Map recommended responses:

```bash
python src/response_engine.py
```

Run all end-to-end scenario tests:

```bash
python src/test_scenarios.py
```

---

## Dashboard Integration

Person B’s Streamlit dashboard can use:

```python
from src.scoring_service import score_event

result = score_event(event)
```

The function returns:

```python
{
    "rule_score": 90.0,
    "ml_score": 100.0,
    "final_score": 94.0,
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

Full integration instructions are available in:

```text
docs/person_a_handoff.md
```

---

## Security and Limitations

- The prototype uses synthetic data and no real customer information.
- Isolation Forest results depend on the quality of the behavioural baseline.
- A production system would require human review before severe account action.
- The prototype does not claim deployment inside Bank of Maharashtra.
- The post-quantum cryptography demonstration is handled separately by the dashboard/security component.
- Real deployment would integrate with IAM, SIEM, database and authentication logs.

---

## Future Scope

- Real-time event streaming
- Analyst investigation timeline
- User behaviour profile page
- Analyst feedback and model retraining
- Exportable incident reports
- SIEM and SOC integration
- Branch-level deployment
- Standardised post-quantum incident signing

---

## FinSpark Hackathon 2026

SentinelAI demonstrates how explainable behavioural analytics can help banks detect threats hidden behind legitimate privileged access.