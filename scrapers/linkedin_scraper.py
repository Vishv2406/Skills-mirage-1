"""
scrapers/linkedin_scraper.py
=============================
Scrapes LinkedIn India job listings via Apify.

LinkedIn is heavily protected — direct scraping gets blocked immediately.
Apify's LinkedIn Jobs Scraper handles this reliably.

Usage:
    python scrapers/linkedin_scraper.py
    python scrapers/linkedin_scraper.py --city Bangalore --keyword "data analyst"
"""

import os
import re
import time
import json
import hashlib
import argparse
from datetime import datetime
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

try:
    from apify_client import ApifyClient
    APIFY_AVAILABLE = True
except ImportError:
    APIFY_AVAILABLE = False

AI_KEYWORDS = [
    "chatgpt", "gpt-4", "llm", "generative ai", "copilot", "ai tools",
    "machine learning", "automation", "rpa", "artificial intelligence",
    "openai", "bard", "claude", "nlp", "deep learning", "ai-powered"
]

CITIES = [
    "Mumbai", "Delhi", "Bangalore", "Hyderabad", "Chennai",
    "Pune", "Kolkata", "Ahmedabad", "Jaipur", "Indore",
    "Nagpur", "Surat", "Lucknow", "Bhopal", "Patna",
    "Coimbatore", "Vadodara", "Kochi", "Chandigarh", "Visakhapatnam"
]

# LinkedIn seniority levels to track
SENIORITY_LEVELS = ["Entry level", "Mid-Senior level", "Associate", "Director"]


def scrape_linkedin_apify(cities=None, keywords=None, max_per_search=50):
    """
    Uses Apify LinkedIn Jobs Scraper.
    
    Actor: 'bebity/linkedin-jobs-scraper' (verify on apify.com/store)
    Free tier gives ~$5 credits — enough for ~1000-2000 listings.
    
    HOW TO SET UP:
    1. Sign up at apify.com (free)
    2. Go to apify.com/store → search "LinkedIn Jobs"
    3. Pick the most popular/recent actor
    4. Note the actor ID (format: "username/actor-name")
    5. Add your API token to .env as APIFY_API_TOKEN
    """
    if not APIFY_AVAILABLE:
        logger.error("Run: pip install apify-client")
        return []

    api_token = os.getenv("APIFY_API_TOKEN")
    if not api_token or api_token == "your_apify_token_here":
        logger.error("Set APIFY_API_TOKEN in .env")
        return []

    client = ApifyClient(api_token)
    cities = cities or CITIES[:10]  # Start with 10 cities to save Apify credits
    keywords = keywords or [
        "BPO", "customer support", "data analyst", "software developer",
        "digital marketing", "content writer", "HR executive"
    ]

    # LinkedIn actor ID — verify latest on apify.com/store
    ACTOR_ID = "bebity/linkedin-jobs-scraper"

    all_jobs = []

    for city in cities:
        for keyword in keywords:
            logger.info(f"🔍 LinkedIn: '{keyword}' in {city}")

            run_input = {
                "title": keyword,
                "location": f"{city}, India",
                "rows": max_per_search,
                "publishedAt": "r604800",   # Last 7 days
            }

            try:
                run = client.actor(ACTOR_ID).call(run_input=run_input)
                items = list(client.dataset(run["defaultDatasetId"]).iterate_items())

                for item in items:
                    job = normalize_linkedin_record(item, city, keyword)
                    if job:
                        all_jobs.append(job)

                logger.success(f"  ✅ {len(items)} jobs | {keyword} in {city}")
                time.sleep(2)

            except Exception as e:
                logger.error(f"  ❌ {keyword} in {city}: {e}")

    logger.info(f"\n📊 Total LinkedIn jobs: {len(all_jobs)}")
    return all_jobs


def normalize_linkedin_record(item, city, keyword):
    """Normalize a raw LinkedIn Apify record."""
    try:
        description = item.get("description", "") or ""
        ai_count = sum(1 for kw in AI_KEYWORDS if kw.lower() in description.lower())

        # Skills from LinkedIn
        skills = item.get("skills", []) or []
        if isinstance(skills, str):
            skills = [s.strip() for s in skills.split(",")]

        title = item.get("title", "Unknown")
        company = item.get("company", {})
        company_name = company.get("name", "Unknown") if isinstance(company, dict) else str(company)

        ext_id = hashlib.md5(f"li_{title}_{company_name}_{city}_{item.get('id','')}".encode()).hexdigest()

        return {
            "source": "linkedin",
            "external_id": ext_id,
            "title": title,
            "company": company_name,
            "city": city,
            "state": "",
            "sector": categorize_sector(title),
            "experience_min": None,
            "experience_max": None,
            "salary_min": None,
            "salary_max": None,
            "skills_raw": ", ".join(skills),
            "skills_parsed": skills,
            "description": description[:5000],
            "ai_tool_mentions": ai_count,
            "posted_date": parse_date(item.get("postedAt", "")),
            "scraped_at": datetime.utcnow(),
            "is_active": True,
        }
    except Exception as e:
        logger.warning(f"Normalize error: {e}")
        return None


def save_jobs_to_json(jobs, filepath="data/raw/linkedin_jobs_scraped.json"):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w") as f:
        json.dump(jobs, f, default=str, indent=2)
    logger.success(f"💾 Saved {len(jobs)} LinkedIn jobs to {filepath}")


def save_jobs_to_db(jobs):
    """Save to database."""
    try:
        import sys
        sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
        from db.schema import JobListing, get_session
        session = get_session()
        added = 0
        for job_data in jobs:
            existing = session.query(JobListing).filter_by(external_id=job_data["external_id"]).first()
            if not existing:
                session.add(JobListing(**job_data))
                added += 1
        session.commit()
        session.close()
        logger.success(f"✅ DB: {added} new LinkedIn jobs added")
        return added
    except Exception as e:
        logger.error(f"DB error: {e}")
        return 0


# ── Helpers ──────────────────────────────────────────────────────────────────

def categorize_sector(title):
    title_lower = title.lower()
    sector_map = {
        "BPO / Customer Support": ["bpo", "call centre", "customer support", "voice process"],
        "IT / Software": ["software", "developer", "engineer", "devops", "cloud"],
        "Data / Analytics": ["data analyst", "data scientist", "business analyst"],
        "Digital Marketing": ["digital marketing", "seo", "content writer"],
        "Finance / Accounts": ["accountant", "finance", "ca ", "audit"],
        "HR / Admin": ["hr ", "human resource", "recruiter", "admin"],
        "Sales / Business Dev": ["sales", "business development", "bdm"],
    }
    for sector, keywords in sector_map.items():
        if any(kw in title_lower for kw in keywords):
            return sector
    return "Other"


def parse_date(date_str):
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(str(date_str)[:19])
    except:
        return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LinkedIn Scraper for Skills Mirage")
    parser.add_argument("--city", default=None)
    parser.add_argument("--keyword", default=None)
    parser.add_argument("--max", type=int, default=50)
    args = parser.parse_args()

    cities = [args.city] if args.city else None
    keywords = [args.keyword] if args.keyword else None

    print("\n" + "="*60)
    print("  Skills Mirage — LinkedIn Scraper")
    print("="*60)

    jobs = scrape_linkedin_apify(cities=cities, keywords=keywords, max_per_search=args.max)

    if jobs:
        save_jobs_to_json(jobs)
        save_jobs_to_db(jobs)
        print(f"\n✅ Done! {len(jobs)} LinkedIn jobs saved.")
    else:
        print("\n⚠️  No jobs scraped.")