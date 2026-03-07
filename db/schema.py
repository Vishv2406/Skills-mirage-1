"""
db/schema.py
============
Database models for Skills Mirage.
Uses SQLAlchemy — works with both SQLite (hackathon) and PostgreSQL (production).

Run this once to create all tables:
    python db/schema.py
"""

from sqlalchemy import (
    create_engine, Column, Integer, String, Float,
    DateTime, Text, Boolean, ForeignKey, JSON
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

Base = declarative_base()

# ─────────────────────────────────────────────
# TABLE 1: Raw Job Listings (scraped from Naukri / LinkedIn)
# ─────────────────────────────────────────────
class JobListing(Base):
    __tablename__ = "job_listings"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    source          = Column(String(50))          # "naukri" or "linkedin"
    external_id     = Column(String(200), unique=True)  # original job ID from source
    title           = Column(String(300))
    company         = Column(String(300))
    city            = Column(String(100))
    state           = Column(String(100))
    sector          = Column(String(200))         # BPO, IT, Manufacturing, etc.
    experience_min  = Column(Integer)             # years
    experience_max  = Column(Integer)
    salary_min      = Column(Float)               # in LPA
    salary_max      = Column(Float)
    skills_raw      = Column(Text)                # comma-separated raw skills from listing
    skills_parsed   = Column(JSON)                # list of cleaned skill names
    description     = Column(Text)                # full JD text
    ai_tool_mentions = Column(Integer, default=0) # count of AI tool mentions in JD
    posted_date     = Column(DateTime)
    scraped_at      = Column(DateTime, default=datetime.utcnow)
    is_active       = Column(Boolean, default=True)

    def __repr__(self):
        return f"<Job {self.title} @ {self.company} [{self.city}]>"


# ─────────────────────────────────────────────
# TABLE 2: Skills Demand Snapshot (aggregated daily)
# ─────────────────────────────────────────────
class SkillDemandSnapshot(Base):
    __tablename__ = "skill_demand_snapshots"

    id           = Column(Integer, primary_key=True, autoincrement=True)
    skill_name   = Column(String(200))
    city         = Column(String(100))
    sector       = Column(String(200))
    count        = Column(Integer)        # how many job listings require this skill
    snapshot_date = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<SkillDemand {self.skill_name} in {self.city}: {self.count}>"


# ─────────────────────────────────────────────
# TABLE 3: AI Vulnerability Index per Role+City
# ─────────────────────────────────────────────
class VulnerabilityIndex(Base):
    __tablename__ = "vulnerability_index"

    id                    = Column(Integer, primary_key=True, autoincrement=True)
    job_category          = Column(String(200))   # "BPO Voice", "Data Entry", etc.
    city                  = Column(String(100))
    score                 = Column(Float)          # 0–100
    risk_level            = Column(String(20))     # Critical / High / Medium / Low
    hiring_trend_pct      = Column(Float)          # % change in hiring volume (negative = declining)
    ai_mention_rate       = Column(Float)          # % of JDs mentioning AI tools
    replacement_ratio     = Column(Float)          # ratio of AI-augmented vs traditional job postings
    score_methodology     = Column(JSON)           # breakdown of how score was calculated
    computed_at           = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Vuln {self.job_category} [{self.city}]: {self.score}/100>"


# ─────────────────────────────────────────────
# TABLE 4: Training Courses (NPTEL + SWAYAM)
# ─────────────────────────────────────────────
class TrainingCourse(Base):
    __tablename__ = "training_courses"

    id               = Column(Integer, primary_key=True, autoincrement=True)
    source           = Column(String(50))     # "nptel" or "swayam" or "pmkvy"
    title            = Column(String(500))
    institution      = Column(String(300))    # e.g. "IIT Madras"
    url              = Column(String(1000))
    duration_weeks   = Column(Integer)
    hours_per_week   = Column(Float)
    topics           = Column(JSON)           # list of skill tags
    level            = Column(String(50))     # Beginner / Intermediate / Advanced
    is_free          = Column(Boolean, default=True)
    certification    = Column(Boolean, default=False)
    scraped_at       = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Course {self.title} [{self.source}]>"


# ─────────────────────────────────────────────
# TABLE 5: PMKVY Training Data (from data.gov.in)
# ─────────────────────────────────────────────
class PMKVYData(Base):
    __tablename__ = "pmkvy_data"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    state           = Column(String(100))
    district        = Column(String(100))
    sector          = Column(String(200))
    course_name     = Column(String(300))
    trained_count   = Column(Integer)
    certified_count = Column(Integer)
    placed_count    = Column(Integer)
    year            = Column(Integer)
    source_file     = Column(String(200))

    def __repr__(self):
        return f"<PMKVY {self.course_name} [{self.state}] {self.year}>"


# ─────────────────────────────────────────────
# TABLE 6: Scrape Run Logs
# ─────────────────────────────────────────────
class ScrapeLog(Base):
    __tablename__ = "scrape_logs"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    source        = Column(String(100))
    started_at    = Column(DateTime, default=datetime.utcnow)
    finished_at   = Column(DateTime)
    records_added = Column(Integer, default=0)
    status        = Column(String(50))    # "success", "partial", "failed"
    error_message = Column(Text)


# ─────────────────────────────────────────────
# DB Setup helper
# ─────────────────────────────────────────────
def get_engine():
    db_url = os.getenv("DATABASE_URL", "sqlite:///./skills_mirage.db")
    return create_engine(db_url, echo=False)

def get_session():
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()

def create_all_tables():
    engine = get_engine()
    Base.metadata.create_all(engine)
    print("✅ All tables created successfully!")
    print("   Tables: job_listings, skill_demand_snapshots, vulnerability_index,")
    print("           training_courses, pmkvy_data, scrape_logs")

if __name__ == "__main__":
    create_all_tables()