import streamlit as st

st.set_page_config(
    page_title="SentinelAI",
    page_icon=":shield:",
    layout="wide",
    initial_sidebar_state="expanded",
)


def load_css():
    st.markdown(
        """
        <style>
        .stApp { background-color: #F7F8FA; }

        [data-testid="stSidebar"] { background-color: #FFFFFF; border-right: 1px solid #E5E7EB; }
        [data-testid="stSidebarNav"] a { color: #4B5563 !important; font-size: 13px; }
        [data-testid="stSidebarNav"] a:hover { color: #111827 !important; }

        h1, h2, h3 { color: #111827; }
        p, span, div { color: #111827; }

        .metric-card {
            background: #FFFFFF;
            border: 1px solid #E5E7EB;
            border-radius: 10px;
            padding: 16px;
        }
        .metric-label { font-size: 13px; color: #6B7280; margin: 0 0 6px 0; }
        .metric-value { font-size: 26px; font-weight: 600; margin: 0; color: #111827; }
        .metric-value.danger { color: #DC2626; }
        .metric-delta { font-size: 12px; margin-top: 6px; }
        .metric-delta.up { color: #16A34A; }
        .metric-delta.down { color: #DC2626; }

        .panel {
            background: #FFFFFF;
            border: 1px solid #E5E7EB;
            border-radius: 10px;
            padding: 16px;
        }
        .panel-title { font-size: 14px; font-weight: 600; color: #111827; margin: 0 0 12px 0; }

        .badge {
            display: inline-block;
            padding: 2px 10px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 600;
        }
        .badge-critical { background: #FEE2E2; color: #DC2626; }
        .badge-high { background: #FFEDD5; color: #EA580C; }
        .badge-medium { background: #FEF9C3; color: #CA8A04; }
        .badge-low { background: #DCFCE7; color: #16A34A; }

        .bar-track { height: 6px; background: #F3F4F6; border-radius: 3px; }
        .bar-fill { height: 100%; border-radius: 3px; }
        </style>
        """,
        unsafe_allow_html=True,
    )


load_css()

st.markdown(
    """
    <h2 style="margin-bottom:0">SentinelAI</h2>
    <p style="color:#6B7280;font-size:13px;margin-top:4px">
    Real-time overview of privileged account activities and security alerts
    </p>
    """,
    unsafe_allow_html=True,
)

st.info("Use the sidebar to navigate to Overview, Live Alerts, Attack Simulation and Evidence Integrity.")