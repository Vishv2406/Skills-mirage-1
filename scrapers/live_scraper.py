"""
scrapers/live_scraper.py
=========================
Step 5 — Live Apify Scraping for Naukri + LinkedIn India.

This is what makes the demo LIVE — no static CSVs.

HOW APIFY WORKS:
  1. You sign up at apify.com (free $5 credits)
  2. Apify has pre-built "actors" (scrapers) for Naukri and LinkedIn
  3. You call them via API — they handle JS rendering, CAPTCHAs, proxies
  4. Results come back as clean JSON

ACTORS USED:
  - Naukri:   "bebity/naukri-jobs-scraper"  (verify on apify.com/store)
  - LinkedIn: "bebity/linkedin-jobs-scraper" (verify on apify.com/store)

HOW TO FIND CORRECT ACTOR IDs:
  1. Go to https://apify.com/store
  2. Search "naukri jobs"
  3. Click the most popular result
  4. Copy the actor ID from the URL: apify.com/ACTOR_ID
  5. Same for LinkedIn

Usage:
    # Run once
    python scrapers/live_scraper.py

    # Keep running every 30 min (for demo)
    python scrapers/live_scraper.py --schedule

    # Test with just 1 city
    python scrapers/live_scraper.py --test
"""

import os
import re
import sys
import time
import json
import hashlib
import argparse
import schedule
from datetime import datetime, timedelta
from dotenv import load_dotenv
from loguru import logger

load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

try:
    from apify_client import ApifyClient
    APIFY_AVAILABLE = True
except ImportError:
    APIFY_AVAILABLE = False
    logger.error("Run: pip install apify-client")

# ─── Config ───────────────────────────────────────────────────────────────────

APIFY_TOKEN = os.getenv("APIFY_API_TOKEN", "")

# 20 cities — Tier 1, 2, and 3
ALL_CITIES = [
    "Mumbai", "Delhi", "Bangalore", "Hyderabad", "Chennai",
    "Pune", "Kolkata", "Ahmedabad", "Jaipur", "Indore",
    "Nagpur", "Surat", "Lucknow", "Bhopal", "Patna",
    "Coimbatore", "Vadodara", "Kochi", "Chandigarh", "Visakhapatnam"
]

# Job categories to track (for vulnerability index)
JOB_KEYWORDS = [
    "BPO", "customer support", "data analyst", "software developer",
    "digital marketing", "data entry", "content writer", "HR executive",
    "accountant", "sales executive", "logistics", "IT support",
]

# AI keywords to count in JDs
AI_KEYWORDS = [
    "chatgpt", "gpt", "llm", "generative ai", "copilot", "ai tools",
    "machine learning", "automation", "rpa", "artificial intelligence",
    "openai", "bard", "nlp", "deep learning", "ai-powered", "automate",
]


# ─────────────────────────────────────────────────────────────────────────────
# STEP 1: FIND YOUR APIFY ACTOR IDs
# ─────────────────────────────────────────────────────────────────────────────

def find_actor_ids():
    """
    Search Apify store for the right actor IDs.
    Run this first to find which actors are available.
    """
    if not APIFY_AVAILABLE:
        print("Install apify-client: pip install apify-client")
        return

    if not APIFY_TOKEN:
        print("Add APIFY_API_TOKEN to your .env file")
        return

    client = ApifyClient(APIFY_TOKEN)

    print("\n" + "="*60)
    print("  Searching Apify Store for job scrapers...")
    print("="*60)

    # Search for actors
    searches = ["naukri", "linkedin jobs india"]
    for query in searches:
        try:
            actors = client.actors().list(search=query, limit=5)
            print(f"\n🔍 Results for '{query}':")
            for actor in actors.items:
                print(f"   ID: {actor.get('username')}/{actor.get('name')}")
                print(f"   Title: {actor.get('title')}")
                print(f"   Runs: {actor.get('stats', {}).get('totalRuns', 0)}")
                print()
        except Exception as e:
            print(f"   Search failed: {e}")

    print("\n📌 Copy the actor ID with most runs and paste into ACTOR_IDS below")


# ─────────────────────────────────────────────────────────────────────────────
# ACTOR IDs — Update these after running find_actor_ids()
# ─────────────────────────────────────────────────────────────────────────────

