# SentinelAI Shared Technical Contract

## Team Roles

Person A: Data and Detection  
Person B: Dashboard, Response and Crypto

## User Personas

30 users across six privileged personas:

1. Database Administrator — 5 users
2. System Administrator — 5 users
3. Security Administrator — 5 users
4. Application Administrator — 5 users
5. External Vendor — 5 users
6. Privileged Auditor — 5 users

## Dataset Schema

Every event must contain:

- timestamp
- user_id
- user_role
- department
- action
- resource
- resource_sensitivity
- login_hour
- device_id
- ip_address
- location
- failed_attempts
- data_downloaded_mb
- privilege_change
- audit_log_disabled
- usual_device
- usual_resource
- approved_maintenance_window
- label

Boolean values must use True or False.

Labels:

- normal
- suspicious

## Rule Weights

- After-hours login: +15
- Unknown device: +20
- Unusual resource: +20
- Repeated failed attempts: +15
- Mass download: +25
- Privilege escalation: +30
- Audit logging disabled: +35
- Sensitive-data access: +20

Rule score is capped at 100.

## Fusion Formula

Final Score = 0.60 × Rule Score + 0.40 × ML Anomaly Score

Final score is capped at 100.

## Risk Tiers

- 0–29: Low
- 30–54: Medium
- 55–79: High
- 80–100: Critical

## Response Mapping

Low: Allow access and log activity.

Medium: Continue monitoring and notify the analyst.

High: Require step-up MFA and temporarily restrict sensitive actions.

Critical: Suspend the session, restrict privileged access and alert the SOC.

## Attack Scenarios

1. Compromised administrator
2. Data exfiltration
3. Privilege abuse
4. Evidence tampering

## Detection Function Contract

Person A provides:

`score_event(event)`

Required output:

```python
{
    "rule_score": 75,
    "ml_score": 88,
    "final_score": 80,
    "risk_tier": "High",
    "reasons": [
        "After-hours login",
        "Unknown device",
        "Unusual resource"
    ],
    "recommended_action": "Require step-up MFA and temporarily restrict sensitive actions."
}
```