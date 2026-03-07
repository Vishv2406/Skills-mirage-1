#!/bin/bash

# Skills Mirage - Startup Script
# This script sets up and starts the complete application

echo "🎯 Skills Mirage - Starting Application"
echo "========================================"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found!"
    echo "Creating .env template..."
    cat > .env << 'EOF'
# Apify Configuration
APIFY_API_TOKEN=your_apify_token_here

# AI Configuration
ANTHROPIC_API_KEY=your_anthropic_key_here

# Database
DATABASE_URL=sqlite:///./skills_mirage.db

# Scraping Configuration
MAX_JOBS_PER_RUN=100
SCRAPE_INTERVAL_MINUTES=30

# Apify Actor IDs (optional)
APIFY_NAUKRI_ACTOR=bebity/naukri-jobs-scraper
APIFY_LINKEDIN_ACTOR=bebity/linkedin-jobs-scraper
EOF
    echo "✅ Created .env template"
    echo "⚠️  Please edit .env with your API keys before continuing"
    echo ""
    exit 1
fi

# Check if database exists
if [ ! -f skills_mirage.db ]; then
    echo "📦 Setting up database..."
    python db/schema.py
    echo "✅ Database created"
    echo ""
    
    echo "📥 Running initial data collection..."
    echo "This may take 5-10 minutes..."
    python pipeline/run_pipeline.py --run-once --include-courses
    echo "✅ Initial data loaded"
    echo ""
fi

# Check if dependencies are installed
echo "📦 Checking dependencies..."
pip install -q -r requirements.txt
echo "✅ Dependencies ready"
echo ""

# Start the application
echo "🚀 Starting Skills Mirage..."
echo ""
echo "The application will open in your browser at:"
echo "http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop"
echo ""

streamlit run app.py