ACTOR_IDS = {
    # Go to apify.com/store → search "naukri" → copy actor ID
    "naukri":   os.getenv("APIFY_NAUKRI_ACTOR", "bebity/naukri-jobs-scraper"),
    # Go to apify.com/store → search "linkedin jobs" → copy actor ID
    "linkedin": os.getenv("APIFY_LINKEDIN_ACTOR", "bebity/linkedin-jobs-scraper"),
}


# ─────────────────────────────────────────────────────────────────────────────
# NAUKRI LIVE SCRAPER
# ─────────────────────────────────────────────────────────────────────────────

def scrape_naukri_live(cities=None, keywords=None, max_per_run=50):
    """
    Scrape Naukri live using Apify.
    
    Args:
        cities: list of cities (default: all 20)
        keywords: job keywords to search
        max_per_run: max listings per city+keyword combo
    
    Returns:
        list of normalized job dicts
    """
    if not APIFY_AVAILABLE or not APIFY_TOKEN:
        logger.error("Apify not configured. Set APIFY_API_TOKEN in .env")
        return []

    client = ApifyClient(APIFY_TOKEN)
    cities = cities or ALL_CITIES[:5]  # Start with 5 cities to save credits
    keywords = keywords or JOB_KEYWORDS[:5]

    all_jobs = []
    actor_id = ACTOR_IDS["naukri"]

    logger.info(f"🚀 Naukri live scrape | {len(cities)} cities × {len(keywords)} keywords")

    for city in cities:
        for keyword in keywords:
            logger.info(f"  Scraping: '{keyword}' in {city}")

            # easyapi/naukri-jobs-scraper input format
            run_input = {
                "keyword":  keyword,
                "location": city,
                "maxItems": max_per_run,
            }

            try:
                run = client.actor(actor_id).call(
                    run_input=run_input,
                    timeout_secs=120,  # 2 min timeout per run
                )

                items = list(
                    client.dataset(run["defaultDatasetId"]).iterate_items()
                )

                for item in items:
                    job = normalize_naukri_item(item, city, keyword)
                    if job:
                        all_jobs.append(job)

                logger.success(f"    ✅ {len(items)} jobs | {keyword} in {city}")
                time.sleep(2)  # Be polite

            except Exception as e:
                logger.error(f"    ❌ Failed: {keyword} in {city}: {e}")
                # Don't stop — continue with next city/keyword
                continue

    logger.success(f"\n📊 Naukri total: {len(all_jobs)} live jobs scraped")
    return all_jobs


def normalize_naukri_item(item: dict, city: str, keyword: str) -> dict:
    """
    Normalize a raw Naukri Apify item into our DB schema.
    Field names vary by actor — we handle all common variants.
    """
    try:
        # Title — different actors use different field names
        title = (item.get("jobTitle") or item.get("title") or
                 item.get("job_title") or item.get("designation") or "Unknown")

        # Company
        company = (item.get("companyName") or item.get("company") or
                   item.get("company_name") or "Unknown")

        # Description
        description = (item.get("jobDescription") or item.get("description") or
                       item.get("job_description") or "")

        # Skills
        skills_raw = (item.get("skills") or item.get("keySkills") or
                      item.get("key_skills") or "")
        if isinstance(skills_raw, list):
            skills_list = skills_raw
            skills_raw = ", ".join(skills_raw)
        else:
            skills_list = [s.strip() for s in re.split(r"[,;|]", str(skills_raw)) if s.strip()]

        # AI keyword count
        desc_lower = str(description).lower()
        ai_count = sum(1 for kw in AI_KEYWORDS if kw in desc_lower)

        # Experience
        exp_str = (item.get("experience") or item.get("experienceText") or "")
        exp_min, exp_max = parse_experience(str(exp_str))

        # Salary
        sal_str = (item.get("salary") or item.get("salaryText") or
                   item.get("compensation") or "")
        sal_min, sal_max = parse_salary(str(sal_str))

        # Posted date
        posted = (item.get("postedDate") or item.get("posted_date") or
                  item.get("createdAt") or "")

        # Stable unique ID
        ext_id = hashlib.md5(
            f"naukri_live_{title}_{company}_{city}_{item.get('jobId', item.get('id', ''))}".encode()
        ).hexdigest()

        return {
            "source": "naukri_live",
            "external_id": ext_id,
            "title": str(title)[:300],
            "company": str(company)[:300],
            "city": city,
            "state": "",
            "sector": categorize_sector(str(title)),
            "experience_min": exp_min,
            "experience_max": exp_max,
            "salary_min": sal_min,
            "salary_max": sal_max,
            "skills_raw": str(skills_raw)[:1000],
            "skills_parsed": skills_list[:20],
            "description": str(description)[:5000],
            "ai_tool_mentions": ai_count,
            "posted_date": parse_date(str(posted)),
            "scraped_at": datetime.utcnow(),
            "is_active": True,
        }
    except Exception as e:
        logger.warning(f"Normalize error: {e}")
        return None


