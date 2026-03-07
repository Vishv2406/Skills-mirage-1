"""
pipeline/run_pipeline.py
========================
Master pipeline runner for Skills Mirage.
Orchestrates all scrapers, runs on schedule, keeps data fresh.

Usage:
    # Run once immediately
    python pipeline/run_pipeline.py --run-once

    # Run on a schedule (refreshes every 30 min during demo)
    python pipeline/run_pipeline.py --schedule

    # Run only specific step
    python pipeline/run_pipeline.py --step naukri
    python pipeline/run_pipeline.py --step linkedin
    python pipeline/run_pipeline.py --step courses
    python pipeline/run_pipeline.py --step vulnerability
"""

import os
import sys
import time
import argparse
import schedule
from datetime import datetime
from loguru import logger
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

load_dotenv()

# ─── Configure logger ────────────────────────────────────────────────────────
logger.add(
    "logs/pipeline_{time:YYYY-MM-DD}.log",
    rotation="1 day",
    retention="7 days",
    level="INFO"
)

os.makedirs("logs", exist_ok=True)


# ─────────────────────────────────────────────────────────────────────────────
# INDIVIDUAL PIPELINE STEPS
# ─────────────────────────────────────────────────────────────────────────────

def step_setup_db():
    """Step 0: Ensure all database tables exist."""
    logger.info("📦 Step 0: Setting up database...")
    try:
        from db.schema import create_all_tables
        create_all_tables()
        logger.success("  ✅ Database ready")
    except Exception as e:
        logger.error(f"  ❌ DB setup failed: {e}")
        raise


def step_scrape_naukri():
    """Step 1: Scrape Naukri job listings."""
    logger.info("🔍 Step 1: Scraping Naukri...")
    start = datetime.utcnow()
    
    try:
        from scrapers.naukri_scraper import scrape_naukri_apify, save_jobs_to_db, save_jobs_to_json
        
        max_per_city = int(os.getenv("MAX_JOBS_PER_RUN", 100))
        jobs = scrape_naukri_apify(max_results_per_city=max_per_city)
        
        if jobs:
            save_jobs_to_json(jobs)
            added = save_jobs_to_db(jobs)
            
            duration = (datetime.utcnow() - start).seconds
            logger.success(f"  ✅ Naukri: {len(jobs)} scraped, {added} new | {duration}s")
            return len(jobs)
        else:
            logger.warning("  ⚠️  No Naukri jobs scraped (check Apify token)")
            return 0
            
    except Exception as e:
        logger.error(f"  ❌ Naukri step failed: {e}")
        return 0


def step_scrape_linkedin():
    """Step 2: Scrape LinkedIn job listings."""
    logger.info("🔍 Step 2: Scraping LinkedIn...")
    start = datetime.utcnow()
    
    try:
        from scrapers.linkedin_scraper import scrape_linkedin_apify, save_jobs_to_db, save_jobs_to_json
        
        jobs = scrape_linkedin_apify(max_per_search=50)
        
        if jobs:
            save_jobs_to_json(jobs)
            added = save_jobs_to_db(jobs)
            duration = (datetime.utcnow() - start).seconds
            logger.success(f"  ✅ LinkedIn: {len(jobs)} scraped, {added} new | {duration}s")
            return len(jobs)
        else:
            logger.warning("  ⚠️  No LinkedIn jobs (check Apify token)")
            return 0
            
    except Exception as e:
        logger.error(f"  ❌ LinkedIn step failed: {e}")
        return 0


def step_scrape_courses():
    """Step 3: Scrape NPTEL + SWAYAM courses (run once, not every cycle)."""
    logger.info("📚 Step 3: Scraping courses...")
    
    try:
        from scrapers.courses_scraper import (
            scrape_nptel_courses, scrape_swayam_courses,
            save_courses_to_db, save_courses_to_json
        )
        
        nptel = scrape_nptel_courses(max_pages=5)
        swayam = scrape_swayam_courses(max_pages=5)
        
        if nptel:
            save_courses_to_json(nptel, "nptel")
            save_courses_to_db(nptel)
            
        if swayam:
            save_courses_to_json(swayam, "swayam")
            save_courses_to_db(swayam)
        
        total = len(nptel) + len(swayam)
        logger.success(f"  ✅ Courses: {len(nptel)} NPTEL + {len(swayam)} SWAYAM = {total} total")
        return total
        
    except Exception as e:
        logger.error(f"  ❌ Courses step failed: {e}")
        return 0


