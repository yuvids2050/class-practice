"""
Shared visual styling for the dashboard: colorful gradient KPI cards,
styled headers/dividers, and a consistent sidebar look. Call
apply_custom_css() once near the top of every page (after
st.set_page_config).
"""
import streamlit as st

# A rotating set of vivid gradients applied to st.metric KPI cards in order,
# so a row of KPIs reads as a colorful card strip instead of flat white boxes.
_GRADIENTS = [
    "linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%)",   # indigo -> violet
    "linear-gradient(135deg, #06B6D4 0%, #3B82F6 100%)",   # cyan -> blue
    "linear-gradient(135deg, #F59E0B 0%, #EF4444 100%)",   # amber -> red
    "linear-gradient(135deg, #10B981 0%, #06B6D4 100%)",   # emerald -> cyan
    "linear-gradient(135deg, #EC4899 0%, #8B5CF6 100%)",   # pink -> violet
    "linear-gradient(135deg, #F97316 0%, #F59E0B 100%)",   # orange -> amber
]

# Master vivid palette reused by charts.py so every chart in the app shares
# the same colorful, professional identity.
CHART_PALETTE = [
    "#6366F1", "#06B6D4", "#F59E0B", "#10B981", "#EC4899",
    "#8B5CF6", "#F97316", "#3B82F6", "#EF4444", "#14B8A6",
]


def apply_custom_css():
    st.markdown(
        f"""
        <style>
        /* ---- Page background & typography ---- */
        .stApp {{
            background: #FAFBFF;
        }}
        h1 {{
            color: #312E81;
            font-weight: 800;
            padding-bottom: 0.2rem;
            border-bottom: 4px solid #6366F1;
            display: inline-block;
        }}
        h2, h3 {{
            color: #3730A3;
            font-weight: 700;
        }}

        /* ---- KPI metric cards: colorful gradient, rotating per card ---- */
        div[data-testid="stMetric"] {{
            border-radius: 14px;
            padding: 16px 14px 12px 14px;
            box-shadow: 0 4px 14px rgba(99, 102, 241, 0.18);
            color: white !important;
        }}
        div[data-testid="stHorizontalBlock"] > div:nth-child(6n+1) div[data-testid="stMetric"] {{ background: {_GRADIENTS[0]}; }}
        div[data-testid="stHorizontalBlock"] > div:nth-child(6n+2) div[data-testid="stMetric"] {{ background: {_GRADIENTS[1]}; }}
        div[data-testid="stHorizontalBlock"] > div:nth-child(6n+3) div[data-testid="stMetric"] {{ background: {_GRADIENTS[2]}; }}
        div[data-testid="stHorizontalBlock"] > div:nth-child(6n+4) div[data-testid="stMetric"] {{ background: {_GRADIENTS[3]}; }}
        div[data-testid="stHorizontalBlock"] > div:nth-child(6n+5) div[data-testid="stMetric"] {{ background: {_GRADIENTS[4]}; }}
        div[data-testid="stHorizontalBlock"] > div:nth-child(6n+6) div[data-testid="stMetric"] {{ background: {_GRADIENTS[5]}; }}

        div[data-testid="stMetric"] label,
        div[data-testid="stMetricLabel"] p {{
            color: rgba(255,255,255,0.9) !important;
            font-weight: 600 !important;
        }}
        div[data-testid="stMetricValue"] {{
            color: white !important;
            font-weight: 800 !important;
        }}
        div[data-testid="stMetricDelta"] {{
            color: #ECFDF5 !important;
        }}

        /* ---- Sidebar ---- */
        section[data-testid="stSidebar"] {{
            background: linear-gradient(180deg, #312E81 0%, #4338CA 100%);
        }}
        section[data-testid="stSidebar"] * {{
            color: #EEF2FF !important;
        }}
        section[data-testid="stSidebar"] .stMultiSelect div[data-baseweb="select"] > div {{
            background-color: rgba(255,255,255,0.08);
            color: #EEF2FF;
        }}

        /* ---- Expander / info / caption polish ---- */
        div[data-testid="stExpander"] {{
            border: 1px solid #E0E7FF;
            border-radius: 10px;
        }}
        .stCaption, [data-testid="stCaptionContainer"] {{
            color: #4B5563 !important;
        }}

        /* ---- Dataframe corners ---- */
        div[data-testid="stDataFrame"] {{
            border-radius: 10px;
            overflow: hidden;
        }}

        /* ---- Divider color ---- */
        hr {{
            border-top: 2px solid #E0E7FF;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def section_header(emoji: str, text: str):
    """A colorful pill-style subsection header, used sparingly for emphasis."""
    st.markdown(
        f"""
        <div style="
            display:inline-block;
            background: linear-gradient(135deg, #EEF2FF 0%, #E0E7FF 100%);
            color:#3730A3; font-weight:700; padding:6px 16px;
            border-radius: 999px; margin: 6px 0 10px 0; font-size: 0.95rem;
            border: 1px solid #C7D2FE;">
            {emoji} {text}
        </div>
        """,
        unsafe_allow_html=True,
    )
