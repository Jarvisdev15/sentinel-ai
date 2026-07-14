# SentinelAI — Technical Results for Presentation

## 1. Problem

Privileged users such as database administrators, system administrators, security administrators, auditors and external vendors already possess legitimate access.

Because of this, traditional authentication alone may not detect:

- Compromised administrator accounts
- Insider data theft
- Unauthorised privilege escalation
- Audit-log tampering
- Suspicious access from unknown devices

SentinelAI detects whether an authorised user is behaving abnormally.

---

## 2. Solution

SentinelAI uses a hybrid detection system containing:

1. Eight explainable security rules
2. Isolation Forest behavioural anomaly detection
3. Rule and ML score fusion
4. Four risk tiers
5. Automated security-response recommendations

```text
User activity
      ↓
Rule-based detection
      +
Isolation Forest
      ↓
60% Rule Score + 40% ML Score
      ↓
Low / Medium / High / Critical
      ↓
Recommended response
```

---

## 3. Synthetic Banking Dataset

| Dataset component | Count |
|---|---:|
| Privileged users | 30 |
| Banking personas | 6 |
| Normal activity events | 600 |
| Suspicious events | 60 |
| Total labelled events | 660 |
| Missing values | 0 |

### User personas

- Database Administrator
- System Administrator
- Security Administrator
- Application Administrator
- External Vendor
- Privileged Auditor

Each user has an individual baseline for:

- Normal login hours
- Approved devices
- Approved resources
- Typical download volume
- Resource sensitivity
- Maintenance windows

---

## 4. Simulated Attack Scenarios

| Attack scenario | Events | Description |
|---|---:|---|
| Compromised Administrator | 15 | After-hours access through an unknown device |
| Data Exfiltration | 15 | Abnormally large customer-data downloads |
| Privilege Abuse | 15 | Unauthorised privilege-escalation attempts |
| Evidence Tampering | 15 | Attempts to disable audit logging |

---

## 5. Explainable Rule Engine

| Indicator | Weight |
|---|---:|
| After-hours login | 15 |
| Unknown device | 20 |
| Unusual resource | 20 |
| Repeated failed attempts | 15 |
| Mass download | 25 |
| Privilege escalation | 30 |
| Audit logging disabled | 35 |
| Sensitive-data access | 20 |

The rule score is capped at 100.

### Rule-engine results

| Event category | Average rule score | Maximum |
|---|---:|---:|
| Normal | 14.93 | 20 |
| Suspicious | 85.17 | 100 |

The rule engine assigned a score of at least 55 to 59 of the 60 suspicious events.

One data-exfiltration event received a lower rule score because it triggered fewer fixed rules. The behavioural ML model detected this event as highly anomalous.

---

## 6. Behavioural Machine Learning

The Isolation Forest model was trained only on the 600 normal activity records.

### Features analysed

- Cyclic login time
- Resource sensitivity
- Failed login attempts
- Download volume
- Privilege-change activity
- Audit-log status
- Unknown-device activity
- Unusual-resource access
- Maintenance-window violations

### Isolation Forest results

| Event category | Average ML score | Minimum suspicious score |
|---|---:|---:|
| Normal | 12.59 | — |
| Suspicious | 99.69 | 90.67 |

All 60 suspicious events received an ML score of at least 55.

The model marked:

- 60 of 60 suspicious events as anomalous
- 30 of 600 normal events as behavioural anomalies

The final hybrid score reduced unnecessary escalation by combining ML results with explainable rules.

---

## 7. Hybrid Risk Fusion

```text
Final Risk Score = 0.60 × Rule Score + 0.40 × ML Score
```

### Reason for the weighting

The rule engine receives a larger weight because:

- It gives analysts clear reasons
- It supports security-policy enforcement
- It makes the system easier to audit

The ML model receives a 40% weight because:

- It catches behaviour not covered by fixed rules
- It detects user-specific deviations
- It strengthens zero-day and unknown-pattern detection

---

## 8. Risk Tiers

| Final score | Risk tier |
|---:|---|
| Below 30 | Low |
| 30 to below 55 | Medium |
| 55 to below 80 | High |
| 80 and above | Critical |

---

## 9. Recommended Responses

| Risk tier | Recommended action |
|---|---|
| Low | Allow access and log the activity |
| Medium | Continue monitoring and notify the security analyst |
| High | Require step-up MFA and temporarily restrict sensitive actions |
| Critical | Suspend the session, restrict privileged access and alert the SOC |

---

## 10. Final Detection Results

| Event category | Average final score |
|---|---:|
| Normal | 13.99 |
| Suspicious | 90.98 |

### Final risk distribution

| Category | Low | Medium | High | Critical |
|---|---:|---:|---:|---:|
| Normal events | 539 | 61 | 0 | 0 |
| Suspicious events | 0 | 0 | 7 | 53 |

### Main result

- 60 of 60 injected suspicious events reached High or Critical risk
- 0 of 600 normal events reached High or Critical risk

This result applies only to the current synthetic prototype dataset.

---

## 11. End-to-End Scenario Testing

| Scenario | Rule score | ML score | Final score | Risk tier | Result |
|---|---:|---:|---:|---|---|
| Normal User Activity | 20.00 | 42.00 | 28.80 | Low | PASS |
| Compromised Administrator | 90.00 | 100.00 | 94.00 | Critical | PASS |
| Data Exfiltration | 60.00 | 98.67 | 75.47 | High | PASS |
| Privilege Abuse | 80.00 | 100.00 | 88.00 | Critical | PASS |
| Evidence Tampering | 100.00 | 100.00 | 100.00 | Critical | PASS |

All five end-to-end scenario tests passed.

---

## 12. Key Demonstration Points

During the presentation, demonstrate:

1. A normal event receiving Low risk
2. A compromised administrator receiving Critical risk
3. Data exfiltration receiving High risk
4. Privilege abuse receiving Critical risk
5. Audit-log disabling receiving Critical risk
6. Explainable reasons generated for every alert
7. Automated response recommendation
8. Dashboard scoring through `score_event(event)`

---

## 13. Technical Contribution of Person A

Person A implemented:

- User-persona generation
- Normal activity generation
- Suspicious-event injection
- Eight-rule detection engine
- Feature preprocessing
- Isolation Forest training
- ML anomaly scoring
- Hybrid risk fusion
- Risk-tier assignment
- Response mapping
- Reusable scoring service
- End-to-end scenario tests
- Dashboard integration documentation

---

## 14. Limitations

- The dataset is synthetic
- The prototype has not been validated using real banking logs
- The results should not be presented as production accuracy
- Isolation Forest performance depends on baseline quality
- Severe automated responses should require human review
- Real deployment would need IAM, SIEM and authentication-log integration

---

## 15. Future Scope

- Real-time event streaming
- Continuous behavioural-baseline updates
- Analyst feedback and retraining
- Incident timeline generation
- SIEM integration
- User-risk history
- Branch and department-level analytics
- Post-quantum signing of incident reports