"""
verify_setup.py
===============
Verify that Skills Mirage is properly set up and ready to run.
"""

import os
import sys
from pathlib import Path

def check_file(path, description):
    """Check if a file exists"""
    exists = os.path.exists(path)
    status = "✅" if exists else "❌"
    print(f"{status} {description}: {path}")
    return exists

def check_env_var(var_name):
    """Check if environment variable is set"""
    from dotenv import load_dotenv
    load_dotenv()
    
    value = os.getenv(var_name)
    is_set = value and value != f"your_{var_name.lower()}_here"
    status = "✅" if is_set else "⚠️"
    masked = "***" + value[-4:] if is_set and len(value) > 4 else "NOT SET"
    print(f"{status} {var_name}: {masked}")
    return is_set

def check_database():
    """Check database connection"""
    try:
        from db.schema import get_session, JobListing
        session = get_session()
        count = session.query(JobListing).count()
        session.close()
        print(f"✅ Database connection: OK ({count} jobs)")
        return True
    except Exception as e:
        print(f"❌ Database connection: FAILED ({e})")
        return False

def check_dependencies():
    """Check if required packages are installed"""
    required = {
        'streamlit': 'streamlit',
        'fastapi': 'fastapi',
        'sqlalchemy': 'sqlalchemy',
        'pandas': 'pandas',
        'plotly': 'plotly',
        'requests': 'requests',
        'beautifulsoup4': 'bs4',  # Import name is different
        'anthropic': 'anthropic'
    }
    
    missing = []
    for package, import_name in required.items():
        try:
            __import__(import_name)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package}")
            missing.append(package)
    
    return len(missing) == 0

def main():
    print("=" * 60)
    print("🎯 Skills Mirage - Setup Verification")
    print("=" * 60)
    print()
    
    # Check files
    print("📁 Checking Files...")
    files_ok = all([
        check_file("app.py", "Main application"),
        check_file("admin_panel.py", "Admin panel"),
        check_file("requirements.txt", "Dependencies"),
        check_file(".env", "Environment config"),
        check_file("db/schema.py", "Database schema"),
        check_file("scrapers/naukri_scraper.py", "Naukri scraper"),
        check_file("layer2/nlp_engine.py", "NLP engine"),
        check_file("layer2/risk_engine.py", "Risk engine"),
        check_file("dashboard/app.py", "Market dashboard"),
    ])
    print()
    
    # Check dependencies
    print("📦 Checking Dependencies...")
    deps_ok = check_dependencies()
    print()
    
    # Check environment variables
    print("🔑 Checking Environment Variables...")
    env_ok = all([
        check_env_var("APIFY_API_TOKEN"),
        check_env_var("ANTHROPIC_API_KEY"),
    ])
    print()
    
    # Check database
    print("💾 Checking Database...")
    db_ok = check_database()
    print()
    
    # Summary
    print("=" * 60)
    print("📊 Summary")
    print("=" * 60)
    
    all_ok = files_ok and deps_ok and db_ok
    
    if all_ok:
        print("✅ All checks passed! You're ready to go!")
        print()
        print("🚀 Start the application:")
        print("   streamlit run app.py")
        print()
        print("Or use the startup script:")
        print("   Windows: start.bat")
        print("   Linux/Mac: bash start.sh")
    else:
        print("⚠️ Some checks failed. Please fix the issues above.")
        print()
        
        if not deps_ok:
            print("📦 Install dependencies:")
            print("   pip install -r requirements.txt")
            print()
        
        if not env_ok:
            print("🔑 Set up environment variables:")
            print("   1. Edit .env file")
            print("   2. Add your API keys")
            print("   3. Get keys from:")
            print("      - Apify: https://apify.com")
            print("      - Anthropic: https://console.anthropic.com")
            print()
        
        if not db_ok:
            print("💾 Initialize database:")
            print("   python db/schema.py")
            print("   python pipeline/run_pipeline.py --run-once --include-courses")
            print()
    
    print("=" * 60)

if __name__ == "__main__":
    main()