# ─────────────────────────────────────────────────────────────────────────────
# LINKEDIN LIVE SCRAPER
# ─────────────────────────────────────────────────────────────────────────────

def scrape_linkedin_live(cities=None, keywords=None, max_per_run=30):
    """
    Scrape LinkedIn India live using Apify.
    LinkedIn is heavily JS-protected — NEVER try direct scraping.
    Apify handles all the auth and JS rendering.
    """
    if not APIFY_AVAILABLE or not APIFY_TOKEN:
        logger.error("Apify not configured")
        return []

    client = ApifyClient(APIFY_TOKEN)
    cities = cities or ALL_CITIES[:5]
    keywords = keywords or ["BPO", "data analyst", "software developer", "digital marketing"]

    all_jobs = []
    actor_id = ACTOR_IDS["linkedin"]

    logger.info(f"🚀 LinkedIn live scrape | {len(cities)} cities × {len(keywords)} keywords")

    for city in cities:
        for keyword in keywords:
            logger.info(f"  Scraping LinkedIn: '{keyword}' in {city}")

            run_input = {
                # Common LinkedIn actor fields:
                "searchKeywords": keyword,
                "location": f"{city}, India",
                "maxResults": max_per_run,
                "publishedAt": "r604800",  # Last 7 days

                # Some actors use:
                # "title": keyword,
                # "rows": max_per_run,
            }

            try:
                run = client.actor(actor_id).call(
                    run_input=run_input,
                    timeout_secs=120,
                )
                items = list(
                    client.dataset(run["defaultDatasetId"]).iterate_items()
                )

                for item in items:
                    job = normalize_linkedin_item(item, city, keyword)
                    if job:
                        all_jobs.append(job)

                logger.success(f"    ✅ {len(items)} jobs | {keyword} in {city}")
                time.sleep(2)

            except Exception as e:
                logger.error(f"    ❌ Failed: {keyword} in {city}: {e}")
                continue

    logger.success(f"\n📊 LinkedIn total: {len(all_jobs)} live jobs scraped")
    return all_jobs


def normalize_linkedin_item(item: dict, city: str, keyword: str) -> dict:
    """Normalize LinkedIn Apify item."""
    try:
        title = (item.get("title") or item.get("jobTitle") or "Unknown")

        company = item.get("company", {})
        if isinstance(company, dict):
            company = company.get("name", "Unknown")
        company = str(company) or "Unknown"

        description = item.get("description", "") or ""
        ai_count = sum(1 for kw in AI_KEYWORDS if kw in str(description).lower())

        skills = item.get("skills", []) or []
        if isinstance(skills, str):
            skills = [s.strip() for s in skills.split(",")]

        ext_id = hashlib.md5(
            f"li_live_{title}_{company}_{city}_{item.get('id', '')}".encode()
        ).hexdigest()

        return {
            "source": "linkedin_live",
            "external_id": ext_id,
            "title": str(title)[:300],
            "company": str(company)[:300],
            "city": city,
            "state": "",
            "sector": categorize_sector(str(title)),
            "experience_min": None,
            "experience_max": None,
            "salary_min": None,
            "salary_max": None,
            "skills_raw": ", ".join(skills),
            "skills_parsed": skills[:20],
            "description": str(description)[:5000],
            "ai_tool_mentions": ai_count,
            "posted_date": parse_date(str(item.get("postedAt", ""))),
            "scraped_at": datetime.utcnow(),
            "is_active": True,
        }
    except Exception as e:
        logger.warning(f"LinkedIn normalize error: {e}")
        return None