def step_compute_vulnerability_index():
    """
    Step 4: Compute AI Vulnerability Index for each job category × city.
    
    Formula:
    score = (0.4 × hiring_decline_score) + (0.4 × ai_mention_score) + (0.2 × replacement_score)
    
    Each component is normalized to 0–100.
    """
    logger.info("🧮 Step 4: Computing Vulnerability Index...")
    
    try:
        from db.schema import get_session, JobListing, VulnerabilityIndex, SkillDemandSnapshot
        import json
        from sqlalchemy import func, text
        from datetime import timedelta
        
        session = get_session()
        
        # Define job categories and their keywords
        CATEGORIES = {
            "BPO Voice": ["bpo", "voice process", "call centre", "call center"],
            "Data Entry": ["data entry", "data operator"],
            "Customer Support": ["customer support", "customer service", "customer care"],
            "IT Support": ["it support", "technical support", "helpdesk"],
            "Software Developer": ["software developer", "software engineer", "programmer"],
            "Data Analyst": ["data analyst", "business analyst", "data scientist"],
            "Content Writer": ["content writer", "copywriter", "content creator"],
            "Digital Marketing": ["digital marketing", "seo", "social media marketing"],
            "Accountant": ["accountant", "accounts executive", "finance executive"],
            "HR Executive": ["hr executive", "human resource", "recruiter"],
            "Sales Executive": ["sales executive", "business development", "bdm"],
            "Logistics": ["logistics", "supply chain", "warehouse", "delivery"],
        }
        
        CITIES = [
            "Mumbai", "Delhi", "Bangalore", "Hyderabad", "Chennai",
            "Pune", "Kolkata", "Ahmedabad", "Jaipur", "Indore",
            "Nagpur", "Surat", "Lucknow", "Bhopal", "Patna",
            "Coimbatore", "Vadodara", "Kochi", "Chandigarh", "Visakhapatnam"
        ]
        
        now = datetime.utcnow()
        records_added = 0
        
        for category, keywords in CATEGORIES.items():
            for city in CITIES:
                
                # Count jobs in last 30 days
                recent_jobs = session.query(JobListing).filter(
                    JobListing.city == city,
                    JobListing.scraped_at >= now - timedelta(days=30),
                    JobListing.is_active == True
                ).all()
                
                # Filter to this category
                category_jobs = [
                    j for j in recent_jobs 
                    if any(kw in (j.title or "").lower() for kw in keywords)
                ]
                
                if len(category_jobs) < 2:
                    continue  # Not enough data for this combo
                
                # ── SIGNAL 1: Hiring decline (last 7d vs 7d before that) ──
                week1_jobs = [j for j in category_jobs 
                              if j.scraped_at >= now - timedelta(days=7)]
                week2_jobs = [j for j in category_jobs 
                              if now - timedelta(days=14) <= j.scraped_at < now - timedelta(days=7)]
                
                if week2_jobs:
                    hiring_change_pct = ((len(week1_jobs) - len(week2_jobs)) / len(week2_jobs)) * 100
                else:
                    hiring_change_pct = 0
                
                # Convert to 0-100 decline score (more negative = higher score)
                hiring_decline_score = max(0, min(100, 50 - hiring_change_pct))
                
                # ── SIGNAL 2: AI tool mention rate ──
                total = len(category_jobs)
                ai_mentions = sum(1 for j in category_jobs if (j.ai_tool_mentions or 0) > 0)
                ai_mention_rate = (ai_mentions / total * 100) if total else 0
                ai_mention_score = min(100, ai_mention_rate * 2)  # normalize
                
                # ── SIGNAL 3: Replacement ratio ──
                # Proxy: count how many JDs explicitly say "AI will assist" or "automation"
                automation_jobs = sum(
                    1 for j in category_jobs 
                    if j.description and any(
                        kw in j.description.lower() 
                        for kw in ["automate", "replace", "ai will", "bot", "automation tool"]
                    )
                )
                replacement_ratio = (automation_jobs / total) if total else 0
                replacement_score = min(100, replacement_ratio * 200)
                
                # ── FINAL SCORE ──
                score = (0.4 * hiring_decline_score + 
                         0.4 * ai_mention_score + 
                         0.2 * replacement_score)
                score = round(score, 1)
                
                risk_level = (
                    "Critical" if score >= 75 else
                    "High"     if score >= 50 else
                    "Medium"   if score >= 25 else
                    "Low"
                )
                
                methodology = {
                    "total_jobs_analyzed": total,
                    "week1_count": len(week1_jobs),
                    "week2_count": len(week2_jobs),
                    "hiring_change_pct": round(hiring_change_pct, 1),
                    "ai_mention_rate_pct": round(ai_mention_rate, 1),
                    "replacement_ratio": round(replacement_ratio, 3),
                    "component_scores": {
                        "hiring_decline": round(hiring_decline_score, 1),
                        "ai_mention": round(ai_mention_score, 1),
                        "replacement": round(replacement_score, 1),
                    },
                    "weights": {"hiring_decline": 0.4, "ai_mention": 0.4, "replacement": 0.2},
                    "computed_at": now.isoformat(),
                }
                
                vuln = VulnerabilityIndex(
                    job_category=category,
                    city=city,
                    score=score,
                    risk_level=risk_level,
                    hiring_trend_pct=round(hiring_change_pct, 1),
                    ai_mention_rate=round(ai_mention_rate, 1),
                    replacement_ratio=round(replacement_ratio, 3),
                    score_methodology=methodology,
                    computed_at=now,
                )
                session.add(vuln)
                records_added += 1
        
        session.commit()
        session.close()
        logger.success(f"  ✅ Vulnerability Index: {records_added} category×city scores computed")
        return records_added
        
    except Exception as e:
        logger.error(f"  ❌ Vulnerability index failed: {e}")
        import traceback
        traceback.print_exc()
        return 0


