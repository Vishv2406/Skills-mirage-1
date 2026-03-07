# 🎯 Skills Mirage

**AI-Powered Workforce Intelligence Platform for India**

A comprehensive system that analyzes job market trends, assesses AI displacement risk, and generates personalized reskilling paths for Indian workers.

Built for HACKaMINeD 2026

---

## 🌟 Key Features

### 📊 Market Intelligence Dashboard
- **Live Job Data**: Real-time scraping from Naukri & LinkedIn using Apify actors
- **Hiring Trends**: Track job volume across 20+ Indian cities and 12+ sectors
- **Skills Intelligence**: Identify in-demand skills and training gaps
- **AI Vulnerability Index**: Risk scores for job categories by city with transparent methodology

### 🎯 Career Intelligence Engine
- **NLP Profile Analysis**: Extract skills, aspirations, and experience from worker descriptions
- **Personal Risk Score**: AI displacement risk (0-100) based on live market data
- **Reskilling Paths**: Week-by-week learning plans from free NPTEL & SWAYAM courses
- **AI Chatbot**: Career guidance in English & Hindi (powered by Gemini AI)

### ⚙️ System Administration
- **Automated Pipeline**: Scheduled data collection and processing
- **Admin Panel**: Monitor system health, manage scrapers, view logs
- **REST API**: FastAPI backend for programmatic access
- **Responsive Design**: Modern, professional, mobile-friendly interface

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- pip or conda
- Apify account (free $5 credits) - https://apify.com
- Google Gemini API key (optional, for enhanced chatbot) - https://ai.google.dev

### Installation

1. **Clone and navigate to the project**
```bash
git clone <your-repo-url>
cd Skills-Mirage
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure environment variables**

Create a `.env` file in the project root:

```bash
# Apify Configuration (Required)
APIFY_API_TOKEN=your_apify_token_here

# Google Gemini AI (Optional - for enhanced chatbot)
GOOGLE_API_KEY=your_gemini_api_key_here

# Database
DATABASE_URL=sqlite:///./skills_mirage.db

