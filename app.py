"""
app.py
======
Main unified application entry point for Skills Mirage.
Provides a modern, responsive interface with proper navigation.

Run: streamlit run app.py
"""

import streamlit as st
import sys
import os
import importlib

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

# Clear module cache for hot reloading of changes
if 'layer2.worker_app' in sys.modules:
    del sys.modules['layer2.worker_app']
if 'dashboard.app' in sys.modules:
    del sys.modules['dashboard.app']
if 'admin_panel' in sys.modules:
    del sys.modules['admin_panel']

# Page config
st.set_page_config(
    page_title="Skills Mirage - AI Workforce Intelligence",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for modern, responsive design
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');
    
    /* Global Styles */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        color: #f1f5f9;
    }
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        color: #f1f5f9 !important;
    }
    
    /* Streamlit Elements */
    .stMarkdown, .stMarkdown p, .stMarkdown div {
        color: #e2e8f0 !important;
    }
    
    h1, h2, h3, h4, h5, h6 {
        font-family: 'JetBrains Mono', monospace;
        color: #f8fafc !important;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
    }
    
    [data-testid="stSidebar"] .stMarkdown {
        color: #e2e8f0 !important;
    }
    
    /* Hide default header */
    header[data-testid="stHeader"] {
        background: transparent !important;
        display: none !important;
    }
    
    /* Hide top toolbar */
    .stApp > header {
        background-color: transparent !important;
        display: none !important;
    }
    
    /* Remove white background from top area */
    [data-testid="stToolbar"] {
        display: none !important;
    }
    
    /* Fix any remaining white backgrounds */
    .stApp > div:first-child {
        background-color: transparent !important;
    }
    
    /* Main container - better spacing */
    .main .block-container {
        padding: 2rem 3rem;
        max-width: 1400px;
        margin: 0 auto;
    }
    
    /* Better typography */
    p {
        line-height: 1.7;
        color: #cbd5e1;
    }
    
    /* Section spacing */
    .element-container {
        margin-bottom: 1rem;
    }
    
    /* Hero Section */
    .hero-section {
        text-align: center;
        padding: 3rem 0 2rem;
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.15), rgba(139, 92, 246, 0.15));
        border-radius: 20px;
        margin-bottom: 2rem;
        border: 1px solid rgba(59, 130, 246, 0.3);
        box-shadow: 0 4px 20px rgba(59, 130, 246, 0.1);
    }
    
    .hero-title {
        font-size: 3rem;
        font-weight: 700;
        background: linear-gradient(135deg, #60a5fa, #c084fc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.5rem;
    }
    
    .hero-subtitle {
        font-size: 1.2rem;
        color: #cbd5e1;
        margin-top: 0.5rem;
        font-weight: 500;
    }
    
    /* Navigation Cards - more professional */
    .nav-card {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.6) 0%, rgba(51, 65, 85, 0.4) 100%);
        border: 1px solid rgba(71, 85, 105, 0.5);
        border-radius: 12px;
        padding: 2rem;
        text-align: center;
        transition: all 0.3s ease;
        cursor: pointer;
        height: 100%;
        position: relative;
        overflow: hidden;
        backdrop-filter: blur(10px);
    }
    
    .nav-card:hover {
        transform: translateY(-4px);
        border-color: rgba(96, 165, 250, 0.6);
        box-shadow: 0 8px 32px rgba(59, 130, 246, 0.25);
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.8) 0%, rgba(51, 65, 85, 0.6) 100%);
    }
    
    .nav-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, #60a5fa, #c084fc);
        opacity: 0;
        transition: opacity 0.3s ease;
    }
    
    .nav-card:hover::before {
        opacity: 1;
    }
    
    .nav-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
        filter: drop-shadow(0 0 10px rgba(96, 165, 250, 0.5));
    }
    
    .nav-title {
        font-size: 1.3rem;
        font-weight: 600;
        color: #f1f5f9;
        margin-bottom: 0.5rem;
    }
    
    .nav-desc {
        font-size: 0.95rem;
        color: #cbd5e1;
        line-height: 1.6;
    }
    
    /* Feature Cards - cleaner design */
    .feature-card {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.5), rgba(51, 65, 85, 0.3));
        border: 1px solid rgba(71, 85, 105, 0.4);
        border-radius: 10px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        transition: all 0.3s ease;
        backdrop-filter: blur(5px);
    }
    
    .feature-card:hover {
        border-color: rgba(96, 165, 250, 0.5);
        box-shadow: 0 4px 16px rgba(59, 130, 246, 0.15);
        transform: translateX(4px);
    }
    
    .feature-icon {
        font-size: 1.8rem;
        margin-bottom: 0.5rem;
        filter: drop-shadow(0 2px 4px rgba(59, 130, 246, 0.3));
    }
    
    .feature-title {
        font-size: 1.05rem;
        font-weight: 600;
        color: #60a5fa;
        margin-bottom: 0.5rem;
    }
    
    .feature-text {
        font-size: 0.9rem;
        color: #cbd5e1;
        line-height: 1.6;
    }
    
    /* Buttons - professional style */
    .stButton > button {
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.15), rgba(139, 92, 246, 0.15));
        color: #93c5fd;
        border: 1px solid rgba(59, 130, 246, 0.4);
        border-radius: 8px;
        padding: 0.7rem 2rem;
        font-weight: 600;
        font-size: 0.95rem;
        transition: all 0.2s ease;
        width: 100%;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.25), rgba(139, 92, 246, 0.25));
        border-color: #60a5fa;
        color: #60a5fa;
        transform: translateY(-2px);
        box-shadow: 0 4px 16px rgba(59, 130, 246, 0.3);
    }
    
    /* Primary buttons */
    button[kind="primary"] {
        background: linear-gradient(135deg, #3b82f6, #8b5cf6) !important;
        color: white !important;
        border: none !important;
    }
    
    button[kind="primary"]:hover {
        background: linear-gradient(135deg, #2563eb, #7c3aed) !important;
        box-shadow: 0 6px 20px rgba(59, 130, 246, 0.4) !important;
    }
    
    /* Stats Grid */
    .stats-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        margin: 2rem 0;
    }
    
    .stat-card {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.6), rgba(51, 65, 85, 0.4));
        border: 1px solid rgba(71, 85, 105, 0.5);
        border-radius: 10px;
        padding: 1.5rem;
        text-align: center;
        transition: all 0.3s ease;
        backdrop-filter: blur(10px);
    }
    
    .stat-card:hover {
        border-color: rgba(96, 165, 250, 0.6);
        box-shadow: 0 4px 20px rgba(59, 130, 246, 0.2);
        transform: translateY(-2px);
    }
    
    .stat-value {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #60a5fa, #c084fc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-family: 'JetBrains Mono', monospace;
    }
    
    .stat-label {
        font-size: 0.8rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-top: 0.5rem;
        font-weight: 500;
    }
    
    /* Remove white backgrounds from inputs */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > div,
    .stNumberInput > div > div > input,
    .stDateInput > div > div > input,
    .stTimeInput > div > div > input {
        background-color: rgba(30, 41, 59, 0.8) !important;
        color: #e2e8f0 !important;
        border: 1px solid #475569 !important;
    }
    
    /* Remove white background from dataframes and tables */
    .stDataFrame, .stTable {
        background-color: transparent !important;
    }
    
    .stDataFrame > div, .stTable > div {
        background-color: rgba(30, 41, 59, 0.8) !important;
    }
    
    /* Fix white backgrounds in expanders */
    .streamlit-expanderHeader,
    .streamlit-expanderContent {
        background-color: rgba(30, 41, 59, 0.8) !important;
        border-color: #475569 !important;
    }
    
    /* Remove white from metric cards */
    [data-testid="stMetricValue"],
    [data-testid="stMetricLabel"] {
        background-color: transparent !important;
    }
    
    /* Fix code blocks */
    .stCodeBlock, pre, code {
        background-color: rgba(15, 23, 42, 0.9) !important;
        color: #e2e8f0 !important;
    }
    
    /* Responsive Design */
    @media (max-width: 768px) {
        .hero-title {
            font-size: 2rem;
        }
        
        .hero-subtitle {
            font-size: 1rem;
        }
        
        .main .block-container {
            padding: 1rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# Load custom CSS
try:
    with open('static/custom.css') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
except FileNotFoundError:
    pass  # Custom CSS is optional

def render_home():
    """Render the home page with navigation"""
    
    # Hero Section
    st.markdown("""
    <div class="hero-section">
        <div class="hero-title">🎯 Skills Mirage</div>
        <div class="hero-subtitle">
            AI-Powered Workforce Intelligence Platform for India
        </div>
        <p style="color: #64748b; margin-top: 1rem; font-size: 0.95rem;">
            Real-time job market analysis • AI risk assessment • Personalized reskilling paths
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Navigation Cards
    st.markdown("### 🚀 Choose Your Dashboard")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="nav-card">
            <div class="nav-icon">📊</div>
            <div class="nav-title">Market Intelligence</div>
            <div class="nav-desc">
                Explore hiring trends, skill demand, and AI vulnerability across 20+ Indian cities
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Open Dashboard →", key="market_btn"):
            st.session_state.page = "market"
            st.rerun()
    
    with col2:
        st.markdown("""
        <div class="nav-card">
            <div class="nav-icon">🎯</div>
            <div class="nav-title">Career Intelligence</div>
            <div class="nav-desc">
                Get your personal AI risk score and week-by-week reskilling roadmap
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Analyze My Profile →", key="worker_btn"):
            st.session_state.page = "worker"
            st.rerun()
    
    with col3:
        st.markdown("""
        <div class="nav-card">
            <div class="nav-icon">⚙️</div>
            <div class="nav-title">System Admin</div>
            <div class="nav-desc">
                Run data pipeline, manage scrapers, and monitor system health
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Admin Panel →", key="admin_btn"):
            st.session_state.page = "admin"
            st.rerun()
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Features Section
    st.markdown("### ✨ Platform Features")
    
    col1, col2 = st.columns(2)
    
    with col1:
        features = [
            ("🔍", "Live Data Scraping", "Real-time job data from Naukri & LinkedIn using Apify actors"),
            ("🧠", "NLP Analysis", "Extract skills, aspirations, and experience from worker profiles"),
            ("📈", "Trend Analysis", "Track hiring patterns across 20 cities and 12+ sectors"),
        ]
        
        for icon, title, desc in features:
            st.markdown(f"""
            <div class="feature-card">
                <div class="feature-icon">{icon}</div>
                <div class="feature-title">{title}</div>
                <div class="feature-text">{desc}</div>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        features = [
            ("⚠️", "AI Risk Scoring", "Personal vulnerability assessment based on live market data"),
            ("🎓", "Reskilling Paths", "Week-by-week learning plans from NPTEL & SWAYAM courses"),
            ("💬", "AI Chatbot", "Career guidance in English & Hindi powered by Claude"),
        ]
        
        for icon, title, desc in features:
            st.markdown(f"""
            <div class="feature-card">
                <div class="feature-icon">{icon}</div>
                <div class="feature-title">{title}</div>
                <div class="feature-text">{desc}</div>
            </div>
            """, unsafe_allow_html=True)
    
    # Quick Stats
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 📊 Platform Statistics")
    
    try:
        from db.schema import get_session, JobListing, TrainingCourse, VulnerabilityIndex
        session = get_session()
        
        job_count = session.query(JobListing).count()
        course_count = session.query(TrainingCourse).count()
        vuln_count = session.query(VulnerabilityIndex).count()
        cities = session.query(JobListing.city).distinct().count()
        
        session.close()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value">{job_count:,}</div>
                <div class="stat-label">Job Listings</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value">{cities}</div>
                <div class="stat-label">Cities Tracked</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value">{course_count}</div>
                <div class="stat-label">Training Courses</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value">{vuln_count}</div>
                <div class="stat-label">Risk Assessments</div>
            </div>
            """, unsafe_allow_html=True)
    
    except Exception as e:
        st.info("💡 Run the data pipeline first to see live statistics")
    
    # Footer
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align: center; padding: 2rem; color: #cbd5e1; font-size: 0.9rem;">
        <p style="color: #e2e8f0;">Built for HACKaMINeD 2026 | Powered by Apify, Claude AI, NPTEL & SWAYAM</p>
        <p style="margin-top: 0.5rem; color: #94a3b8;">
            Data sources: Naukri.com • LinkedIn India • PLFS • PMKVY
        </p>
    </div>
    """, unsafe_allow_html=True)


def main():
    # Initialize session state
    if "page" not in st.session_state:
        st.session_state.page = "home"
    
    # Sidebar navigation
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; padding: 1.5rem 0;">
            <div style="font-size: 2rem;">🎯</div>
            <div style="font-size: 1.2rem; font-weight: 700; color: #60a5fa; margin-top: 0.5rem;">
                Skills Mirage
            </div>
            <div style="font-size: 0.75rem; color: #cbd5e1; margin-top: 0.3rem;">
                Workforce Intelligence
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Navigation buttons
        if st.button("🏠 Home", width='stretch'):
            st.session_state.page = "home"
            st.rerun()
        
        if st.button("📊 Market Intelligence", width='stretch'):
            st.session_state.page = "market"
            st.rerun()
        
        if st.button("🎯 Career Intelligence", width='stretch'):
            st.session_state.page = "worker"
            st.rerun()
        
        if st.button("⚙️ System Admin", width='stretch'):
            st.session_state.page = "admin"
            st.rerun()
        
        st.markdown("---")
        
        # System status
        try:
            from db.schema import get_session, JobListing
            session = get_session()
            job_count = session.query(JobListing).count()
            session.close()
            
            st.markdown(f"""
            <div style="font-size: 0.85rem; color: #e2e8f0; padding: 0.5rem 0;">
                <p style="color: #f1f5f9;"><strong>System Status:</strong></p>
                <p style="color: #cbd5e1;">🟢 Database: Online</p>
                <p style="color: #cbd5e1;">📊 Jobs: {job_count:,}</p>
            </div>
            """, unsafe_allow_html=True)
        except:
            st.markdown("""
            <div style="font-size: 0.85rem; color: #fca5a5; padding: 0.5rem 0;">
                <p style="color: #fca5a5;">⚠️ Database not initialized</p>
                <p style="color: #fca5a5;">Run setup first</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        st.markdown("""
        <div style="font-size: 0.85rem; color: #e2e8f0; padding: 1rem 0;">
            <p style="color: #f1f5f9;"><strong>Quick Links:</strong></p>
            <p>• <a href="http://localhost:8000/docs" target="_blank" style="color: #60a5fa; text-decoration: none;">API Docs</a></p>
            <p>• <a href="https://github.com" target="_blank" style="color: #60a5fa; text-decoration: none;">Documentation</a></p>
        </div>
        """, unsafe_allow_html=True)
    
    # Route to appropriate page
    try:
        if st.session_state.page == "home":
            render_home()
        elif st.session_state.page == "market":
            # Import and run market dashboard
            import dashboard.app as market_app
            # Reload to get latest changes
            import importlib
            importlib.reload(market_app)
            market_app.main()
        elif st.session_state.page == "worker":
            # Import and run worker app
            import layer2.worker_app as worker_app
            # Reload to get latest changes
            import importlib
            importlib.reload(worker_app)
            worker_app.main()
        elif st.session_state.page == "admin":
            # Import and run admin panel
            import admin_panel
            # Reload to get latest changes
            import importlib
            importlib.reload(admin_panel)
            admin_panel.main()
    except Exception as e:
        st.error(f"❌ Error loading page: {e}")
        st.info("💡 Try running the setup first: `python verify_setup.py`")
        
        if st.button("🏠 Return to Home"):
            st.session_state.page = "home"
            st.rerun()


if __name__ == "__main__":
    main()
