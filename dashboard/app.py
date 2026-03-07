"""
dashboard/app.py
=================
Layer 1 — Job Market Intelligence Dashboard
Skills Mirage | HACKaMINeD 2026

Three tabs:
  Tab A — Hiring Trends (volume by city/sector/time)
  Tab B — Skills Intelligence (rising/falling skills + gap map)
  Tab C — AI Vulnerability Index (risk scores per role × city)

Run: streamlit run dashboard/app.py
"""

import os
import sys
import json
from datetime import datetime, timedelta
from collections import Counter

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Configure Plotly to keep hover tooltips inside the chart
import plotly.io as pio
pio.templates.default = "plotly_dark"

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# ─── Page config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Skills Mirage — Market Intelligence",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600&display=swap');

    /* Global */
    .stApp { background-color: #0f172a; color: #f1f5f9; }
    .main .block-container { padding: 1.5rem 2rem; max-width: 1600px; }

    /* Hide default header and toolbar */
    header[data-testid="stHeader"] { 
        background: transparent !important; 
        display: none !important;
    }
    
    [data-testid="stToolbar"] {
        display: none !important;
    }
    
    .stApp > header {
        background-color: transparent !important;
        display: none !important;
    }

    /* Fonts */
    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; color: #e2e8f0; }
    h1, h2, h3 { font-family: 'Space Mono', monospace; color: #f1f5f9 !important; }
    
    /* Streamlit elements */
    .stMarkdown, .stMarkdown p { color: #e2e8f0 !important; }

    /* Chart containers */
    .js-plotly-plot { 
        background: linear-gradient(135deg, rgba(30,41,59,0.3), rgba(51,65,85,0.2)) !important;
        border: 1px solid #475569;
        border-radius: 12px;
        padding: 1rem;
        margin: 0.5rem 0;
    }

    /* Metric cards */
    .metric-card {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        border: 2px solid #475569;
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        text-align: center;
        position: relative;
        overflow: hidden;
        transition: all 0.3s ease;
    }
    .metric-card:hover {
        border-color: #60a5fa;
        box-shadow: 0 4px 20px rgba(96,165,250,0.2);
    }
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 3px;
        background: linear-gradient(90deg, #60a5fa, #c084fc);
    }
    .metric-value {
        font-family: 'Space Mono', monospace;
        font-size: 2rem;
        font-weight: 700;
        color: #60a5fa;
        display: block;
    }
    .metric-label {
        font-size: 0.8rem;
        color: #cbd5e1;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-top: 0.3rem;
        font-weight: 500;
    }
    .metric-delta {
        font-size: 0.85rem;
        margin-top: 0.4rem;
        font-weight: 600;
    }
    .delta-up { color: #34d399; }
    .delta-down { color: #f87171; }

    /* Section headers */
    .section-header {
        font-family: 'Space Mono', monospace;
        font-size: 0.75rem;
        letter-spacing: 0.2em;
        text-transform: uppercase;
        color: #60a5fa;
        margin-bottom: 0.5rem;
        font-weight: 600;
    }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        background: #111827;
        border-radius: 10px;
        padding: 4px;
        gap: 4px;
        border: 1px solid #1e2a3a;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        color: #94a3b8;
        font-family: 'Space Mono', monospace;
        font-size: 0.75rem;
        letter-spacing: 0.05em;
        padding: 0.5rem 1.2rem;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #1d4ed8, #7c3aed) !important;
        color: white !important;
    }

    /* Sidebar */
    .css-1d391kg, [data-testid="stSidebar"] {
        background: #0d1117 !important;
        border-right: 1px solid #1e2a3a;
    }

    /* Selectbox, slider */
    .stSelectbox > div, .stMultiSelect > div {
        background: #111827 !important;
        border-color: #2d3748 !important;
        color: #e8eaf0 !important;
    }

    /* Risk badge */
    .badge-critical { background:#7f1d1d; color:#fca5a5; padding:2px 10px; border-radius:20px; font-size:0.75rem; font-weight:600; }
    .badge-high     { background:#7c2d12; color:#fdba74; padding:2px 10px; border-radius:20px; font-size:0.75rem; font-weight:600; }
    .badge-medium   { background:#713f12; color:#fcd34d; padding:2px 10px; border-radius:20px; font-size:0.75rem; font-weight:600; }
    .badge-low      { background:#14532d; color:#86efac; padding:2px 10px; border-radius:20px; font-size:0.75rem; font-weight:600; }

    /* Data tables */
    .stDataFrame { border: 1px solid #2d3748; border-radius: 8px; }

    /* Plotly charts transparent bg */
    .js-plotly-plot .plotly { background: transparent !important; }

    /* Info boxes */
    .insight-box {
        background: linear-gradient(135deg, #1e3a5f22, #1e3a5f44);
        border: 1px solid #3b82f633;
        border-left: 3px solid #3b82f6;
        border-radius: 8px;
        padding: 0.8rem 1rem;
        font-size: 0.85rem;
        color: #cbd5e1;
        margin: 0.5rem 0;
    }
    .warning-box {
        background: linear-gradient(135deg, #7f1d1d22, #7f1d1d44);
        border: 1px solid #ef444433;
        border-left: 3px solid #ef4444;
        border-radius: 8px;
        padding: 0.8rem 1rem;
        font-size: 0.85rem;
        color: #fca5a5;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Load custom CSS
try:
    with open('static/custom.css') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
except FileNotFoundError:
    pass  # Custom CSS is optional


# ─────────────────────────────────────────────────────────────────────────────
# DATA LOADING
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=300)  # Refresh every 5 minutes
def load_jobs():
    """Load job listings from database."""
    try:
        from db.schema import get_session, JobListing
        session = get_session()
        jobs = session.query(JobListing).all()
        session.close()

        data = []
        for j in jobs:
            skills = j.skills_parsed or []
            if isinstance(skills, str):
                try:
                    skills = json.loads(skills)
                except:
                    skills = []
            data.append({
                "id": j.id,
                "title": j.title or "",
                "company": j.company or "",
                "city": j.city or "Unknown",
                "sector": j.sector or "Other",
                "experience_min": j.experience_min or 0,
                "skills": skills,
                "skills_raw": j.skills_raw or "",
                "ai_tool_mentions": j.ai_tool_mentions or 0,
                "scraped_at": j.scraped_at or datetime.utcnow(),
                "source": j.source or "",
            })
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"DB Error: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=300)
def load_vulnerability():
    """Load vulnerability index scores."""
    try:
        from db.schema import get_session, VulnerabilityIndex
        session = get_session()
        records = session.query(VulnerabilityIndex).order_by(
            VulnerabilityIndex.computed_at.desc()
        ).all()
        session.close()

        data = []
        for r in records:
            data.append({
                "job_category": r.job_category,
                "city": r.city,
                "score": r.score,
                "risk_level": r.risk_level,
                "hiring_trend_pct": r.hiring_trend_pct or 0,
                "ai_mention_rate": r.ai_mention_rate or 0,
                "replacement_ratio": r.replacement_ratio or 0,
                "computed_at": r.computed_at,
            })
        return pd.DataFrame(data)
    except Exception as e:
        return pd.DataFrame()


@st.cache_data(ttl=3600)
def load_courses():
    """Load training courses."""
    try:
        from db.schema import get_session, TrainingCourse
        session = get_session()
        courses = session.query(TrainingCourse).all()
        session.close()
        data = []
        for c in courses:
            topics = c.topics or []
            if isinstance(topics, str):
                try:
                    topics = json.loads(topics)
                except:
                    topics = []
            data.append({
                "title": c.title,
                "source": c.source,
                "institution": c.institution,
                "duration_weeks": c.duration_weeks or 8,
                "topics": topics,
                "level": c.level,
                "url": c.url,
            })
        return pd.DataFrame(data)
    except:
        return pd.DataFrame()


# ─────────────────────────────────────────────────────────────────────────────
# COMPUTED METRICS (from jobs DataFrame)
# ─────────────────────────────────────────────────────────────────────────────

def truncate_label(text, max_length=20):
    """Truncate long text labels to fit in chart boxes."""
    if not text or not isinstance(text, str):
        return text
    text = str(text).strip()
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

def compute_skill_trends(df):
    """Count skill occurrences across all jobs."""
    skill_counts = Counter()
    for _, row in df.iterrows():
        skills = row.get("skills", [])
        if isinstance(skills, list):
            for s in skills:
                if s and len(s) > 1:
                    skill_counts[s.lower().strip()] += 1
    return skill_counts


def get_city_sector_counts(df, days=30):
    """Job counts by city and sector for last N days."""
    cutoff = datetime.utcnow() - timedelta(days=days)
    filtered = df[df["scraped_at"] >= cutoff] if not df.empty else df
    if filtered.empty:
        return df  # fallback to all data if no recent data
    return filtered


def compute_sector_trend(df, sector, days_recent=14, days_past=14):
    """Compare recent vs past hiring for a sector."""
    now = datetime.utcnow()
    recent = df[
        (df["sector"] == sector) &
        (df["scraped_at"] >= now - timedelta(days=days_recent))
    ]
    past = df[
        (df["sector"] == sector) &
        (df["scraped_at"] >= now - timedelta(days=days_recent + days_past)) &
        (df["scraped_at"] < now - timedelta(days=days_recent))
    ]
    if len(past) == 0:
        return 0
    return ((len(recent) - len(past)) / len(past)) * 100


# ─────────────────────────────────────────────────────────────────────────────
# PLOTLY THEME - Enhanced for better visibility and cleaner look
# ─────────────────────────────────────────────────────────────────────────────

# Base layout — improved for better readability
PLOT_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(30,41,59,0.4)",
    font=dict(family="DM Sans", color="#e2e8f0", size=13),
    title_font=dict(family="Space Mono", color="#f1f5f9", size=16, weight=600),
    margin=dict(l=60, r=40, t=60, b=60),
    hovermode=False  # Disable all hover tooltips
)

_AXIS = dict(
    gridcolor="rgba(71,85,105,0.3)",
    linecolor="#475569",
    tickfont=dict(color="#cbd5e1", size=12),
    title=dict(font=dict(color="#f1f5f9", size=14, family="Space Mono")),
    showgrid=True,
    zeroline=False,
)

_LEGEND = dict(
    bgcolor="rgba(30,41,59,0.8)",
    font=dict(color="#e2e8f0", size=12),
    bordercolor="#475569",
    borderwidth=1,
    orientation="h",
    yanchor="bottom",
    y=1.02,
    xanchor="right",
    x=1
)

def PL(height=450, xtick=None, yrange=None, **kw):
    """Build update_layout dict safely — no duplicate key conflicts."""
    xax = dict(_AXIS)
    if xtick is not None:
        xax["tickangle"] = xtick
    xax["automargin"] = True
    xax["tickmode"] = "linear"
    
    yax = dict(_AXIS)
    if yrange:
        yax["range"] = yrange
    yax["automargin"] = True
    
    # Generous margins to contain all text
    default_margin = dict(l=150, r=60, t=70, b=150, pad=15)
    margin = kw.pop("margin", default_margin)
    
    return {
        **PLOT_LAYOUT, 
        "height": height, 
        "xaxis": xax, 
        "yaxis": yax, 
        "legend": _LEGEND,
        "margin": margin,
        "autosize": True,
        **kw
    }

# Enhanced color palette - more vibrant and distinguishable
COLOR_SEQ = ["#60a5fa", "#c084fc", "#34d399", "#fbbf24", "#f87171",
             "#a78bfa", "#2dd4bf", "#fb923c", "#f472b6", "#818cf8"]

RISK_COLORS = {
    "Critical": "#ef4444",
    "High":     "#f97316",
    "Medium":   "#fbbf24",
    "Low":      "#22c55e",
}


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────

def render_sidebar(df):
    with st.sidebar:
        st.markdown("""
        <div style='text-align:center; padding: 1rem 0 1.5rem;'>
            <div style='font-family: Space Mono; font-size: 1.1rem; color: #60a5fa; font-weight: 700;'>
                🧠 SKILLS MIRAGE
            </div>
            <div style='font-size: 0.7rem; color: #475569; letter-spacing: 0.15em; margin-top: 4px;'>
                WORKFORCE INTELLIGENCE
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div class='section-header'>⚙ FILTERS</div>", unsafe_allow_html=True)

        # Time range
        time_range = st.selectbox(
            "Time Range",
            ["Last 7 days", "Last 30 days", "Last 90 days", "All time"],
            index=3,
        )

        # Cities
        all_cities = sorted(df["city"].unique().tolist()) if not df.empty else []
        selected_cities = st.multiselect(
            "Cities",
            all_cities,
            default=all_cities[:5] if len(all_cities) >= 5 else all_cities,
            placeholder="Select cities..."
        )

        # Sectors
        all_sectors = sorted(df["sector"].unique().tolist()) if not df.empty else []
        selected_sectors = st.multiselect(
            "Sectors",
            all_sectors,
            default=all_sectors,
            placeholder="Select sectors..."
        )

        st.divider()
        st.markdown("<div class='section-header'>📊 DATABASE STATUS</div>", unsafe_allow_html=True)
        if not df.empty:
            st.markdown(f"""
            <div style='font-size: 0.8rem; color: #64748b; line-height: 2;'>
                Total jobs: <span style='color:#60a5fa'>{len(df):,}</span><br>
                Cities: <span style='color:#60a5fa'>{df['city'].nunique()}</span><br>
                Sectors: <span style='color:#60a5fa'>{df['sector'].nunique()}</span><br>
                Last update: <span style='color:#60a5fa'>just now</span>
            </div>
            """, unsafe_allow_html=True)

        st.divider()
        if st.button("🔄 Refresh Data", width='stretch'):
            st.cache_data.clear()
            st.rerun()

        # Map time range to days
        time_map = {"Last 7 days": 7, "Last 30 days": 30, "Last 90 days": 90, "All time": 9999}
        days = time_map[time_range]

    return selected_cities, selected_sectors, days


# ─────────────────────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────────────────────

def render_header(df):
    st.markdown("""
    <div style='margin-bottom: 1.5rem;'>
        <div style='font-family: Space Mono; font-size: 1.6rem; font-weight: 700; color: #e8eaf0;'>
            India Workforce Intelligence Dashboard
        </div>
        <div style='font-size: 0.85rem; color: #475569; margin-top: 4px;'>
            Real-time signals from Naukri · LinkedIn · PLFS · Updated every 30 minutes
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Top metrics
    total_jobs = len(df) if not df.empty else 0
    total_cities = df["city"].nunique() if not df.empty else 0
    total_sectors = df["sector"].nunique() if not df.empty else 0
    ai_jobs = len(df[df["ai_tool_mentions"] > 0]) if not df.empty else 0
    ai_pct = int((ai_jobs / total_jobs * 100)) if total_jobs > 0 else 0

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class='metric-card'>
            <span class='metric-value'>{total_jobs:,}</span>
            <div class='metric-label'>Total Job Listings</div>
            <div class='metric-delta delta-up'>↑ live data</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class='metric-card'>
            <span class='metric-value'>{total_cities}</span>
            <div class='metric-label'>Cities Tracked</div>
            <div class='metric-delta' style='color:#94a3b8'>Tier 1 · 2 · 3</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class='metric-card'>
            <span class='metric-value'>{total_sectors}</span>
            <div class='metric-label'>Sectors Monitored</div>
            <div class='metric-delta' style='color:#94a3b8'>across all roles</div>
        </div>""", unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class='metric-card'>
            <span class='metric-value'>{ai_pct}%</span>
            <div class='metric-label'>JDs Mentioning AI</div>
            <div class='metric-delta delta-up'>↑ rising signal</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# TAB A — HIRING TRENDS
# ─────────────────────────────────────────────────────────────────────────────

def render_tab_a(df, selected_cities, selected_sectors, days):
    st.markdown("### 📈 Hiring Trends")
    st.markdown("""
    <div class='insight-box'>
        Live job volume by city, sector, and time. Signals where hiring is accelerating or collapsing.
    </div>
    """, unsafe_allow_html=True)

    if df.empty:
        st.warning("No data available. Run the pipeline first.")
        return

    # Filter
    filtered = df.copy()
    if selected_cities:
        filtered = filtered[filtered["city"].isin(selected_cities)]
    if selected_sectors:
        filtered = filtered[filtered["sector"].isin(selected_sectors)]
    if days < 9999:
        cutoff = datetime.utcnow() - timedelta(days=days)
        recent = filtered[filtered["scraped_at"] >= cutoff]
        if not recent.empty:
            filtered = recent

    col1, col2 = st.columns(2)

    # ── Chart 1: Top cities by job volume ────────────────────────────────────
    with col1:
        st.markdown("<div class='section-header'>📍 Top Cities by Job Volume</div>", unsafe_allow_html=True)
        city_counts = filtered["city"].value_counts().head(20).reset_index()
        city_counts.columns = ["City", "Jobs"]
        
        # Wrap text for display
        city_counts["City_Display"] = city_counts["City"].apply(lambda x: '<br>'.join([x[i:i+15] for i in range(0, len(str(x)), 15)]) if len(str(x)) > 15 else str(x))

        fig = px.bar(
            city_counts, x="Jobs", y="City_Display", orientation="h",
            color="Jobs", 
            color_continuous_scale=["#60a5fa", "#c084fc", "#f472b6"],
            labels={"Jobs": "Number of Jobs", "City_Display": ""}
        )
        fig.update_layout(
            height=600, 
            showlegend=False, 
            coloraxis_showscale=False,
            margin=dict(l=150, r=40, t=40, b=60),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(30,41,59,0.4)",
            font=dict(family="DM Sans", color="#e2e8f0", size=11),
            xaxis_title="Number of Jobs",
            yaxis_title="",
            xaxis=dict(
                gridcolor="rgba(71,85,105,0.3)",
                linecolor="#475569",
                tickfont=dict(color="#cbd5e1", size=11),
                automargin=True
            ),
            yaxis=dict(
                gridcolor="rgba(71,85,105,0.3)",
                linecolor="#475569",
                tickfont=dict(color="#cbd5e1", size=9),
                automargin=True
            ),
            hovermode=False
        )
        fig.update_traces(
            marker_line_width=0,
            hoverinfo='skip'
        )
        st.plotly_chart(fig, use_container_width=True, key="city_bar")

    # ── Chart 2: Jobs by Sector ───────────────────────────────────────────────
    with col2:
        st.markdown("<div class='section-header'>🏢 Job Distribution by Sector</div>", unsafe_allow_html=True)
        sector_counts = filtered["sector"].value_counts().reset_index()
        sector_counts.columns = ["Sector", "Jobs"]

        fig2 = px.pie(
            sector_counts, names="Sector", values="Jobs",
            color_discrete_sequence=COLOR_SEQ,
            hole=0.4,
        )
        fig2.update_layout(
            height=600,
            showlegend=True,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(30,41,59,0.4)",
            font=dict(family="DM Sans", color="#e2e8f0", size=10),
            margin=dict(l=20, r=180, t=40, b=40),
            legend=dict(
                title=dict(text="Sectors", font=dict(size=11, color="#f1f5f9")),
                orientation="v",
                yanchor="middle",
                y=0.5,
                xanchor="left",
                x=1.05,
                font=dict(size=10, color="#e2e8f0"),
                bgcolor="rgba(30,41,59,0.9)",
                bordercolor="#475569",
                borderwidth=1,
                itemsizing='constant'
            ),
            hovermode=False
        )
        fig2.update_traces(
            textposition="inside", 
            textinfo="percent",
            textfont_size=11,
            textfont_color="white",
            marker=dict(line=dict(color='#1e293b', width=2)),
            hoverinfo='skip',
            showlegend=True
        )
        st.plotly_chart(fig2, use_container_width=True, key="sector_pie")

    # ── Chart 3: City × Sector heatmap ───────────────────────────────────────
    st.markdown("<div class='section-header'>🗺️ City × Sector Hiring Heatmap</div>", unsafe_allow_html=True)

    top_cities = filtered["city"].value_counts().head(15).index.tolist()
    top_sectors = filtered["sector"].value_counts().head(12).index.tolist()

    heatmap_data = filtered[
        filtered["city"].isin(top_cities) & filtered["sector"].isin(top_sectors)
    ]

    if not heatmap_data.empty:
        pivot = heatmap_data.groupby(["city", "sector"]).size().reset_index(name="count")
        pivot_wide = pivot.pivot(index="city", columns="sector", values="count").fillna(0)

        # Wrap labels for display
        city_labels = ['<br>'.join([c[i:i+12] for i in range(0, len(c), 12)]) for c in pivot_wide.index.tolist()]
        sector_labels = ['<br>'.join([s[i:i+15] for i in range(0, len(s), 15)]) for s in pivot_wide.columns.tolist()]
        city_full = pivot_wide.index.tolist()
        sector_full = pivot_wide.columns.tolist()

        fig3 = go.Figure(data=go.Heatmap(
            z=pivot_wide.values,
            x=sector_labels,
            y=city_labels,
            colorscale=[[0, "#1e3a5f"], [0.3, "#3b82f6"], [0.6, "#8b5cf6"], [0.8, "#c084fc"], [1, "#f472b6"]],
            hoverongaps=False,
            hoverinfo='skip',
            colorbar=dict(
                title=dict(text="Jobs", font=dict(color="#f1f5f9", size=11)),
                tickfont=dict(color="#cbd5e1", size=10),
                bgcolor="rgba(30,41,59,0.8)",
                bordercolor="#475569",
                borderwidth=1
            )
        ))
        fig3.update_layout(
            height=500,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(30,41,59,0.4)",
            font=dict(family="DM Sans", color="#e2e8f0", size=9),
            margin=dict(l=120, r=60, t=40, b=150),
            xaxis_title="Sector",
            yaxis_title="City",
            xaxis=dict(
                gridcolor="rgba(71,85,105,0.3)",
                linecolor="#475569",
                tickfont=dict(color="#cbd5e1", size=8),
                automargin=True,
                side="bottom"
            ),
            yaxis=dict(
                gridcolor="rgba(71,85,105,0.3)",
                linecolor="#475569",
                tickfont=dict(color="#cbd5e1", size=8),
                automargin=True
            ),
            hovermode=False
        )
        st.plotly_chart(fig3, use_container_width=True, key="heatmap")

    # ── Chart 4: Sector trends (which sectors are growing/declining) ──────────
    st.markdown("<div class='section-header'>📈 Sector Hiring Trends — Ranked by Volume</div>", unsafe_allow_html=True)

    sector_data = []
    for sector in filtered["sector"].unique():
        count = len(filtered[filtered["sector"] == sector])
        ai_count = len(filtered[(filtered["sector"] == sector) & (filtered["ai_tool_mentions"] > 0)])
        ai_rate = round(ai_count / count * 100, 1) if count > 0 else 0
        # Wrap sector names
        sector_wrapped = '<br>'.join([sector[i:i+18] for i in range(0, len(sector), 18)])
        sector_data.append({
            "Sector": sector,
            "Sector_Display": sector_wrapped,
            "Total Jobs": count,
            "AI Mention Rate": f"{ai_rate}%",
            "AI Mentions": ai_count,
        })

    if sector_data:
        sector_df = pd.DataFrame(sector_data).sort_values("Total Jobs", ascending=False)

        fig4 = px.bar(
            sector_df, x="Sector_Display", y="Total Jobs",
            color="AI Mentions",
            color_continuous_scale=["#3b82f6", "#8b5cf6", "#f472b6"],
            labels={"Total Jobs": "Number of Jobs", "AI Mentions": "AI Tool Mentions", "Sector_Display": "Sector"},
            hover_data=["AI Mention Rate"],
        )
        fig4.update_layout(
            height=450,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(30,41,59,0.4)",
            font=dict(family="DM Sans", color="#e2e8f0", size=10),
            margin=dict(l=60, r=60, t=40, b=180),
            xaxis_title="Sector",
            yaxis_title="Number of Jobs",
            coloraxis_colorbar=dict(
                title=dict(text="AI Mentions", font=dict(color="#f1f5f9", size=11)),
                tickfont=dict(color="#cbd5e1", size=10),
                bgcolor="rgba(30,41,59,0.8)",
                bordercolor="#475569",
                borderwidth=1
            ),
            xaxis=dict(
                gridcolor="rgba(71,85,105,0.3)",
                linecolor="#475569",
                tickfont=dict(color="#cbd5e1", size=8),
                automargin=True
            ),
            yaxis=dict(
                gridcolor="rgba(71,85,105,0.3)",
                linecolor="#475569",
                tickfont=dict(color="#cbd5e1", size=11),
                automargin=True
            ),
            hovermode=False
        )
        fig4.update_traces(
            marker_line_width=0,
            hoverinfo='skip'
        )
        st.plotly_chart(fig4, use_container_width=True, key="sector_trends")
    else:
        st.info("No sector data available with current filters.")


# ─────────────────────────────────────────────────────────────────────────────
# TAB B — SKILLS INTELLIGENCE
# ─────────────────────────────────────────────────────────────────────────────

def render_tab_b(df, courses_df, selected_cities, selected_sectors, days):
    st.markdown("### 🔬 Skills Intelligence")
    st.markdown("""
    <div class='insight-box'>
        What skills employers are demanding vs what training institutions are teaching.
        The gap is where workers fall through the cracks.
    </div>
    """, unsafe_allow_html=True)

    if df.empty:
        st.warning("No data available.")
        return

    # Filter
    filtered = df.copy()
    if selected_cities:
        filtered = filtered[filtered["city"].isin(selected_cities)]

    # ── Skill counts ──────────────────────────────────────────────────────────
    skill_counts = compute_skill_trends(filtered)
    skill_df = pd.DataFrame([
        {"Skill": k, "Demand": v}
        for k, v in skill_counts.most_common(40)
        if len(k) > 1
    ])

    col1, col2 = st.columns(2)

    # Top 30 in-demand skills
    with col1:
        st.markdown("<div class='section-header'>🔥 Top 30 In-Demand Skills</div>", unsafe_allow_html=True)
        top30 = skill_df.head(30).copy()
        # Wrap skill names
        top30["Skill_Display"] = top30["Skill"].apply(lambda x: '<br>'.join([x[i:i+15] for i in range(0, len(str(x)), 15)]))
        
        fig = px.bar(
            top30, x="Demand", y="Skill_Display", orientation="h",
            color="Demand",
            color_continuous_scale=["#3b82f6", "#8b5cf6", "#f472b6"],
        )
        fig.update_layout(
            height=800,
            showlegend=False,
            coloraxis_showscale=False,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(30,41,59,0.4)",
            font=dict(family="DM Sans", color="#e2e8f0", size=10),
            margin=dict(l=140, r=20, t=40, b=40),
            xaxis=dict(
                gridcolor="rgba(71,85,105,0.3)",
                linecolor="#475569",
                tickfont=dict(color="#cbd5e1", size=11),
                automargin=True
            ),
            yaxis=dict(
                gridcolor="rgba(71,85,105,0.3)",
                linecolor="#475569",
                tickfont=dict(color="#cbd5e1", size=8),
                automargin=True
            ),
            hovermode=False
        )
        fig.update_traces(
            marker_line_width=0,
            hoverinfo='skip'
        )
        st.plotly_chart(fig, use_container_width=True)

    # Skills by sector
    with col2:
        st.markdown("<div class='section-header'>Skills Concentration by Sector</div>", unsafe_allow_html=True)

        sector_skills = {}
        for sector in filtered["sector"].unique():
            sector_df_f = filtered[filtered["sector"] == sector]
            sc = compute_skill_trends(sector_df_f)
            if sc:
                top_skill = sc.most_common(1)[0][0]
                sector_wrapped = '<br>'.join([sector[i:i+15] for i in range(0, len(sector), 15)])
                sector_skills[sector] = {
                    "sector": sector,
                    "sector_display": sector_wrapped,
                    "top_skill": top_skill,
                    "unique_skills": len(sc),
                    "total_mentions": sum(sc.values()),
                }

        if sector_skills:
            ss_df = pd.DataFrame(list(sector_skills.values())).sort_values(
                "total_mentions", ascending=False
            )
            fig2 = px.scatter(
                ss_df, x="sector_display", y="unique_skills",
                size="total_mentions", color="total_mentions",
                color_continuous_scale=["#3b82f6", "#8b5cf6", "#f472b6"],
                hover_data=["top_skill", "total_mentions"],
                size_max=60,
            )
            fig2.update_layout(
                height=800,
                coloraxis_showscale=False,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(30,41,59,0.4)",
                font=dict(family="DM Sans", color="#e2e8f0", size=10),
                margin=dict(l=60, r=40, t=40, b=180),
                xaxis=dict(
                    gridcolor="rgba(71,85,105,0.3)",
                    linecolor="#475569",
                    tickfont=dict(color="#cbd5e1", size=8),
                    automargin=True
                ),
                yaxis=dict(
                    gridcolor="rgba(71,85,105,0.3)",
                    linecolor="#475569",
                    tickfont=dict(color="#cbd5e1", size=11),
                    automargin=True
                ),
                hovermode=False
            )
            fig2.update_traces(
                hoverinfo='skip'
            )
            st.plotly_chart(fig2, use_container_width=True)

    # ── Skill Gap Map ─────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("<div class='section-header'>🎯 Skill Gap Map — Market Demand vs Training Supply</div>",
                unsafe_allow_html=True)
    st.markdown("""
    <div class='warning-box'>
        ⚠️ Red = High demand from employers but LOW coverage in NPTEL/SWAYAM.
        These are the reskilling gaps India needs to close.
    </div>
    """, unsafe_allow_html=True)

    # Get skills being trained (from courses)
    trained_skills = set()
    if not courses_df.empty:
        for _, row in courses_df.iterrows():
            topics = row.get("topics", [])
            if isinstance(topics, list):
                trained_skills.update([t.lower() for t in topics])

    # Build gap analysis
    gap_data = []
    for skill, demand in skill_counts.most_common(35):
        is_trained = any(skill in t or t in skill for t in trained_skills)
        gap_score = demand if not is_trained else demand * 0.2
        skill_wrapped = '<br>'.join([skill[i:i+15] for i in range(0, len(skill), 15)])
        gap_data.append({
            "Skill": skill,
            "Skill_Display": skill_wrapped,
            "Market Demand": demand,
            "Training Coverage": "✅ Covered" if is_trained else "❌ Gap",
            "Gap Score": round(gap_score),
            "color": "#34d399" if is_trained else "#f87171",
        })

    gap_df = pd.DataFrame(gap_data).sort_values("Gap Score", ascending=False)

    fig3 = go.Figure()
    for _, row in gap_df.iterrows():
        fig3.add_trace(go.Bar(
            x=[row["Skill_Display"]],
            y=[row["Market Demand"]],
            marker_color=row["color"],
            name=row["Training Coverage"],
            showlegend=False,
            hovertemplate=f"<b>{row['Skill']}</b><br>Demand: {row['Market Demand']}<br>{row['Training Coverage']}<extra></extra>",
        ))

    # Legend manually
    fig3.add_trace(go.Bar(x=[None], y=[None], marker_color="#34d399", name="✅ Training exists", showlegend=True))
    fig3.add_trace(go.Bar(x=[None], y=[None], marker_color="#f87171", name="❌ Training gap", showlegend=True))

    fig3.update_layout(
        height=550,
        barmode="overlay",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(30,41,59,0.4)",
        font=dict(family="DM Sans", color="#e2e8f0", size=10),
        margin=dict(l=60, r=40, t=60, b=180),
        legend=dict(orientation="h", y=1.12, x=0, bgcolor="rgba(0,0,0,0)", font=dict(color="#94a3b8")),
        xaxis=dict(
            gridcolor="rgba(71,85,105,0.3)",
            linecolor="#475569",
            tickfont=dict(color="#cbd5e1", size=8),
            automargin=True
        ),
        yaxis=dict(
            gridcolor="rgba(71,85,105,0.3)",
            linecolor="#475569",
            tickfont=dict(color="#cbd5e1", size=11),
            automargin=True
        ),
        hovermode=False
    )
    st.plotly_chart(fig3, use_container_width=True)

    # ── Skills by City ────────────────────────────────────────────────────────
    st.markdown("<div class='section-header'>Top Skills per City</div>", unsafe_allow_html=True)

    city_skill_data = []
    top_cities = filtered["city"].value_counts().head(15).index.tolist()
    for city in top_cities:
        city_jobs = filtered[filtered["city"] == city]
        sc = compute_skill_trends(city_jobs)
        top5 = [s for s, _ in sc.most_common(5)]
        city_skill_data.append({
            "City": city,
            "Jobs": len(city_jobs),
            "Top Skills": " · ".join(top5) if top5 else "N/A",
            "#1 Skill": top5[0] if top5 else "N/A",
        })

    cs_df = pd.DataFrame(city_skill_data)
    st.dataframe(
        cs_df,
        width='stretch',
        hide_index=True,
        column_config={
            "City": st.column_config.TextColumn("City"),
            "Jobs": st.column_config.NumberColumn("Jobs", format="%d"),
            "Top Skills": st.column_config.TextColumn("Top 5 Skills in Demand"),
            "#1 Skill": st.column_config.TextColumn("Most Demanded"),
        }
    )


# ─────────────────────────────────────────────────────────────────────────────
# TAB C — AI VULNERABILITY INDEX
# ─────────────────────────────────────────────────────────────────────────────

def render_tab_c(df, vuln_df):
    st.markdown("### ⚠️ AI Vulnerability Index")
    st.markdown("""
    <div class='warning-box'>
        Score 0–100 per job category × city. Computed from: hiring decline (40%) +
        AI tool mentions in JDs (40%) + role replacement signals (20%).
        Higher = more at risk from AI displacement.
    </div>
    """, unsafe_allow_html=True)

    # ── If no computed scores yet, compute live from jobs ────────────────────
    if vuln_df.empty and not df.empty:
        st.info("Computing vulnerability scores from job data...")
        vuln_df = compute_vulnerability_live(df)

    if vuln_df.empty:
        st.warning("Not enough data to compute vulnerability scores yet. Run the pipeline.")
        return

    # ── Top metrics ───────────────────────────────────────────────────────────
    critical = len(vuln_df[vuln_df["risk_level"] == "Critical"])
    high = len(vuln_df[vuln_df["risk_level"] == "High"])
    medium = len(vuln_df[vuln_df["risk_level"] == "Medium"])
    low = len(vuln_df[vuln_df["risk_level"] == "Low"])

    c1, c2, c3, c4 = st.columns(4)
    for col, label, count, color, badge_class in [
        (c1, "Critical Risk", critical, "#ef4444", "badge-critical"),
        (c2, "High Risk", high, "#f97316", "badge-high"),
        (c3, "Medium Risk", medium, "#eab308", "badge-medium"),
        (c4, "Low Risk", low, "#22c55e", "badge-low"),
    ]:
        with col:
            st.markdown(f"""
            <div class='metric-card'>
                <span class='metric-value' style='color:{color}'>{count}</span>
                <div class='metric-label'>{label} Categories</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns([3, 2])

    # ── Heatmap: Job Category × City ─────────────────────────────────────────
    with col1:
        st.markdown("<div class='section-header'>Vulnerability Heatmap — Job Category × City</div>",
                    unsafe_allow_html=True)

        if not vuln_df.empty:
            pivot = vuln_df.pivot_table(
                index="job_category", columns="city", values="score", aggfunc="mean"
            ).fillna(0)

            # Limit size for readability
            top_cats = vuln_df.groupby("job_category")["score"].mean().nlargest(15).index
            top_cities = vuln_df.groupby("city")["score"].mean().nlargest(12).index
            pivot = pivot.loc[
                pivot.index.isin(top_cats),
                pivot.columns.isin(top_cities)
            ]

            # Wrap labels for display
            cat_labels = ['<br>'.join([c[i:i+15] for i in range(0, len(c), 15)]) for c in pivot.index.tolist()]
            city_labels = ['<br>'.join([c[i:i+12] for i in range(0, len(c), 12)]) for c in pivot.columns.tolist()]
            cat_full = pivot.index.tolist()
            city_full = pivot.columns.tolist()

            fig = go.Figure(data=go.Heatmap(
                z=pivot.values,
                x=city_labels,
                y=cat_labels,
                colorscale=[
                    [0.0, "#22c55e"],
                    [0.25, "#34d399"],
                    [0.5, "#fbbf24"],
                    [0.75, "#f97316"],
                    [1.0, "#ef4444"],
                ],
                zmin=0, zmax=100,
                hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]}<br>Score: <b>%{z:.0f}/100</b><extra></extra>",
                customdata=[[[cat_full[i], city_full[j]] for j in range(len(city_full))] for i in range(len(cat_full))],
                colorbar=dict(
                    title="Risk Score",
                    tickvals=[0, 25, 50, 75, 100],
                    ticktext=["0 Low", "25", "50 Med", "75", "100 Critical"],
                    tickfont=dict(color="#64748b", size=10),
                    title_font=dict(color="#94a3b8"),
                ),
            ))
            fig.update_layout(
                height=520,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(30,41,59,0.4)",
                font=dict(family="DM Sans", color="#e2e8f0", size=9),
                margin=dict(l=140, r=60, t=40, b=120),
                xaxis=dict(
                    gridcolor="rgba(71,85,105,0.3)",
                    linecolor="#475569",
                    tickfont=dict(color="#cbd5e1", size=8),
                    automargin=True
                ),
                yaxis=dict(
                    gridcolor="rgba(71,85,105,0.3)",
                    linecolor="#475569",
                    tickfont=dict(color="#cbd5e1", size=8),
                    automargin=True
                ),
                hovermode=False
            )
            st.plotly_chart(fig, use_container_width=True)

    # ── Top at-risk roles table ───────────────────────────────────────────────
    with col2:
        st.markdown("<div class='section-header'>Most At-Risk Roles</div>",
                    unsafe_allow_html=True)

        top_risk = vuln_df.sort_values("score", ascending=False).head(20)

        for _, row in top_risk.iterrows():
            score = row["score"]
            risk = row["risk_level"]
            badge_class = f"badge-{risk.lower()}"
            bar_width = int(score)
            bar_color = RISK_COLORS.get(risk, "#94a3b8")

            st.markdown(f"""
            <div style='margin-bottom: 0.6rem; padding: 0.6rem 0.8rem;
                        background: #111827; border-radius: 8px;
                        border: 1px solid #1e2a3a;'>
                <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;'>
                    <div style='font-size:0.8rem; color:#e2e8f0; font-weight:500;'>
                        {row['job_category']}
                    </div>
                    <span class='{badge_class}'>{risk}</span>
                </div>
                <div style='font-size:0.7rem; color:#475569; margin-bottom:5px;'>
                    {row['city']}
                </div>
                <div style='background:#1e2a3a; border-radius:4px; height:5px; overflow:hidden;'>
                    <div style='width:{bar_width}%; background:{bar_color};
                                height:100%; border-radius:4px;'></div>
                </div>
                <div style='font-size:0.7rem; color:{bar_color}; margin-top:3px;'>
                    {score:.0f} / 100
                </div>
            </div>
            """, unsafe_allow_html=True)

    # ── Methodology panel ─────────────────────────────────────────────────────
    st.markdown("---")
    with st.expander("📐 Score Methodology — No Black Boxes", expanded=False):
        st.markdown("""
        <div style='font-size:0.85rem; color:#e2e8f0; line-height:1.8;'>

        <p style='color:#f1f5f9; font-weight:600; margin-bottom:0.5rem;'>Score Formula:</p>
        <pre style='background:#0f172a; border:1px solid #334155; border-radius:8px; padding:1rem; margin:0.5rem 0; font-family:monospace; color:#cbd5e1; overflow-x:auto;'>score = (0.40 × hiring_decline_score)
        + (0.40 × ai_mention_score)
        + (0.20 × replacement_score)</pre>

        <p style='color:#f1f5f9; font-weight:600; margin:1rem 0 0.5rem 0;'>Component Definitions:</p>

        <table style='width:100%; border-collapse:collapse; margin:0.5rem 0;'>
        <tr style='border-bottom:1px solid #334155;'>
            <th style='text-align:left; padding:0.5rem; color:#60a5fa;'>Component</th>
            <th style='text-align:left; padding:0.5rem; color:#60a5fa;'>Weight</th>
            <th style='text-align:left; padding:0.5rem; color:#60a5fa;'>What it measures</th>
        </tr>
        <tr style='border-bottom:1px solid #334155;'>
            <td style='padding:0.5rem; color:#e2e8f0;'>Hiring Decline</td>
            <td style='padding:0.5rem; color:#e2e8f0;'>40%</td>
            <td style='padding:0.5rem; color:#cbd5e1;'>% drop in job postings vs 7 days prior for this role × city</td>
        </tr>
        <tr style='border-bottom:1px solid #334155;'>
            <td style='padding:0.5rem; color:#e2e8f0;'>AI Mention Rate</td>
            <td style='padding:0.5rem; color:#e2e8f0;'>40%</td>
            <td style='padding:0.5rem; color:#cbd5e1;'>% of JDs in this role × city mentioning AI tools (ChatGPT, LLM, automation, RPA etc.)</td>
        </tr>
        <tr>
            <td style='padding:0.5rem; color:#e2e8f0;'>Replacement Signal</td>
            <td style='padding:0.5rem; color:#e2e8f0;'>20%</td>
            <td style='padding:0.5rem; color:#cbd5e1;'>% of JDs using words like "automate", "AI will", "bot replaces"</td>
        </tr>
        </table>

        <p style='color:#f1f5f9; font-weight:600; margin:1rem 0 0.5rem 0;'>Risk Levels:</p>
        <ul style='list-style:none; padding:0; margin:0.5rem 0;'>
            <li style='padding:0.3rem 0; color:#ef4444;'>🔴 Critical: 75–100</li>
            <li style='padding:0.3rem 0; color:#f97316;'>🟠 High: 50–74</li>
            <li style='padding:0.3rem 0; color:#eab308;'>🟡 Medium: 25–49</li>
            <li style='padding:0.3rem 0; color:#22c55e;'>🟢 Low: 0–24</li>
        </ul>

        <p style='color:#94a3b8; font-size:0.8rem; margin-top:1rem;'><strong>Data Sources:</strong> Naukri · LinkedIn India · Updated every 30 minutes</p>
        </div>
        """, unsafe_allow_html=True)

    # ── Bar chart: avg score by category ─────────────────────────────────────
    st.markdown("<div class='section-header'>Average Risk Score by Job Category</div>",
                unsafe_allow_html=True)

    avg_scores = vuln_df.groupby("job_category")["score"].mean().sort_values(ascending=False).reset_index()
    avg_scores.columns = ["Category", "Avg Score"]
    # Wrap category names
    avg_scores["Category_Display"] = avg_scores["Category"].apply(lambda x: '<br>'.join([x[i:i+15] for i in range(0, len(x), 15)]))
    avg_scores["Color"] = avg_scores["Avg Score"].apply(
        lambda s: "#ef4444" if s >= 75 else "#f97316" if s >= 50 else "#eab308" if s >= 25 else "#22c55e"
    )

    fig2 = go.Figure(go.Bar(
        x=avg_scores["Category_Display"],
        y=avg_scores["Avg Score"],
        marker_color=avg_scores["Color"],
        hoverinfo='skip'
    ))
    fig2.add_hline(y=75, line_dash="dot", line_color="#ef4444", annotation_text="Critical threshold",
                   annotation_font_color="#ef4444")
    fig2.add_hline(y=50, line_dash="dot", line_color="#f97316", annotation_text="High threshold",
                   annotation_font_color="#f97316")
    fig2.update_layout(
        height=420,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(30,41,59,0.4)",
        font=dict(family="DM Sans", color="#e2e8f0", size=10),
        margin=dict(l=60, r=40, t=40, b=180),
        xaxis=dict(
            gridcolor="rgba(71,85,105,0.3)",
            linecolor="#475569",
            tickfont=dict(color="#cbd5e1", size=8),
            automargin=True
        ),
        yaxis=dict(
            gridcolor="rgba(71,85,105,0.3)",
            linecolor="#475569",
            tickfont=dict(color="#cbd5e1", size=11),
            automargin=True,
            range=[0, 105]
        ),
        hovermode=False
    )
    fig2.update_traces(marker_line_width=0)
    st.plotly_chart(fig2, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# COMPUTE VULNERABILITY LIVE (if DB table is empty)
# ─────────────────────────────────────────────────────────────────────────────

def compute_vulnerability_live(df):
    """
    Compute vulnerability scores directly from job dataframe.
    Used when the pipeline hasn't run the vulnerability step yet.
    """
    AI_KEYWORDS_LOWER = [
        "chatgpt", "gpt", "llm", "generative ai", "copilot", "ai tools",
        "automation", "rpa", "artificial intelligence", "openai", "machine learning"
    ]

    CATEGORIES = {
        "BPO Voice":          ["bpo", "voice process", "call centre", "call center"],
        "Data Entry":         ["data entry", "data operator"],
        "Customer Support":   ["customer support", "customer service"],
        "IT Support":         ["it support", "technical support", "helpdesk"],
        "Software Developer": ["software developer", "software engineer"],
        "Data Analyst":       ["data analyst", "business analyst"],
        "Content Writer":     ["content writer", "copywriter"],
        "Digital Marketing":  ["digital marketing", "seo"],
        "Accountant":         ["accountant", "accounts executive"],
        "HR Executive":       ["hr executive", "human resource", "recruiter"],
        "Sales Executive":    ["sales executive", "business development"],
        "Logistics":          ["logistics", "supply chain", "warehouse"],
    }

    records = []
    cities = df["city"].value_counts().head(15).index.tolist()

    for category, keywords in CATEGORIES.items():
        for city in cities:
            city_jobs = df[df["city"] == city]
            cat_jobs = city_jobs[
                city_jobs["title"].str.lower().apply(
                    lambda t: any(kw in t for kw in keywords)
                )
            ]
            if len(cat_jobs) < 1:
                continue

            total = len(cat_jobs)
            ai_count = len(cat_jobs[cat_jobs["ai_tool_mentions"] > 0])
            ai_rate = (ai_count / total * 100) if total else 0

            # Hiring decline: compare this city's overall trend
            city_total = len(city_jobs)
            all_total = len(df[df["city"] != city]) / max(len(df["city"].unique()) - 1, 1)
            hiring_decline = max(0, min(100, 50 - ((total / max(city_total, 1)) * 100 - 10)))

            ai_score = min(100, ai_rate * 2.5)
            score = round(0.4 * hiring_decline + 0.4 * ai_score + 0.2 * (ai_score * 0.5), 1)

            risk = ("Critical" if score >= 75 else
                    "High"     if score >= 50 else
                    "Medium"   if score >= 25 else "Low")

            records.append({
                "job_category": category,
                "city": city,
                "score": score,
                "risk_level": risk,
                "hiring_trend_pct": 0,
                "ai_mention_rate": round(ai_rate, 1),
                "replacement_ratio": 0,
            })

    return pd.DataFrame(records)


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    # Load data
    with st.spinner("Loading data..."):
        df = load_jobs()
        vuln_df = load_vulnerability()
        courses_df = load_courses()

    # Sidebar filters
    selected_cities, selected_sectors, days = render_sidebar(df)

    # Header + top metrics
    render_header(df)

    # Main tabs
    tab_a, tab_b, tab_c = st.tabs([
        "📈  Tab A — Hiring Trends",
        "🔬  Tab B — Skills Intelligence",
        "⚠️  Tab C — AI Vulnerability Index",
    ])

    with tab_a:
        render_tab_a(df, selected_cities, selected_sectors, days)

    with tab_b:
        render_tab_b(df, courses_df, selected_cities, selected_sectors, days)

    with tab_c:
        render_tab_c(df, vuln_df)


if __name__ == "__main__":
    main()
