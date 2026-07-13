import streamlit as st
from app import load_css

st.set_page_config(page_title="Live Alerts - SentinelAI", layout="wide")
load_css()

# ---------------------------------------------------------------
# TEMP dummy data — matches the frozen score_event() key contract.
# Replace with data/scored_activity_logs.csv once Person A hands it off.
# ---------------------------------------------------------------
ALERTS = [
    {"time": "May 28, 10:24", "user": "dba_admin", "role": "DBA",
     "activity": "Bulk data query", "final_score": 94.1, "risk_tier": "Critical",
     "reasons": ["Unknown device", "Mass download"],
     "recommended_action": "Suspend session and alert the SOC"},
    {"time": "May 28, 09:11", "user": "sys_admin", "role": "Sys Admin",
     "activity": "Privilege escalation", "final_score": 88.6, "risk_tier": "High",
     "reasons": ["Privilege escalation", "After-hours login"],
     "recommended_action": "Require step-up MFA and temporarily restrict sensitive actions"},
    {"time": "May 27, 16:42", "user": "auditor_01", "role": "Auditor",
     "activity": "Sensitive data export", "final_score": 76.3, "risk_tier": "High",
     "reasons": ["Sensitive-data access", "Unusual resource"],
     "recommended_action": "Require step-up MFA and temporarily restrict sensitive actions"},
    {"time": "May 27, 11:03", "user": "vendor_user", "role": "Vendor",
     "activity": "Unusual access time", "final_score": 72.8, "risk_tier": "High",
     "reasons": ["After-hours login", "Unknown device"],
     "recommended_action": "Require step-up MFA and temporarily restrict sensitive actions"},
    {"time": "May 26, 22:18", "user": "dba_admin", "role": "DBA",
     "activity": "Failed access attempts", "final_score": 91.2, "risk_tier": "Critical",
     "reasons": ["Repeated failures", "Audit logging disabled"],
     "recommended_action": "Suspend session and alert the SOC"},
    {"time": "May 26, 14:05", "user": "backup_svc", "role": "Service Account",
     "activity": "Scheduled backup", "final_score": 18.4, "risk_tier": "Low",
     "reasons": [],
     "recommended_action": "Allow access and log activity"},
]

TIER_BADGE = {"Low": "badge-low", "Medium": "badge-medium", "High": "badge-high", "Critical": "badge-critical"}

st.title("Live Alerts")
st.caption("All scored events, filterable by risk tier")

# ---- Filter ----
tier_filter = st.multiselect(
    "Risk tier",
    options=["Low", "Medium", "High", "Critical"],
    default=["High", "Critical"],
)

filtered = [a for a in ALERTS if a["risk_tier"] in tier_filter] if tier_filter else ALERTS

st.write("")
st.markdown('<div class="panel"><p class="panel-title">Alerts</p>', unsafe_allow_html=True)

header = st.columns([1.3, 1, 1, 1.6, 0.7, 0.8])
for c, h in zip(header, ["Time", "User", "Role", "Activity", "Score", "Tier"]):
    c.markdown(f'<span style="font-size:12px;color:#6B7280">{h}</span>', unsafe_allow_html=True)

for i, a in enumerate(filtered):
    row = st.columns([1.3, 1, 1, 1.6, 0.7, 0.8])
    row[0].markdown(f'<span style="font-size:13px">{a["time"]}</span>', unsafe_allow_html=True)
    row[1].markdown(f'<span style="font-size:13px">{a["user"]}</span>', unsafe_allow_html=True)
    row[2].markdown(f'<span style="font-size:13px">{a["role"]}</span>', unsafe_allow_html=True)
    row[3].markdown(f'<span style="font-size:13px">{a["activity"]}</span>', unsafe_allow_html=True)
    row[4].markdown(f'<span style="font-size:13px;font-weight:600">{a["final_score"]}</span>', unsafe_allow_html=True)
    row[5].markdown(
        f'<span class="badge {TIER_BADGE[a["risk_tier"]]}">{a["risk_tier"]}</span>',
        unsafe_allow_html=True,
    )
    with st.expander(f"Details — {a['user']} at {a['time']}", expanded=False):
        st.markdown(
            f'**Reasons:** {", ".join(a["reasons"]) if a["reasons"] else "None"}  \n'
            f'**Recommended action:** {a["recommended_action"]}'
        )

st.markdown("</div>", unsafe_allow_html=True)