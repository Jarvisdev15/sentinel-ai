from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

import streamlit as st

from app import load_css
from src.crypto_demo import (
    create_keypair,
    public_key_fingerprint,
    sign_incident,
    signature_to_text,
    tamper_incident,
    verify_incident,
)

try:
    from src.scoring_service import load_user_lookup
    from src.scoring_service import score_event
except Exception as import_error:
    st.error(
        "SentinelAI could not load the live scoring service. "
        f"{type(import_error).__name__}: {import_error}"
    )
    st.stop()


st.set_page_config(
    page_title="Attack Simulation - SentinelAI",
    layout="wide",
)

load_css()


SCENARIOS: dict[str, dict[str, Any]] = {
    "Compromised DBA": {
        "user_id": "DBA-001",
        "action": "suspicious_remote_login",
        "resource": "Identity Server",
        "resource_sensitivity": 5,
        "login_hour": 2,
        "device_id": "UNKNOWN-DEVICE-001",
        "failed_attempts": 3,
        "data_downloaded_mb": 12,
        "privilege_change": False,
        "audit_log_disabled": False,
        "usual_device": False,
        "usual_resource": False,
        "approved_maintenance_window": False,
    },
    "Data Exfiltration": {
        "user_id": "DBA-002",
        "action": "bulk_customer_data_export",
        "resource": "KYC Database",
        "resource_sensitivity": 5,
        "login_hour": 3,
        "device_id": "UNKNOWN-DEVICE-EXFIL",
        "failed_attempts": 0,
        "data_downloaded_mb": 6500,
        "privilege_change": False,
        "audit_log_disabled": False,
        "usual_device": False,
        "usual_resource": True,
        "approved_maintenance_window": False,
    },
    "Privilege Abuse": {
        "user_id": "SYS-001",
        "action": "privilege_escalation_attempt",
        "resource": "Identity and Access Management",
        "resource_sensitivity": 5,
        "login_hour": 11,
        "device_id": "SYS-001-DEV-01",
        "failed_attempts": 5,
        "data_downloaded_mb": 4,
        "privilege_change": True,
        "audit_log_disabled": False,
        "usual_device": True,
        "usual_resource": False,
        "approved_maintenance_window": False,
    },
    "Evidence Tampering": {
        "user_id": "SEC-001",
        "action": "disable_audit_logging",
        "resource": "Security Incident Repository",
        "resource_sensitivity": 4,
        "login_hour": 23,
        "device_id": "SEC-001-DEV-01",
        "failed_attempts": 1,
        "data_downloaded_mb": 30,
        "privilege_change": False,
        "audit_log_disabled": True,
        "usual_device": True,
        "usual_resource": True,
        "approved_maintenance_window": False,
    },
}

TIER_BADGES = {
    "Low": "badge-low",
    "Medium": "badge-medium",
    "High": "badge-high",
    "Critical": "badge-critical",
}


def create_simulated_alert(
    scenario_name: str,
    event: dict[str, Any],
    result: dict[str, Any],
) -> dict[str, Any]:
    """Create the alert record consumed by the Live Alerts page."""

    user_id = str(event["user_id"])
    user_profile = load_user_lookup().get(user_id, {})
    reasons = list(result.get("reasons") or [])

    return {
        **event,
        **result,
        "timestamp": datetime.now().astimezone().isoformat(),
        "scenario": scenario_name,
        "source": "Simulated",
        "is_simulated": True,
        "employee_name": user_profile.get(
            "employee_name",
            user_id,
        ),
        "user_role": user_profile.get(
            "user_role",
            "Unknown",
        ),
        "reasons": reasons,
        "reasons_text": ", ".join(reasons) if reasons else "None",
    }


def create_evidence_record(
    scenario_name: str,
    event: dict[str, Any],
    result: dict[str, Any],
    created_at: str,
) -> dict[str, Any]:
    """Sign an incident and verify its original contents."""

    incident = {
        "incident_id": f"SIM-{uuid4().hex[:12].upper()}",
        "created_at": created_at,
        "scenario": scenario_name,
        "event": dict(event),
        "result": dict(result),
    }

    private_key, public_key = create_keypair()
    signature = sign_incident(incident, private_key)

    return {
        "incident": incident,
        "signature_bytes": signature,
        "signature_text": signature_to_text(signature),
        "public_key": public_key,
        "public_key_fingerprint": public_key_fingerprint(public_key),
        "original_verified": verify_incident(
            incident,
            signature,
            public_key,
        ),
        "tampered_incident": None,
        "tampered_verified": None,
    }


st.title("Attack Simulation")
st.caption(
    "Trigger a security scenario and run it through the live "
    "SentinelAI scoring pipeline."
)

if "sim_result" not in st.session_state:
    st.session_state.sim_result = None
    st.session_state.sim_name = None
    st.session_state.sim_evidence = None

