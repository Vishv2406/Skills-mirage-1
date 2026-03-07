"""
admin_panel.py
==============
System administration panel for Skills Mirage.
Manage scrapers, run pipeline, monitor system health.
"""

import streamlit as st
import sys
import os
from datetime import datetime
import subprocess

sys.path.insert(0, os.path.dirname(__file__))

# Load custom CSS
try:
    with open('static/custom.css') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
except FileNotFoundError:
    pass  # Custom CSS is optional

# Add header hiding CSS
st.markdown("""
<style>
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
</style>
""", unsafe_allow_html=True)

def main():
    st.markdown("## ⚙️ System Administration")
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "🚀 Pipeline Control",
        "📊 Database Status",
        "🔧 Configuration",
        "📝 Logs"
    ])
    
    # Tab 1: Pipeline Control
    with tab1:
        st.markdown("### Data Pipeline Management")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #111827, #1e293b); 
                        border: 1px solid #334155; border-radius: 12px; padding: 1.5rem;">
                <h4 style="color: #60a5fa; margin-bottom: 1rem;">🔄 Run Pipeline</h4>
                <p style="color: #94a3b8; font-size: 0.9rem;">
                    Execute the complete data collection and processing pipeline
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            include_courses = st.checkbox("Include course scraping", value=False,
                                         help="Courses don't change often, only run this occasionally")
            
            if st.button("▶️ Run Full Pipeline", width='stretch', type="primary"):
                with st.spinner("Running pipeline..."):
                    try:
                        from pipeline.run_pipeline import run_full_pipeline
                        results = run_full_pipeline(include_courses=include_courses)
                        
                        st.success("✅ Pipeline completed successfully!")
                        st.json(results)
                    except Exception as e:
                        st.error(f"❌ Pipeline failed: {e}")
        
        with col2:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #111827, #1e293b); 
                        border: 1px solid #334155; border-radius: 12px; padding: 1.5rem;">
                <h4 style="color: #60a5fa; margin-bottom: 1rem;">🎯 Individual Steps</h4>
                <p style="color: #94a3b8; font-size: 0.9rem;">
                    Run specific pipeline components
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            steps = {
                "Setup Database": "db",
                "Scrape Naukri": "naukri",
                "Scrape LinkedIn": "linkedin",
                "Scrape Courses": "courses",
                "Compute Vulnerability": "vulnerability",
                "Compute Skills": "skills"
            }
            
            for label, step in steps.items():
                if st.button(f"▶️ {label}", width='stretch', key=f"step_{step}"):
                    with st.spinner(f"Running {label}..."):
                        try:
                            from pipeline import run_pipeline
                            step_map = {
                                "db": run_pipeline.step_setup_db,
                                "naukri": run_pipeline.step_scrape_naukri,
                                "linkedin": run_pipeline.step_scrape_linkedin,
                                "courses": run_pipeline.step_scrape_courses,
                                "vulnerability": run_pipeline.step_compute_vulnerability_index,
                                "skills": run_pipeline.step_compute_skill_snapshots,
                            }
                            result = step_map[step]()
                            st.success(f"✅ {label} completed! Result: {result}")
                        except Exception as e:
                            st.error(f"❌ Failed: {e}")
        
        st.markdown("---")
        
        # Scheduler
        st.markdown("### ⏰ Automated Scheduling")
        
        st.info("""
        **To run the pipeline on a schedule:**
        
        ```bash
        python pipeline/run_pipeline.py --schedule --interval 30
        ```
        
        This will run the pipeline every 30 minutes automatically.
        """)
    
    # Tab 2: Database Status
    with tab2:
        st.markdown("### 📊 Database Statistics")
        
        try:
            from db.schema import get_session, JobListing, TrainingCourse, VulnerabilityIndex, SkillDemandSnapshot, ScrapeLog
            
            session = get_session()
            
            # Get counts
            job_count = session.query(JobListing).count()
            active_jobs = session.query(JobListing).filter(JobListing.is_active == True).count()
            course_count = session.query(TrainingCourse).count()
            vuln_count = session.query(VulnerabilityIndex).count()
            skill_count = session.query(SkillDemandSnapshot).count()
            
            # Get latest scrape
            latest_scrape = session.query(ScrapeLog).order_by(ScrapeLog.started_at.desc()).first()
            
            session.close()
            
            # Display stats
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Jobs", f"{job_count:,}", f"{active_jobs:,} active")
            
            with col2:
                st.metric("Training Courses", f"{course_count:,}")
            
            with col3:
                st.metric("Vulnerability Records", f"{vuln_count:,}")
            
            with col4:
                st.metric("Skill Snapshots", f"{skill_count:,}")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Latest scrape info
            if latest_scrape:
                st.markdown("### 🕐 Latest Scrape")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write(f"**Source:** {latest_scrape.source}")
                
                with col2:
                    st.write(f"**Status:** {latest_scrape.status}")
                
                with col3:
                    st.write(f"**Records Added:** {latest_scrape.records_added}")
                
                st.write(f"**Started:** {latest_scrape.started_at}")
                if latest_scrape.finished_at:
                    duration = (latest_scrape.finished_at - latest_scrape.started_at).seconds
                    st.write(f"**Duration:** {duration}s")
            
            # Table details
            st.markdown("---")
            st.markdown("### 📋 Table Details")
            
            import pandas as pd
            
            table_info = pd.DataFrame([
                {"Table": "job_listings", "Records": job_count, "Description": "Scraped job postings"},
                {"Table": "training_courses", "Records": course_count, "Description": "NPTEL & SWAYAM courses"},
                {"Table": "vulnerability_index", "Records": vuln_count, "Description": "AI risk scores"},
                {"Table": "skill_demand_snapshots", "Records": skill_count, "Description": "Skill demand tracking"},
            ])
            
            st.dataframe(table_info, width='stretch', hide_index=True)
            
        except Exception as e:
            st.error(f"❌ Database error: {e}")
            st.info("💡 Make sure to run the database setup first")
    
    # Tab 3: Configuration
    with tab3:
        st.markdown("### 🔧 System Configuration")
        
        st.markdown("#### Environment Variables")
        
        env_vars = {
            "APIFY_API_TOKEN": "Apify API token for scraping",
            "ANTHROPIC_API_KEY": "Claude API key for chatbot",
            "DATABASE_URL": "Database connection string",
            "MAX_JOBS_PER_RUN": "Max jobs to scrape per city",
            "SCRAPE_INTERVAL_MINUTES": "Pipeline schedule interval",
        }
        
        for var, desc in env_vars.items():
            value = os.getenv(var, "Not set")
            masked = "***" + value[-4:] if value != "Not set" and len(value) > 4 else value
            
            with st.expander(f"**{var}**"):
                st.write(f"**Description:** {desc}")
                st.code(f"{var}={masked}")
        
        st.markdown("---")
        
        st.markdown("#### .env File Template")
        
        st.code("""
# Apify Configuration
APIFY_API_TOKEN=your_apify_token_here

# AI Configuration
ANTHROPIC_API_KEY=your_anthropic_key_here

# Database
DATABASE_URL=sqlite:///./skills_mirage.db

# Scraping Configuration
MAX_JOBS_PER_RUN=100
SCRAPE_INTERVAL_MINUTES=30

# Apify Actor IDs (optional - defaults provided)
APIFY_NAUKRI_ACTOR=bebity/naukri-jobs-scraper
APIFY_LINKEDIN_ACTOR=bebity/linkedin-jobs-scraper
        """, language="bash")
        
        st.info("""
        **Setup Instructions:**
        
        1. Copy the template above to a `.env` file in the project root
        2. Get your Apify token from https://apify.com (free $5 credits)
        3. Get your Anthropic API key from https://console.anthropic.com
        4. Run `python db/schema.py` to create the database
        5. Run `python pipeline/run_pipeline.py --run-once` to populate data
        """)
    
    # Tab 4: Logs
    with tab4:
        st.markdown("### 📝 System Logs")
        
        log_dir = "logs"
        
        if os.path.exists(log_dir):
            log_files = sorted([f for f in os.listdir(log_dir) if f.endswith('.log')], reverse=True)
            
            if log_files:
                selected_log = st.selectbox("Select log file", log_files)
                
                if selected_log:
                    log_path = os.path.join(log_dir, selected_log)
                    
                    try:
                        # Try UTF-8 first, then fallback to latin-1 with error handling
                        try:
                            with open(log_path, 'r', encoding='utf-8') as f:
                                log_content = f.read()
                        except UnicodeDecodeError:
                            # Fallback to latin-1 which accepts all byte values
                            with open(log_path, 'r', encoding='latin-1', errors='replace') as f:
                                log_content = f.read()
                            st.warning("⚠️ Log file contains non-UTF-8 characters. Some characters may be replaced.")
                        
                        # Show last N lines
                        lines = log_content.split('\n')
                        num_lines = st.slider("Number of lines to show", 10, 500, 100)
                        
                        st.code('\n'.join(lines[-num_lines:]), language="log")
                        
                        # Download button
                        st.download_button(
                            "📥 Download Full Log",
                            log_content,
                            file_name=selected_log,
                            mime="text/plain",
                            type="secondary"
                        )
                    
                    except Exception as e:
                        st.error(f"Error reading log: {e}")
                        st.info("💡 Tip: Try clearing the logs and running the pipeline again to generate clean log files.")
            else:
                st.info("No log files found. Run the pipeline to generate logs.")
        else:
            st.info("Logs directory not found. It will be created when you run the pipeline.")
        
        st.markdown("---")
        
        # Clear logs
        if st.button("🗑️ Clear All Logs", type="secondary"):
            if st.checkbox("I understand this will delete all log files"):
                try:
                    import shutil
                    if os.path.exists(log_dir):
                        shutil.rmtree(log_dir)
                        os.makedirs(log_dir)
                    st.success("✅ Logs cleared")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
