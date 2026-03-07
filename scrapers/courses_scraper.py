"""
scrapers/courses_scraper.py (FIXED)
=====================================
Scrapes NPTEL + SWAYAM courses using the correct API endpoints.
Falls back to a curated list if scraping fails.
"""

import os
import re
import time
import json
import argparse
import requests
from datetime import datetime
from loguru import logger

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0",
    "Accept": "application/json, text/html",
}

NPTEL_SKILL_MAP = {
    "data science": ["python", "data analysis", "statistics", "pandas", "numpy"],
    "machine learning": ["machine learning", "python", "scikit-learn", "tensorflow"],
    "artificial intelligence": ["ai", "machine learning", "deep learning"],
    "programming": ["programming", "python", "java", "c++"],
    "database": ["sql", "database", "mysql"],
    "cloud": ["aws", "azure", "cloud", "devops"],
    "digital marketing": ["digital marketing", "seo", "social media"],
    "accounting": ["accounting", "tally", "finance", "gst"],
    "communication": ["communication", "english", "soft skills"],
    "project management": ["project management", "agile", "scrum"],
    "cybersecurity": ["cybersecurity", "network security"],
    "entrepreneurship": ["entrepreneurship", "startup", "business"],
    "excel": ["excel", "spreadsheet", "data analysis"],
    "java": ["java", "programming", "backend"],
    "web development": ["html", "css", "javascript", "web development"],
}


# ─────────────────────────────────────────────────────────────────────────────
# NPTEL
# ─────────────────────────────────────────────────────────────────────────────