# ─────────────────────────────────────────────────────────────────────────────
# SAVE TO DATABASE
# ─────────────────────────────────────────────────────────────────────────────

def save_to_db(jobs: list, source: str = "") -> int:
    """Save live scraped jobs to database. Returns count of new jobs added."""
    try:
        from db.schema import get_session, JobListing, ScrapeLog
        session = get_session()
        added = 0
        skipped = 0

        for job in jobs:
            existing = session.query(JobListing).filter_by(
                external_id=job["external_id"]
            ).first()
            if existing:
                skipped += 1
                continue
            session.add(JobListing(**job))
            added += 1

        # Log this scrape run
        log = ScrapeLog(
            source=source,
            started_at=datetime.utcnow(),
            finished_at=datetime.utcnow(),
            records_added=added,
            status="success",
        )
        session.add(log)
        session.commit()
        session.close()

        logger.success(f"✅ DB: {added} new jobs added, {skipped} duplicates skipped")
        return added

    except Exception as e:
        logger.error(f"DB save error: {e}")
        return 0


def save_to_json(jobs: list, filename: str):
    """Backup to JSON."""
    os.makedirs("data/raw", exist_ok=True)
    path = f"data/raw/{filename}_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    with open(path, "w") as f:
        json.dump(jobs, f, default=str, indent=2)
    logger.info(f"💾 Saved to {path}")


# ─────────────────────────────────────────────────────────────────────────────
# TRIGGER LAYER 2 RECOMPUTE (connects to Step 4)
# ─────────────────────────────────────────────────────────────────────────────

