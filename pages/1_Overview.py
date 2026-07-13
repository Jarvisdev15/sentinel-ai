import streamlit as st
import plotly.graph_objects as go
from app import load_css

st.set_page_config(page_title="Overview - SentinelAI", layout="wide")
load_css()

# ---------------------------------------------------------------
# TEMP dummy data — matches the frozen score_event() key contract.
# Replace once scored_activity_logs.csv / real score_event() exist.
# ---------------------------------------------------------------
DUMMY_ALERTS = [
    {"time": "May 28, 10:24", "user": "dba_admin", "role": "DBA",
     "activity": "Bulk data query", "final_score": 94.1, "risk_tier": "Critical"},
    {"time": "May 28, 09:11", "user": "sys_admin", "role": "Sys Admin",
     "activity": "Privilege escalation", "final_score": 88.6, "risk_tier": "High"},
    {"time": "May 27, 16:42", "user": "auditor_01", "role": "Auditor",
     "activity": "Sensitive data export", "final_score": 76.3, "risk_tier": "High"},
    {"time": "May 27, 11:03", "user": "vendor_user", "role": "Vendor",
     "activity": "Unusual access time", "final_score": 72.8, "risk_tier": "High"},
    {"time": "May 26, 22:18", "user": "dba_admin", "role": "DBA",
     "activity": "Failed access attempts", "final_score": 91.2, "risk_tier": "Critical"},
]

TOP_USERS = [
    {"user": "dba_admin", "role": "DBA", "score": 94.1},
    {"user": "sys_admin", "role": "Sys Admin", "score": 88.6},
    {"user": "vendor_user", "role": "Vendor", "score": 72.8},
    {"user": "auditor_01", "role": "Auditor", "score": 65.4},
    {"user": "backup_svc", "role": "Service Account", "score": 59.1},
]

TIER_DIST = {"Low": 56.4, "Medium": 25.9, "High": 14.1, "Critical": 3.6}
TIER_COLORS = {"Low": "#16A34A", "Medium": "#CA8A04", "High": "#EA580C", "Critical": "#DC2626"}
TIER_BADGE = {"Low": "badge-low", "Medium": "badge-medium", "High": "badge-high", "Critical": "badge-critical"}

TREND = [10, 14, 12, 18, 22, 20, 28]
TREND_DAYS = ["May 21", "May 22", "May 23", "May 24", "May 25", "May 26", "May 27"]

st.title("Overview")

# ---- Metric cards ----
kpi_cols = st.columns(4)
kpis = [
    ("Total activities", "12,842", "+18.6% vs last 7 days", "up", False),
    ("High / critical alerts", "23", "+9.5% vs last 7 days", "up", True),
    ("Average risk score", "32.7", "-5.3% vs last 7 days", "down", False),
    ("Critical incidents", "7", "+2 vs last 7 days", "up", True),
]
for col, (label, value, delta, direction, danger) in zip(kpi_cols, kpis):
    vcls = "metric-value danger" if danger else "metric-value"
    dcls = f"metric-delta {direction}"
    col.markdown(
        f'<div class="metric-card">'
        f'<p class="metric-label">{label}</p>'
        f'<p class="{vcls}">{value}</p>'
        f'<p class="{dcls}">{delta}</p>'
        f'</div>',
        unsafe_allow_html=True,
    )

st.write("")

# ---- Risk tier distribution + trend ----
col_left, col_right = st.columns([1, 1.6])

with col_left:
    st.markdown('<div class="panel"><p class="panel-title">Risk tier distribution</p>', unsafe_allow_html=True)
    fig = go.Figure(data=[go.Pie(
        labels=list(TIER_DIST.keys()),
        values=list(TIER_DIST.values()),
        hole=0.65,
        marker=dict(colors=[TIER_COLORS[t] for t in TIER_DIST]),
        textinfo="none",
    )])
    fig.update_layout(
        height=200,
        margin=dict(t=0, b=0, l=0, r=0),
        showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    for tier, pct in TIER_DIST.items():
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:8px;font-size:12px;margin-bottom:4px">'
            f'<span style="width:8px;height:8px;border-radius:50%;background:{TIER_COLORS[tier]}"></span>'
            f'<span style="flex:1;color:#6B7280">{tier}</span>'
            f'<span style="font-weight:600">{pct}%</span></div>',
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)

with col_right:
    st.markdown('<div class="panel"><p class="panel-title">Risk score trend</p>', unsafe_allow_html=True)
    fig2 = go.Figure(data=[go.Scatter(
        x=TREND_DAYS, y=TREND, mode="lines+markers",
        line=dict(color="#2563EB", width=2),
        marker=dict(size=5, color="#2563EB"),
    )])
    fig2.update_layout(
        height=200,
        margin=dict(t=0, b=0, l=0, r=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False, color="#6B7280"),
        yaxis=dict(showgrid=True, gridcolor="#F3F4F6", color="#6B7280"),
    )
    st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})
    st.markdown("</div>", unsafe_allow_html=True)

st.write("")

# ---- Alerts table + top risky users ----
col_a, col_b = st.columns([1.6, 1])

with col_a:
    st.markdown('<div class="panel"><p class="panel-title">Recent high and critical alerts</p>', unsafe_allow_html=True)
    header = st.columns([1.4, 1, 1, 1.6, 0.8, 0.8])
    for c, h in zip(header, ["Time", "User", "Role", "Activity", "Score", "Tier"]):
        c.markdown(f'<span style="font-size:12px;color:#6B7280">{h}</span>', unsafe_allow_html=True)
    for a in DUMMY_ALERTS:
        row = st.columns([1.4, 1, 1, 1.6, 0.8, 0.8])
        row[0].markdown(f'<span style="font-size:13px">{a["time"]}</span>', unsafe_allow_html=True)
        row[1].markdown(f'<span style="font-size:13px">{a["user"]}</span>', unsafe_allow_html=True)
        row[2].markdown(f'<span style="font-size:13px">{a["role"]}</span>', unsafe_allow_html=True)
        row[3].markdown(f'<span style="font-size:13px">{a["activity"]}</span>', unsafe_allow_html=True)
        row[4].markdown(f'<span style="font-size:13px;font-weight:600">{a["final_score"]}</span>', unsafe_allow_html=True)
        row[5].markdown(
            f'<span class="badge {TIER_BADGE[a["risk_tier"]]}">{a["risk_tier"]}</span>',
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)

with col_b:
    st.markdown('<div class="panel"><p class="panel-title">Top risky users</p>', unsafe_allow_html=True)
    for u in TOP_USERS:
        bar_color = "#DC2626" if u["score"] >= 80 else "#EA580C" if u["score"] >= 55 else "#CA8A04"
        st.markdown(
            f'<div style="margin-bottom:10px">'
            f'<div style="display:flex;justify-content:space-between;font-size:13px;margin-bottom:4px">'
            f'<span>{u["user"]}</span><span style="font-weight:600">{u["score"]}</span></div>'
            f'<div class="bar-track"><div class="bar-fill" style="width:{u["score"]}%;background:{bar_color}"></div></div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)