def scrape_nptel_courses(max_pages=5):
    logger.info("📚 Scraping NPTEL courses...")

    try:
        search_url = "https://api.nptel.ac.in/v2/courses/search/"
        params = {"query": "", "page": 1, "size": 100}
        resp = requests.get(search_url, params=params, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            courses = parse_nptel_api_response(data)
            if courses:
                logger.success(f"  ✅ NPTEL API: {len(courses)} courses")
                return courses
    except Exception as e:
        logger.warning(f"  NPTEL API failed: {e}")

    logger.warning("  Using curated NPTEL course list...")
    courses = get_nptel_curated_courses()
    logger.success(f"  ✅ NPTEL curated: {len(courses)} courses loaded")
    return courses


def parse_nptel_api_response(data):
    courses = []
    items = data.get("courses", data.get("data", data.get("results", data if isinstance(data, list) else [])))
    for item in items:
        try:
            title = item.get("courseName", item.get("title", item.get("name", "Unknown")))
            if title == "Unknown":
                continue
            courses.append({
                "source": "nptel",
                "title": title,
                "institution": item.get("nptelInstitute", item.get("institute", "IIT")),
                "url": f"https://nptel.ac.in/courses/{item.get('courseId', item.get('id', ''))}",
                "duration_weeks": extract_weeks(str(item.get("duration", "8 weeks"))),
                "hours_per_week": 5.0,
                "topics": extract_topics_from_title(title),
                "level": item.get("courseLevel", "Intermediate"),
                "is_free": True,
                "certification": True,
                "scraped_at": datetime.utcnow(),
            })
        except:
            continue
    return courses


def get_nptel_curated_courses():
    return [
        {"source": "nptel", "title": "Python for Data Science", "institution": "IIT Madras",
         "url": "https://nptel.ac.in/courses/106106212", "duration_weeks": 8, "hours_per_week": 6,
         "topics": ["python", "data analysis", "pandas", "numpy"], "level": "Beginner", "is_free": True, "certification": True, "scraped_at": datetime.utcnow()},
        {"source": "nptel", "title": "Introduction to Machine Learning", "institution": "IIT Kharagpur",
         "url": "https://nptel.ac.in/courses/106105152", "duration_weeks": 8, "hours_per_week": 6,
         "topics": ["machine learning", "python", "scikit-learn"], "level": "Intermediate", "is_free": True, "certification": True, "scraped_at": datetime.utcnow()},
        {"source": "nptel", "title": "Data Science for Engineers", "institution": "IIT Madras",
         "url": "https://nptel.ac.in/courses/106106202", "duration_weeks": 12, "hours_per_week": 5,
         "topics": ["data science", "statistics", "python", "data analysis"], "level": "Intermediate", "is_free": True, "certification": True, "scraped_at": datetime.utcnow()},
        {"source": "nptel", "title": "Deep Learning", "institution": "IIT Ropar",
         "url": "https://nptel.ac.in/courses/106107239", "duration_weeks": 12, "hours_per_week": 6,
         "topics": ["deep learning", "tensorflow", "neural networks", "ai"], "level": "Advanced", "is_free": True, "certification": True, "scraped_at": datetime.utcnow()},
        {"source": "nptel", "title": "Business Analytics and Data Mining", "institution": "IIT Roorkee",
         "url": "https://nptel.ac.in/courses/110107108", "duration_weeks": 8, "hours_per_week": 5,
         "topics": ["business analytics", "data mining", "statistics"], "level": "Intermediate", "is_free": True, "certification": True, "scraped_at": datetime.utcnow()},
        {"source": "nptel", "title": "Programming in Java", "institution": "IIT Kharagpur",
         "url": "https://nptel.ac.in/courses/106105191", "duration_weeks": 12, "hours_per_week": 6,
         "topics": ["java", "programming", "object oriented"], "level": "Beginner", "is_free": True, "certification": True, "scraped_at": datetime.utcnow()},
        {"source": "nptel", "title": "The Joy of Computing using Python", "institution": "IIT Madras",
         "url": "https://nptel.ac.in/courses/106106145", "duration_weeks": 12, "hours_per_week": 4,
         "topics": ["python", "programming", "coding"], "level": "Beginner", "is_free": True, "certification": True, "scraped_at": datetime.utcnow()},
        {"source": "nptel", "title": "Database Management System", "institution": "IIT Madras",
         "url": "https://nptel.ac.in/courses/106106093", "duration_weeks": 8, "hours_per_week": 5,
         "topics": ["sql", "database", "mysql", "rdbms"], "level": "Intermediate", "is_free": True, "certification": True, "scraped_at": datetime.utcnow()},
        {"source": "nptel", "title": "Cloud Computing", "institution": "IIT Kharagpur",
         "url": "https://nptel.ac.in/courses/106105167", "duration_weeks": 8, "hours_per_week": 5,
         "topics": ["cloud computing", "aws", "azure", "devops"], "level": "Intermediate", "is_free": True, "certification": True, "scraped_at": datetime.utcnow()},
        {"source": "nptel", "title": "Soft Skills", "institution": "IIT Kanpur",
         "url": "https://nptel.ac.in/courses/109104099", "duration_weeks": 8, "hours_per_week": 4,
         "topics": ["soft skills", "communication", "presentation"], "level": "Beginner", "is_free": True, "certification": True, "scraped_at": datetime.utcnow()},
        {"source": "nptel", "title": "Business English Communication", "institution": "IIT Bombay",
         "url": "https://nptel.ac.in/courses/109101005", "duration_weeks": 8, "hours_per_week": 4,
         "topics": ["english", "communication", "business writing", "soft skills"], "level": "Beginner", "is_free": True, "certification": True, "scraped_at": datetime.utcnow()},
        {"source": "nptel", "title": "Financial Accounting", "institution": "IIT Kharagpur",
         "url": "https://nptel.ac.in/courses/110105049", "duration_weeks": 8, "hours_per_week": 4,
         "topics": ["accounting", "finance", "tally", "balance sheet"], "level": "Beginner", "is_free": True, "certification": True, "scraped_at": datetime.utcnow()},
        {"source": "nptel", "title": "Digital Marketing", "institution": "IIT Delhi",
         "url": "https://nptel.ac.in/courses/110102028", "duration_weeks": 8, "hours_per_week": 4,
         "topics": ["digital marketing", "seo", "social media", "google ads"], "level": "Beginner", "is_free": True, "certification": True, "scraped_at": datetime.utcnow()},
        {"source": "nptel", "title": "Introduction to Artificial Intelligence", "institution": "IIT Kharagpur",
         "url": "https://nptel.ac.in/courses/106105078", "duration_weeks": 8, "hours_per_week": 5,
         "topics": ["ai", "artificial intelligence", "machine learning"], "level": "Beginner", "is_free": True, "certification": True, "scraped_at": datetime.utcnow()},
        {"source": "nptel", "title": "Natural Language Processing", "institution": "IIT Bombay",
         "url": "https://nptel.ac.in/courses/106101007", "duration_weeks": 8, "hours_per_week": 6,
         "topics": ["nlp", "natural language processing", "python", "ai"], "level": "Advanced", "is_free": True, "certification": True, "scraped_at": datetime.utcnow()},
        {"source": "nptel", "title": "Project Management", "institution": "IIT Roorkee",
         "url": "https://nptel.ac.in/courses/110107081", "duration_weeks": 8, "hours_per_week": 4,
         "topics": ["project management", "agile", "scrum", "planning"], "level": "Intermediate", "is_free": True, "certification": True, "scraped_at": datetime.utcnow()},
        {"source": "nptel", "title": "Introduction to Cybersecurity", "institution": "IIT Kanpur",
         "url": "https://nptel.ac.in/courses/106104106", "duration_weeks": 8, "hours_per_week": 5,
         "topics": ["cybersecurity", "network security", "ethical hacking"], "level": "Beginner", "is_free": True, "certification": True, "scraped_at": datetime.utcnow()},
        {"source": "nptel", "title": "Programming in C++", "institution": "IIT Kharagpur",
         "url": "https://nptel.ac.in/courses/106105151", "duration_weeks": 8, "hours_per_week": 5,
         "topics": ["c++", "programming", "data structures"], "level": "Intermediate", "is_free": True, "certification": True, "scraped_at": datetime.utcnow()},
        {"source": "nptel", "title": "Financial Management", "institution": "IIT Kharagpur",
         "url": "https://nptel.ac.in/courses/110105050", "duration_weeks": 8, "hours_per_week": 5,
         "topics": ["finance", "investment", "financial planning"], "level": "Intermediate", "is_free": True, "certification": True, "scraped_at": datetime.utcnow()},
        {"source": "nptel", "title": "Web Technologies", "institution": "IIT Kharagpur",
         "url": "https://nptel.ac.in/courses/106105084", "duration_weeks": 8, "hours_per_week": 5,
         "topics": ["html", "css", "javascript", "web development"], "level": "Beginner", "is_free": True, "certification": True, "scraped_at": datetime.utcnow()},
    ]


# ─────────────────────────────────────────────────────────────────────────────
# SWAYAM
# ─────────────────────────────────────────────────────────────────────────────

def scrape_swayam_courses(max_pages=5):
    logger.info("📚 Loading SWAYAM courses...")

    try:
        resp = requests.get("https://swayam.gov.in/api/courses", headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            courses = parse_swayam_api(data)
            if courses:
                logger.success(f"  ✅ SWAYAM API: {len(courses)} courses")
                return courses
    except Exception as e:
        logger.warning(f"  SWAYAM API failed: {e}")

    logger.warning("  Using curated SWAYAM list...")
    courses = get_swayam_curated_courses()
    logger.success(f"  ✅ SWAYAM curated: {len(courses)} courses loaded")
    return courses


def parse_swayam_api(data):
    courses = []
    items = data if isinstance(data, list) else data.get("courses", data.get("data", []))
    for item in items:
        try:
            title = item.get("name", item.get("title", "Unknown"))
            if title == "Unknown":
                continue
            courses.append({
                "source": "swayam",
                "title": title,
                "institution": item.get("ncCordinatingInstitute", "SWAYAM"),
                "url": f"https://swayam.gov.in/courses/{item.get('slug', item.get('id', ''))}",
                "duration_weeks": extract_weeks(str(item.get("duration", "8 weeks"))),
                "hours_per_week": 5.0,
                "topics": extract_topics_from_title(title),
                "level": item.get("level", "Beginner"),
                "is_free": True,
                "certification": True,
                "scraped_at": datetime.utcnow(),
            })
        except:
            continue
    return courses


def get_swayam_curated_courses():
    return [
        {"source": "swayam", "title": "Python Programming", "institution": "NPTEL",
         "url": "https://swayam.gov.in/nd1_noc20_cs47/preview", "duration_weeks": 8, "hours_per_week": 5,
         "topics": ["python", "programming", "coding"], "level": "Beginner", "is_free": True, "certification": True, "scraped_at": datetime.utcnow()},
        {"source": "swayam", "title": "Fundamentals of Artificial Intelligence", "institution": "IGNOU",
         "url": "https://swayam.gov.in/courses/ai-fundamentals", "duration_weeks": 12, "hours_per_week": 4,
         "topics": ["ai", "machine learning", "artificial intelligence"], "level": "Beginner", "is_free": True, "certification": True, "scraped_at": datetime.utcnow()},
        {"source": "swayam", "title": "Data Analytics with Python", "institution": "NPTEL",
         "url": "https://swayam.gov.in/courses/data-analytics-python", "duration_weeks": 8, "hours_per_week": 6,
         "topics": ["data analytics", "python", "pandas", "visualization"], "level": "Intermediate", "is_free": True, "certification": True, "scraped_at": datetime.utcnow()},
        {"source": "swayam", "title": "Entrepreneurship and New Venture Creation", "institution": "IIM Bangalore",
         "url": "https://swayam.gov.in/courses/entrepreneurship", "duration_weeks": 8, "hours_per_week": 4,
         "topics": ["entrepreneurship", "startup", "business"], "level": "Beginner", "is_free": True, "certification": True, "scraped_at": datetime.utcnow()},
        {"source": "swayam", "title": "Goods and Services Tax (GST)", "institution": "ICAI",
         "url": "https://swayam.gov.in/courses/gst", "duration_weeks": 4, "hours_per_week": 4,
         "topics": ["gst", "tax", "accounting", "finance", "tally"], "level": "Beginner", "is_free": True, "certification": True, "scraped_at": datetime.utcnow()},
        {"source": "swayam", "title": "Marketing Management", "institution": "IIM Kozhikode",
         "url": "https://swayam.gov.in/courses/marketing-management", "duration_weeks": 8, "hours_per_week": 4,
         "topics": ["marketing", "sales", "digital marketing", "branding"], "level": "Intermediate", "is_free": True, "certification": True, "scraped_at": datetime.utcnow()},
        {"source": "swayam", "title": "Human Resource Management", "institution": "IIM Lucknow",
         "url": "https://swayam.gov.in/courses/hrm", "duration_weeks": 8, "hours_per_week": 4,
         "topics": ["hr", "human resource", "recruitment", "talent management"], "level": "Intermediate", "is_free": True, "certification": True, "scraped_at": datetime.utcnow()},
        {"source": "swayam", "title": "Spoken English for Beginners", "institution": "IGNOU",
         "url": "https://swayam.gov.in/courses/spoken-english", "duration_weeks": 8, "hours_per_week": 3,
         "topics": ["english", "communication", "spoken english", "soft skills"], "level": "Beginner", "is_free": True, "certification": True, "scraped_at": datetime.utcnow()},
        {"source": "swayam", "title": "Digital Marketing and E-Commerce", "institution": "NPTEL",
         "url": "https://swayam.gov.in/courses/digital-marketing", "duration_weeks": 8, "hours_per_week": 4,
         "topics": ["digital marketing", "ecommerce", "seo", "social media"], "level": "Beginner", "is_free": True, "certification": True, "scraped_at": datetime.utcnow()},
        {"source": "swayam", "title": "Cyber Security and Privacy", "institution": "IIT Madras",
         "url": "https://swayam.gov.in/courses/cybersecurity", "duration_weeks": 8, "hours_per_week": 5,
         "topics": ["cybersecurity", "privacy", "network security"], "level": "Intermediate", "is_free": True, "certification": True, "scraped_at": datetime.utcnow()},
        {"source": "swayam", "title": "Customer Relationship Management", "institution": "IGNOU",
         "url": "https://swayam.gov.in/courses/crm", "duration_weeks": 6, "hours_per_week": 3,
         "topics": ["crm", "customer service", "sales", "communication"], "level": "Beginner", "is_free": True, "certification": True, "scraped_at": datetime.utcnow()},
        {"source": "swayam", "title": "Basics of Financial Literacy", "institution": "NISM",
         "url": "https://swayam.gov.in/courses/financial-literacy", "duration_weeks": 4, "hours_per_week": 3,
         "topics": ["finance", "financial literacy", "savings", "investment"], "level": "Beginner", "is_free": True, "certification": True, "scraped_at": datetime.utcnow()},
        {"source": "swayam", "title": "Logistics and Supply Chain Management", "institution": "IIT Delhi",
         "url": "https://swayam.gov.in/courses/supply-chain", "duration_weeks": 8, "hours_per_week": 4,
         "topics": ["logistics", "supply chain", "warehouse", "operations"], "level": "Intermediate", "is_free": True, "certification": True, "scraped_at": datetime.utcnow()},
        {"source": "swayam", "title": "Technical Writing", "institution": "IIT Bombay",
         "url": "https://swayam.gov.in/courses/technical-writing", "duration_weeks": 6, "hours_per_week": 3,
         "topics": ["writing", "communication", "documentation", "content"], "level": "Intermediate", "is_free": True, "certification": True, "scraped_at": datetime.utcnow()},
        {"source": "swayam", "title": "Internet of Things", "institution": "IIT Kharagpur",
         "url": "https://swayam.gov.in/nd1_noc19_cs47/preview", "duration_weeks": 8, "hours_per_week": 5,
         "topics": ["iot", "programming", "electronics", "automation"], "level": "Beginner", "is_free": True, "certification": True, "scraped_at": datetime.utcnow()},
    ]


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def extract_weeks(duration_str):
    if not duration_str:
        return 8
    duration_str = duration_str.lower()
    nums = re.findall(r"\d+", duration_str)
    if not nums:
        return 8
    n = int(nums[0])
    if "month" in duration_str:
        return n * 4
    return n


def extract_topics_from_title(title):
    title_lower = title.lower()
    topics = []
    for topic_key, skill_list in NPTEL_SKILL_MAP.items():
        if topic_key in title_lower or any(s in title_lower for s in skill_list[:2]):
            topics.extend(skill_list)
    return list(set(topics)) if topics else ["general skills"]


def save_courses_to_json(courses, source):
    filepath = f"data/raw/{source}_courses.json"
    os.makedirs("data/raw", exist_ok=True)
    with open(filepath, "w") as f:
        json.dump(courses, f, indent=2, default=str)
    logger.success(f"💾 Saved {len(courses)} {source} courses to {filepath}")


def save_courses_to_db(courses):
    try:
        import sys
        sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
        from db.schema import TrainingCourse, get_session
        session = get_session()
        added = 0
        for c in courses:
            session.add(TrainingCourse(**c))
            added += 1
        session.commit()
        session.close()
        logger.success(f"✅ DB: {added} courses saved")
    except Exception as e:
        logger.error(f"DB error: {e}")
        import traceback
        traceback.print_exc()


def load_pmkvy_data(csv_path="data/raw/pmkvy_data.csv"):
    try:
        import pandas as pd
    except ImportError:
        logger.error("Install pandas: pip install pandas")
        return []
    if not os.path.exists(csv_path):
        logger.warning(f"PMKVY CSV not found: {csv_path}")
        return []
    df = pd.read_csv(csv_path)
    records = []
    for _, row in df.iterrows():
        try:
            records.append({
                "state": str(row.get("State", "")),
                "district": str(row.get("District", "")),
                "sector": str(row.get("Sector", row.get("Job Role", ""))),
                "course_name": str(row.get("Course Name", row.get("job_role", ""))),
                "trained_count": int(row.get("Trained", 0) or 0),
                "certified_count": int(row.get("Certified", 0) or 0),
                "placed_count": int(row.get("Placed", 0) or 0),
                "year": int(row.get("Year", 2023) or 2023),
                "source_file": csv_path,
            })
        except:
            continue
    logger.success(f"✅ Loaded {len(records)} PMKVY records")
    return records


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", choices=["nptel", "swayam", "pmkvy", "both", "all"], default="both")
    parser.add_argument("--max-pages", type=int, default=5)
    parser.add_argument("--pmkvy-csv", default="data/raw/pmkvy_data.csv")
    args = parser.parse_args()

    print("\n" + "="*60)
    print("  Skills Mirage — Course Scraper (Fixed)")
    print("="*60)

    if args.source in ("nptel", "both", "all"):
        nptel = scrape_nptel_courses(max_pages=args.max_pages)
        if nptel:
            save_courses_to_json(nptel, "nptel")
            save_courses_to_db(nptel)
            print(f"\n✅ NPTEL: {len(nptel)} courses saved")

    if args.source in ("swayam", "both", "all"):
        swayam = scrape_swayam_courses(max_pages=args.max_pages)
        if swayam:
            save_courses_to_json(swayam, "swayam")
            save_courses_to_db(swayam)
            print(f"✅ SWAYAM: {len(swayam)} courses saved")

    if args.source in ("pmkvy", "all"):
        from scrapers.courses_scraper import load_pmkvy_data
        pmkvy = load_pmkvy_data(args.pmkvy_csv)

    print("\n✅ Course scraping done!")