# Scraping Configuration
MAX_JOBS_PER_RUN=100
SCRAPE_INTERVAL_MINUTES=30
```

**Get your API keys:**
- **Apify**: https://apify.com → Sign up → Settings → Integrations → API Token
- **Gemini**: https://ai.google.dev → Get API Key

4. **Initialize the database**
```bash
python db/schema.py
```

5. **Run the data pipeline** (first time - takes 5-10 minutes)
```bash
python pipeline/run_pipeline.py
```

This will:
- Scrape job listings from Naukri & LinkedIn
- Collect training courses from NPTEL & SWAYAM
- Compute vulnerability scores
- Generate skill demand snapshots

6. **Start the application**
```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`

---

## 📁 Project Structure

```
Skills-Mirage/
├── app.py                      # Main unified application entry point
├── admin_panel.py              # System administration interface
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables (create this)
├── verify_setup.py             # Setup verification script
│
├── scrapers/                   # Data collection modules
│   ├── naukri_scraper.py      # Naukri job scraper (Apify)
│   ├── linkedin_scraper.py    # LinkedIn job scraper (Apify)
│   ├── courses_scraper.py     # NPTEL & SWAYAM course scraper
│   └── live_scraper.py        # Live scraping orchestrator
│
├── layer2/                     # Worker intelligence engine
│   ├── nlp_engine.py          # NLP profile extraction & analysis
│   ├── risk_engine.py         # AI risk scoring algorithm
│   └── worker_app.py          # Worker-facing interface
│
├── dashboard/                  # Market intelligence dashboard
│   └── app.py                 # Layer 1 dashboard (hiring trends, skills, vulnerability)
│
├── api/                        # FastAPI backend
│   └── main.py                # REST API endpoints
│
├── db/                         # Database layer
│   └── schema.py              # SQLAlchemy models & database setup
│
├── pipeline/                   # Data processing pipeline
│   └── run_pipeline.py        # Pipeline orchestrator
│
├── static/                     # Static assets
│   └── custom.css             # Custom styling
│
├── data/                       # Data storage
│   ├── raw/                   # Scraped data (JSON backups)
│   └── processed/             # Processed datasets
│
└── logs/                       # Application logs
```

---

## 🎮 Usage Guide

### 1. Home Page
Navigate between three main sections:
- **📊 Market Intelligence**: Explore job market trends and AI vulnerability
- **🎯 Career Intelligence**: Get personalized risk assessment and reskilling path
- **⚙️ System Admin**: Manage data pipeline and monitor system health

### 2. Market Intelligence Dashboard

Access via: Home → "Open Dashboard" button

**Tab: Hiring Trends**
- View job volume by city and sector
- Identify hiring hotspots across India
- Track sector-wise growth patterns

**Tab: Skills Intelligence**
- Top in-demand skills in the market
- Skill gap analysis (market demand vs training supply)
- Skills breakdown by city and sector

**Tab: AI Vulnerability Index**
- Risk scores for different job categories
- Transparent methodology with score breakdown
- City-wise vulnerability heatmap

### 3. Career Intelligence

Access via: Home → "Analyze My Profile" button

**Step 1: Input Your Profile**
- Current job title
- City (select from 20+ Indian cities)
- Years of experience
- **Work write-up** (100-200 words - most important!)
  - Describe your day-to-day work
  - Tools/software you use
  - What you're good at
  - What you want to move toward

**Step 2: View Your Analysis Tab**
- **Personal AI Risk Score** (0-100)
  - Score breakdown by component
  - Risk signals and factors
  - Peer comparison
- **Reskilling Path**
  - Week-by-week learning plan
  - Free courses from NPTEL & SWAYAM
  - Skills gap analysis
  - Target role and salary expectations

**Step 3: AI Career Advisor Tab**
- Ask questions in English or Hindi
- Get personalized career advice
- Quick questions available:
  - "Why is my risk score high?"
  - "What safer jobs can I move to?"
  - "How long will reskilling take?"
- Explore alternative career paths
- Get course recommendations

### 4. System Admin

Access via: Home → "Admin Panel" button

**Pipeline Control:**
- Run full pipeline or individual steps
- Monitor execution status
- View pipeline logs

**Database Status:**
- View record counts for all tables
- Check latest scrape timestamp
- Inspect data quality

**Configuration:**
- Review environment variables
- Check API key status
- Access setup instructions

**Logs:**
- View recent application logs
- Download log files for debugging
- Clear old logs

---

## 🔧 Advanced Usage

### Running the API Server

The FastAPI backend provides REST endpoints for programmatic access:

```bash
uvicorn api.main:app --reload --port 8000
```

API documentation available at: `http://localhost:8000/docs`

**Key Endpoints:**
- `POST /api/analyze` - Full worker analysis (risk + reskilling)
- `GET /api/jobs/live` - Live job counts by city/sector
- `GET /api/vulnerability` - Vulnerability scores
- `POST /api/chat` - AI chatbot interaction

### Scheduled Pipeline Runs

For continuous data updates, run the pipeline on a schedule:

```bash
# Run every 30 minutes
python pipeline/run_pipeline.py --schedule --interval 30
```

Or use system cron/Task Scheduler for production deployments.

### Custom Scraper Configuration

Edit `.env` to use different Apify actors:

```bash
APIFY_NAUKRI_ACTOR=your-custom-actor-id
APIFY_LINKEDIN_ACTOR=your-custom-actor-id
```

Browse available actors at: https://apify.com/store

---

## 📊 Data Sources

### Job Market Data
- **Naukri.com**: India's largest job portal (20M+ jobs)
- **LinkedIn India**: Professional networking platform
- **Apify Actors**: Handles JavaScript rendering, CAPTCHAs, proxies, rate limiting

### Training Data
- **NPTEL**: IIT/IISc online courses (2000+ courses)
- **SWAYAM**: Government of India MOOC platform (1000+ courses)
- **PMKVY**: Skill India training programs

### Government Data
- **PLFS**: Periodic Labour Force Survey (employment statistics)
- **data.gov.in**: Open government datasets

---

## 🛠️ Troubleshooting

### "No data available" in dashboards
**Solution**: Run the pipeline first to populate the database
```bash
python pipeline/run_pipeline.py
```
Wait 5-10 minutes for completion, then refresh the dashboard.

### Apify scraping fails
**Check:**
1. Valid API token in `.env` file
2. Sufficient credits in Apify account (check dashboard)
3. Correct actor IDs in configuration