def step_compute_skill_snapshots():
    """Step 5: Aggregate skill demand into daily snapshots."""
    logger.info("📊 Step 5: Computing skill snapshots...")
    
    try:
        from db.schema import get_session, JobListing, SkillDemandSnapshot
        from collections import Counter
        from datetime import timedelta
        import json
        
        session = get_session()
        now = datetime.utcnow()
        
        # Get all jobs from last 30 days
        recent_jobs = session.query(JobListing).filter(
            JobListing.scraped_at >= now - timedelta(days=30),
            JobListing.is_active == True
        ).all()
        
        # Count skills by city
        city_skill_counts = {}
        for job in recent_jobs:
            city = job.city or "Unknown"
            skills = job.skills_parsed or []
            if isinstance(skills, str):
                import json as _json
                try:
                    skills = _json.loads(skills)
                except:
                    skills = []
            
            for skill in skills:
                skill = skill.lower().strip()
                if len(skill) < 2:
                    continue
                key = (skill, city)
                city_skill_counts[key] = city_skill_counts.get(key, 0) + 1
        
        # Save snapshots
        added = 0
        for (skill, city), count in city_skill_counts.items():
            snap = SkillDemandSnapshot(
                skill_name=skill,
                city=city,
                sector="All",
                count=count,
                snapshot_date=now,
            )
            session.add(snap)
            added += 1
        
        session.commit()
        session.close()
        logger.success(f"  ✅ Skill snapshots: {added} skill×city records saved")
        return added
        
    except Exception as e:
        logger.error(f"  ❌ Skill snapshots failed: {e}")
        return 0


# ─────────────────────────────────────────────────────────────────────────────
# FULL PIPELINE
# ─────────────────────────────────────────────────────────────────────────────

def run_full_pipeline(include_courses=False):
    """
    Run the complete data pipeline.
    
    include_courses: Only scrape courses on first run (they don't change often)
    """
    start = datetime.utcnow()
    print("\n" + "="*60)
    print(f"  🚀 Pipeline started at {start.strftime('%H:%M:%S')}")
    print("="*60)
    
    results = {}
    
    # Step 0: DB setup
    step_setup_db()
    
    # Step 1: Naukri
    results["naukri"] = step_scrape_naukri()
    
    # Step 2: LinkedIn
    results["linkedin"] = step_scrape_linkedin()
    
    # Step 3: Courses (only on first run or if explicitly requested)
    if include_courses:
        results["courses"] = step_scrape_courses()
    
    # Step 4: Vulnerability Index (computed from scraped data)
    results["vulnerability_index"] = step_compute_vulnerability_index()
    
    # Step 5: Skill demand snapshots
    results["skill_snapshots"] = step_compute_skill_snapshots()
    
    duration = (datetime.utcnow() - start).seconds
    
    print("\n" + "="*60)
    print(f"  ✅ Pipeline complete in {duration}s")
    print(f"  📊 Results: {results}")
    print("="*60 + "\n")
    
    return results


def run_scheduled_pipeline():
    """Wrapper for scheduled runs (no course scraping)."""
    logger.info(f"⏰ Scheduled pipeline run at {datetime.now().strftime('%H:%M:%S')}")
    run_full_pipeline(include_courses=False)


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Skills Mirage Pipeline Runner")
    parser.add_argument("--run-once", action="store_true", help="Run pipeline once and exit")
    parser.add_argument("--schedule", action="store_true", help="Run on schedule continuously")
    parser.add_argument("--step", choices=["db", "naukri", "linkedin", "courses", "vulnerability", "skills"],
                        help="Run only one step")
    parser.add_argument("--include-courses", action="store_true", help="Include course scraping")
    parser.add_argument("--interval", type=int, default=30, help="Schedule interval in minutes (default: 30)")
    args = parser.parse_args()

    if args.step:
        step_map = {
            "db": step_setup_db,
            "naukri": step_scrape_naukri,
            "linkedin": step_scrape_linkedin,
            "courses": step_scrape_courses,
            "vulnerability": step_compute_vulnerability_index,
            "skills": step_compute_skill_snapshots,
        }
        step_map[args.step]()

    elif args.run_once:
        run_full_pipeline(include_courses=args.include_courses)

    elif args.schedule:
        interval = args.interval
        print(f"\n⏰ Starting scheduler — pipeline runs every {interval} minutes")
        print("   Press Ctrl+C to stop\n")
        
        # Run immediately on start
        run_full_pipeline(include_courses=True)  # Include courses on first run
        
        # Then schedule
        schedule.every(interval).minutes.do(run_scheduled_pipeline)
        
        while True:
            schedule.run_pending()
            time.sleep(60)

    else:
        # Default: run once
        run_full_pipeline(include_courses=True)