def trigger_layer2_update():
    """
    After new jobs are scraped, recompute:
    1. Skill demand snapshots
    2. Vulnerability index scores
    
    This is the L1 → L2 live connection.
    Any worker who reloads their score will get updated numbers.
    """
    logger.info("🔄 Triggering Layer 2 recompute...")
    try:
        sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
        from pipeline.run_pipeline import (
            step_compute_skill_snapshots,
            step_compute_vulnerability_index,
        )
        step_compute_skill_snapshots()
        step_compute_vulnerability_index()
        logger.success("✅ Layer 2 scores updated from new L1 data")
    except Exception as e:
        logger.error(f"Layer 2 update failed: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# FULL LIVE PIPELINE RUN
# ─────────────────────────────────────────────────────────────────────────────

def run_live_scrape(cities=None, test_mode=False):
    """
    Run one full live scraping cycle:
    1. Scrape Naukri
    2. Scrape LinkedIn
    3. Save to DB
    4. Trigger Layer 2 recompute
    """
    start = datetime.utcnow()
    cities = cities or (ALL_CITIES[:3] if test_mode else ALL_CITIES)
    mode = "TEST" if test_mode else "FULL"

    print("\n" + "="*60)
    print(f"  🚀 Live Scrape Started [{mode}] — {start.strftime('%H:%M:%S')}")
    print(f"  Cities: {len(cities)} | Apify Token: {'✅' if APIFY_TOKEN else '❌'}")
    print("="*60)

    total_added = 0

    # ── Naukri ────────────────────────────────────────────────────────────────
    logger.info("\n📥 Scraping Naukri...")
    naukri_jobs = scrape_naukri_live(
        cities=cities,
        keywords=JOB_KEYWORDS[:4] if test_mode else JOB_KEYWORDS,
        max_per_run=20 if test_mode else 50,
    )
    if naukri_jobs:
        save_to_json(naukri_jobs, "naukri_live")
        total_added += save_to_db(naukri_jobs, "naukri_live")

    # ── LinkedIn ──────────────────────────────────────────────────────────────
    logger.info("\n📥 Scraping LinkedIn...")
    linkedin_jobs = scrape_linkedin_live(
        cities=cities,
        keywords=JOB_KEYWORDS[:3] if test_mode else JOB_KEYWORDS[:6],
        max_per_run=15 if test_mode else 30,
    )
    if linkedin_jobs:
        save_to_json(linkedin_jobs, "linkedin_live")
        total_added += save_to_db(linkedin_jobs, "linkedin_live")

    # ── Trigger Layer 2 recompute ─────────────────────────────────────────────
    if total_added > 0:
        trigger_layer2_update()
    else:
        logger.warning("No new jobs added — skipping Layer 2 recompute")

    duration = (datetime.utcnow() - start).seconds
    print("\n" + "="*60)
    print(f"  ✅ Live scrape complete in {duration}s")
    print(f"  📊 New jobs added: {total_added}")
    print("="*60 + "\n")

    return total_added


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def parse_experience(exp_str: str):
    nums = re.findall(r"\d+", exp_str)
    if len(nums) >= 2: return int(nums[0]), int(nums[1])
    if len(nums) == 1: return int(nums[0]), int(nums[0])
    return None, None


def parse_salary(sal_str: str):
    nums = re.findall(r"[\d.]+", sal_str.replace(",", ""))
    if len(nums) >= 2: return float(nums[0]), float(nums[1])
    if len(nums) == 1: return float(nums[0]), float(nums[0])
    return None, None


def parse_date(date_str: str):
    if not date_str or date_str == "None":
        return None
    formats = ["%Y-%m-%d", "%d/%m/%Y", "%B %d, %Y", "%d %b %Y", "%Y-%m-%dT%H:%M:%S"]
    for fmt in formats:
        try:
            return datetime.strptime(date_str[:19], fmt)
        except:
            continue
    return None


def categorize_sector(title: str) -> str:
    t = title.lower()
    if any(k in t for k in ["bpo", "call centre", "voice", "customer support"]): return "BPO / Customer Support"
    if any(k in t for k in ["software", "developer", "engineer", "devops"]):     return "IT / Software"
    if any(k in t for k in ["data analyst", "data scientist", "business analyst"]): return "Data / Analytics"
    if any(k in t for k in ["digital marketing", "seo", "content writer"]):      return "Digital Marketing"
    if any(k in t for k in ["accountant", "finance", "ca ", "audit"]):           return "Finance / Accounts"
    if any(k in t for k in ["hr ", "human resource", "recruiter"]):              return "HR / Admin"
    if any(k in t for k in ["sales", "business development"]):                   return "Sales / Business Dev"
    if any(k in t for k in ["logistics", "supply chain", "warehouse"]):          return "Manufacturing / Operations"
    return "Other"


# ─────────────────────────────────────────────────────────────────────────────
# SCHEDULER — keep running during demo
# ─────────────────────────────────────────────────────────────────────────────

def run_scheduled():
    """Run on schedule — call this during the demo to keep data fresh."""
    interval = int(os.getenv("SCRAPE_INTERVAL_MINUTES", 30))

    print(f"\n⏰ Scheduler started — runs every {interval} minutes")
    print("   Ctrl+C to stop\n")

    # Run immediately on start
    run_live_scrape()

    # Schedule
    schedule.every(interval).minutes.do(run_live_scrape)

    while True:
        schedule.run_pending()
        time.sleep(60)


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Skills Mirage — Live Scraper")
    parser.add_argument("--find-actors", action="store_true",
                        help="Search Apify store for actor IDs")
    parser.add_argument("--test", action="store_true",
                        help="Test mode: 3 cities, 4 keywords, 20 jobs max")
    parser.add_argument("--schedule", action="store_true",
                        help="Run on schedule (every 30 min)")
    parser.add_argument("--naukri-only", action="store_true",
                        help="Only scrape Naukri")
    parser.add_argument("--linkedin-only", action="store_true",
                        help="Only scrape LinkedIn")
    args = parser.parse_args()

    if args.find_actors:
        find_actor_ids()

    elif args.schedule:
        run_scheduled()

    elif args.naukri_only:
        jobs = scrape_naukri_live(
            cities=ALL_CITIES[:3] if args.test else ALL_CITIES,
            max_per_run=20 if args.test else 50,
        )
        if jobs:
            save_to_json(jobs, "naukri_live")
            save_to_db(jobs, "naukri_live")

    elif args.linkedin_only:
        jobs = scrape_linkedin_live(
            cities=ALL_CITIES[:3] if args.test else ALL_CITIES,
            max_per_run=15 if args.test else 30,
        )
        if jobs:
            save_to_json(jobs, "linkedin_live")
            save_to_db(jobs, "linkedin_live")

    else:
        run_live_scrape(test_mode=args.test)