**Test connection:**
```bash
python verify_setup.py
```

### Chatbot not responding or giving basic responses
**Check:**
1. Google Gemini API key in `.env` (optional but recommended)
2. API key has sufficient quota
3. Check logs for error messages

**Note**: Chatbot works without Gemini but responses are more basic.

### Database errors
**Reset database:**
```bash
rm skills_mirage.db
python db/schema.py
python pipeline/run_pipeline.py
```

### Port already in use
**Change port:**
```bash
streamlit run app.py --server.port 8502
```

### Import errors
**Reinstall dependencies:**
```bash
pip install -r requirements.txt --force-reinstall
```

---

## 🎯 For Judges / Evaluators

### Key Innovation Points

1. **Live Data Integration**: Real Apify scraping, not static CSVs
2. **NLP-Driven Analysis**: Extracts skills from free-text worker descriptions
3. **Reactive Risk Scoring**: Scores update with live market data
4. **Bilingual Support**: English + Hindi chatbot with AI enhancement
5. **Transparent Methodology**: All scores show calculation breakdown
6. **Personalized Reskilling**: Week-by-week plans based on individual profiles
7. **Professional UI**: Modern, responsive design with dark theme

### Quick Testing Guide

**Test 1: Live Data Flow (5 minutes)**
```bash
# Run pipeline
python pipeline/run_pipeline.py

# Start app
streamlit run app.py

# Navigate: Home → Market Intelligence → View hiring trends
```

**Test 2: Worker Analysis (3 minutes)**
```bash
streamlit run app.py
# Navigate: Home → Career Intelligence
# Input example:
#   Job: "BPO Voice Process Executive"
#   City: "Pune"
#   Experience: 5 years
#   Write-up: "I handle inbound calls for US insurance client, 
#              manage team of 12 agents, track AHT and CSAT in Excel,
#              good at resolving escalations, want to move to data analytics"
# Observe: Risk score, reskilling path, chatbot responses
```

**Test 3: Chatbot Interaction (2 minutes)**
```bash
# After completing Test 2, switch to "AI Career Advisor" tab
# Try questions:
#   - "Why is my risk score high?"
#   - "Show me paths that take less than 3 months"
#   - "मुझे कहाँ से शुरू करना चाहिए?" (Hindi)
```

**Test 4: API Integration (2 minutes)**
```bash
# Start API server
uvicorn api.main:app --port 8000

# Test endpoint (in another terminal)
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "job_title": "BPO Executive",
    "city": "Pune",
    "years_experience": 5,
    "write_up": "Handle customer calls, use Excel, manage team"
  }'
```

### Evaluation Criteria Coverage

✅ **Data Integration**: Apify + NPTEL + SWAYAM + PLFS  
✅ **Real-time Processing**: Live scraping with 30-min refresh capability  
✅ **NLP Analysis**: Skill extraction from free-text descriptions  
✅ **Risk Assessment**: Multi-factor scoring algorithm (hiring decline + AI mentions + replacement potential)  
✅ **Reskilling Paths**: Personalized, week-by-week learning plans  
✅ **User Interface**: Modern, responsive, accessible design  
✅ **Bilingual Support**: English + Hindi with AI enhancement  
✅ **API Access**: RESTful endpoints with OpenAPI documentation  
✅ **Transparency**: All calculations shown with methodology  
✅ **Reproducibility**: One-command setup and execution  

---

## 🔐 Security Notes

- Never commit `.env` file to version control
- Keep API keys secure and rotate regularly
- Use environment variables for all sensitive configuration
- Review Apify actor permissions before use

---

## 📝 License

This project was built for HACKaMINeD 2026.

---

## 🙏 Acknowledgments

- **Apify**: For providing robust web scraping infrastructure
- **Google**: For Gemini AI API
- **NPTEL & SWAYAM**: For open access to quality educational content
- **Government of India**: For PLFS and PMKVY open data
- **Streamlit**: For rapid application development framework

---

## 📧 Support

For issues or questions:
1. Check the Troubleshooting section above
2. Review logs in `logs/` directory
3. Run `python verify_setup.py` to check configuration
4. Check API documentation at `http://localhost:8000/docs`

---

**Built with ❤️ for India's workforce**