if "sim_evidence" not in st.session_state:
    st.session_state.sim_evidence = None

if (
    st.session_state.sim_result is not None
    and st.session_state.sim_evidence is None
):
    # Results created before evidence signing was enabled are incomplete.
    st.session_state.sim_result = None
    st.session_state.sim_name = None

if "simulated_alerts" not in st.session_state:
    st.session_state.simulated_alerts = []

scenario_columns = st.columns(len(SCENARIOS))

for column, (scenario_name, event) in zip(
    scenario_columns,
    SCENARIOS.items(),
):
    if column.button(
        scenario_name,
        use_container_width=True,
    ):
        try:
            result = score_event(event)
            alert = create_simulated_alert(
                scenario_name,
                event,
                result,
            )
            evidence = create_evidence_record(
                scenario_name,
                event,
                result,
                alert["timestamp"],
            )

            alert["incident_id"] = evidence["incident"]["incident_id"]
            alert["evidence_original_verified"] = evidence[
                "original_verified"
            ]
            alert["evidence_tampered_verified"] = None

            st.session_state.sim_result = result
            st.session_state.sim_name = scenario_name
            st.session_state.sim_evidence = evidence
            existing_alerts = st.session_state.get(
                "simulated_alerts",
                [],
            )
            st.session_state["simulated_alerts"] = [
                alert,
                *existing_alerts,
            ]
            st.success(
                f"{scenario_name} was added to Live Alerts."
            )
        except Exception as error:
            st.session_state.sim_result = None
            st.session_state.sim_name = None
            st.session_state.sim_evidence = None
            st.error(
                f"Could not run {scenario_name}: "
                f"{type(error).__name__}: {error}"
            )

end_simulations = st.button(
    "End simulated attacks",
    disabled=not st.session_state.simulated_alerts,
)

if end_simulations:
    st.session_state.simulated_alerts = []
    st.session_state.sim_result = None
    st.session_state.sim_name = None
    st.session_state.sim_evidence = None
    st.success("All simulated attacks have ended and were removed.")

st.write("")

if st.session_state.sim_result is None:
    st.info("Select a scenario above to simulate an attack.")
else:
    result = st.session_state.sim_result
    evidence = st.session_state.sim_evidence
    tier = str(result["risk_tier"])

    st.subheader(f"Result — {st.session_state.sim_name}")

    score_columns = st.columns(4)
    score_columns[0].metric("Rule score", result["rule_score"])
    score_columns[1].metric("ML score", result["ml_score"])
    score_columns[2].metric("Final score", result["final_score"])
    score_columns[3].markdown(
        f'<p class="metric-label">Risk tier</p>'
        f'<span class="badge {TIER_BADGES.get(tier, "badge-medium")}">'
        f"{tier}</span>",
        unsafe_allow_html=True,
    )

    st.write("")
    reasons = result.get("reasons") or []

    st.markdown("**Why this was flagged**")
    if reasons:
        for reason in reasons:
            st.write(f"- {reason}")
    else:
        st.write("No rule or behavioural anomaly reasons were recorded.")

    st.markdown(
        f'**Recommended action:** {result["recommended_action"]}'
    )

    st.divider()
    st.subheader("Evidence integrity")
    st.caption(
        f'Incident {evidence["incident"]["incident_id"]} was signed '
        "with Ed25519 before being sent to Live Alerts."
    )
    st.info(
        "Classical integrity fallback used in this prototype: Ed25519 "
        "digital signatures. A production design would migrate to "
        "standardized post-quantum digital signatures."
    )

    if evidence["original_verified"]:
        st.success("Original evidence verified successfully.")
    else:
        st.error("Original evidence verification failed.")

    if st.button("Tamper with Evidence"):
        tampered_incident = tamper_incident(evidence["incident"])
        tampered_verified = verify_incident(
            tampered_incident,
            evidence["signature_bytes"],
            evidence["public_key"],
        )
        evidence = {
            **evidence,
            "tampered_incident": tampered_incident,
            "tampered_verified": tampered_verified,
        }
        st.session_state.sim_evidence = evidence

        incident_id = evidence["incident"]["incident_id"]
        st.session_state["simulated_alerts"] = [
            {
                **alert,
                "evidence_tampered_verified": tampered_verified,
            }
            if alert.get("incident_id") == incident_id
            else alert
            for alert in st.session_state.get("simulated_alerts", [])
        ]

    if evidence["tampered_verified"] is False:
        st.success(
            "Tampered evidence verification failed, as expected."
        )
    elif evidence["tampered_verified"] is True:
        st.error("Tampered evidence was incorrectly accepted.")

    with st.expander("View signed evidence details"):
        st.write(
            "**Public-key fingerprint:** "
            f'`{evidence["public_key_fingerprint"]}`'
        )
        st.write(
            f'**Signature (Base64):** `{evidence["signature_text"]}`'
        )
        st.json(evidence["incident"])
