@echo off
REM Skills Mirage - Startup Script for Windows

echo 🎯 Skills Mirage - Starting Application
echo ========================================
echo.

REM Check if .env exists
if not exist .env (
    echo ⚠️  .env file not found!
    echo Creating .env template...
    (
        echo # Apify Configuration
        echo APIFY_API_TOKEN=your_apify_token_here
        echo.
        echo # AI Configuration
        echo ANTHROPIC_API_KEY=your_anthropic_key_here
        echo.
        echo # Database
        echo DATABASE_URL=sqlite:///./skills_mirage.db
        echo.
        echo # Scraping Configuration
        echo MAX_JOBS_PER_RUN=100
        echo SCRAPE_INTERVAL_MINUTES=30
        echo.
        echo # Apify Actor IDs ^(optional^)
        echo APIFY_NAUKRI_ACTOR=bebity/naukri-jobs-scraper
        echo APIFY_LINKEDIN_ACTOR=bebity/linkedin-jobs-scraper
    ) > .env
    echo ✅ Created .env template
    echo ⚠️  Please edit .env with your API keys before continuing
    echo.
    pause
    exit /b 1
)

REM Check if database exists
if not exist skills_mirage.db (
    echo 📦 Setting up database...
    python db/schema.py
    echo ✅ Database created
    echo.
    
    echo 📥 Running initial data collection...
    echo This may take 5-10 minutes...
    python pipeline/run_pipeline.py --run-once --include-courses
    echo ✅ Initial data loaded
    echo.
)

REM Check if dependencies are installed
echo 📦 Checking dependencies...
pip install -q -r requirements.txt
echo ✅ Dependencies ready
echo.

REM Start the application
echo 🚀 Starting Skills Mirage...
echo.
echo The application will open in your browser at:
echo http://localhost:8501
echo.
echo Press Ctrl+C to stop
echo.

streamlit run app.py
