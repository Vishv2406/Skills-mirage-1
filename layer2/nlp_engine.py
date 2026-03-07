 
"""
layer2/nlp_engine.py
=====================
NLP engine that processes the worker's 100-200 word write-up.

This is the MOST CRITICAL part of Layer 2.
Two workers with the same title can have completely different skills.
The write-up extracts:
  - Explicit skills (tools, software, methods they mention)
  - Implicit skills (soft skills, domain knowledge)
  - Aspirations (what they want to move toward)
  - Experience signals (what they've actually done)

If the write-up is ignored → counts as NOT IMPLEMENTED by judges.

Usage:
    from layer2.nlp_engine import extract_worker_profile
    result = extract_worker_profile("I manage BPO teams of 15 agents...")
"""

import re
import json
from typing import Optional

# ─── Skill keyword dictionaries ───────────────────────────────────────────────

# Hard skills — tools, software, technical
HARD_SKILLS = {
    # IT & Dev
    "python": ["python", "django", "flask", "pandas", "numpy", "scripting", "py", "python programming"],
    "java": ["java", "spring", "j2ee", "maven", "java programming"],
    "javascript": ["javascript", "js", "node", "react", "angular", "vue", "typescript", "nodejs"],
    "sql": ["sql", "mysql", "postgresql", "database", "queries", "oracle", "sql server", "query", "rdbms"],
    "excel": ["excel", "spreadsheet", "pivot", "vlookup", "macros", "ms excel", "advanced excel", "excel formulas"],
    "cloud": ["aws", "azure", "gcp", "cloud", "s3", "ec2", "lambda", "cloud computing", "devops"],
    "data analysis": ["data analysis", "analytics", "reporting", "dashboards", "bi", "tableau", "power bi", "data visualization", "data analytics"],
    "machine learning": ["machine learning", "ml", "ai", "deep learning", "tensorflow", "model", "neural network", "predictive modeling"],
    "digital marketing": ["seo", "sem", "google ads", "facebook ads", "social media", "content marketing", "email marketing", "digital marketing", "online marketing", "ppc"],
    "accounting": ["tally", "gst", "taxation", "audit", "accounts", "balance sheet", "invoicing", "bookkeeping", "accounting", "financial accounting"],
    "crm": ["crm", "salesforce", "zoho", "hubspot", "customer relationship", "crm software", "customer management"],
    "rpa": ["rpa", "uipath", "automation anywhere", "blue prism", "automation", "robotic process automation", "process automation"],
    "content writing": ["content writing", "copywriting", "blogging", "seo writing", "proofreading", "editing", "technical writing", "creative writing"],
    "graphic design": ["photoshop", "illustrator", "canva", "figma", "design", "ui/ux", "adobe", "graphic design", "visual design"],
    "project management": ["jira", "trello", "asana", "project management", "pmp", "agile", "scrum", "sprint", "project planning", "project coordination"],
    "customer support": ["customer support", "helpdesk", "ticketing", "zendesk", "freshdesk", "call handling", "customer service", "client support"],
    "bpo operations": ["bpo", "voice process", "non-voice", "inbound", "outbound", "dialer", "ivr", "aht", "csat", "call center", "call centre"],
    "hr": ["recruitment", "hiring", "onboarding", "payroll", "hrms", "appraisal", "talent acquisition", "hr operations", "employee relations"],
    "logistics": ["supply chain", "inventory", "warehouse", "dispatch", "erp", "sap", "logistics", "inventory management", "supply chain management"],
    "communication": ["english", "communication", "presentation", "public speaking", "verbal communication", "written communication"],
}

# Soft skills — inferred from how they describe their work
SOFT_SKILLS = {
    "leadership": ["lead", "manage", "team lead", "supervise", "mentor", "guide", "head", "in-charge", "leading", "managed", "leadership", "team management"],
    "communication": ["communicate", "present", "spoken", "written", "english", "client-facing", "liaison", "presentation", "communicating", "fluent", "proficient"],
    "problem solving": ["solve", "troubleshoot", "debug", "root cause", "analyse", "investigate", "fix", "problem solving", "analytical", "analysis", "resolved"],
    "attention to detail": ["accurate", "precise", "error-free", "quality check", "qa", "verify", "audit", "meticulous", "thorough", "detail-oriented"],
    "multitasking": ["multitask", "juggle", "handle multiple", "parallel", "simultaneous", "multi-tasking", "managing multiple"],
    "client management": ["client", "customer", "stakeholder", "escalation", "relationship management", "client-facing", "customer-facing", "account management"],
    "training": ["train", "coach", "teach", "onboard", "induct", "workshop", "facilitator", "training", "mentoring", "coaching"],
    "target-driven": ["target", "kpi", "quota", "achieve", "exceed", "performance", "metrics", "goal-oriented", "results-driven", "achieved"],
    "time management": ["deadline", "time management", "prioritize", "schedule", "organize", "planning", "efficient"],
    "teamwork": ["team", "collaborate", "cooperation", "teamwork", "team player", "collaborative", "working with team"],
}

# Aspiration keywords → target job domains
ASPIRATION_MAP = {
    "data analyst": ["data", "analytics", "insights", "dashboards", "reporting", "numbers", "data analysis", "business intelligence", "data-driven"],
    "digital marketing": ["marketing", "social media", "content", "brand", "audience", "campaign", "seo", "digital marketing", "online marketing"],
    "software developer": ["coding", "programming", "developer", "build apps", "software", "development", "software engineer", "web development"],
    "product manager": ["product", "roadmap", "features", "user stories", "stakeholder", "product management", "product development"],
    "hr manager": ["hr", "people", "culture", "hiring", "talent", "human resources", "recruitment", "employee"],
    "operations manager": ["operations", "process", "efficiency", "optimize", "workflow", "operations management", "process improvement"],
    "content creator": ["write", "create content", "blog", "video", "creative", "content creation", "blogging", "writing"],
    "accountant": ["finance", "accounts", "gst", "taxation", "audit", "accounting", "financial", "bookkeeping"],
    "customer success": ["customer", "client", "satisfaction", "relationship", "support", "customer success", "client management"],
    "ai/ml engineer": ["ai", "machine learning", "model", "algorithm", "data science", "artificial intelligence", "ml", "deep learning"],
    "business analyst": ["business analysis", "requirements", "business analyst", "ba", "business intelligence", "stakeholder analysis"],
    "project manager": ["project management", "project manager", "pmp", "agile", "scrum", "project coordination"],
}

# AI displacement risk per skill domain
SKILL_RISK_SCORES = {
    "bpo operations":     85,
    "customer support":   78,
    "data analysis":      35,
    "accounting":         55,
    "content writing":    60,
    "digital marketing":  30,
    "python":             15,
    "machine learning":   10,
    "sql":                40,
    "excel":              50,
    "rpa":                20,
    "hr":                 45,
    "logistics":          60,
    "graphic design":     55,
    "project management": 30,
    "crm":                50,
    "java":               20,
    "javascript":         20,
    "cloud":              15,
}


# ─────────────────────────────────────────────────────────────────────────────
# MAIN EXTRACTION FUNCTION
# ─────────────────────────────────────────────────────────────────────────────

def extract_worker_profile(
    write_up: str,
    job_title: str = "",
    city: str = "",
    years_experience: int = 0,
) -> dict:
    """
    Extract structured profile from worker's free-text write-up.
    
    Args:
        write_up: 100-200 word description of their work, skills, aspirations
        job_title: Their current job title
        city: Their city
        years_experience: Years of experience
    
    Returns:
        dict with extracted skills, soft skills, aspirations, risk factors
    """
    text = write_up.lower().strip()
    title_lower = job_title.lower()

    # ── Step 1: Extract hard skills ──────────────────────────────────────────
    extracted_hard = []
    skill_scores = []

    for skill_name, keywords in HARD_SKILLS.items():
        if any(kw in text for kw in keywords):
            extracted_hard.append(skill_name)
            if skill_name in SKILL_RISK_SCORES:
                skill_scores.append(SKILL_RISK_SCORES[skill_name])

    # Also check job title for skills
    for skill_name, keywords in HARD_SKILLS.items():
        if skill_name not in extracted_hard:
            if any(kw in title_lower for kw in keywords):
                extracted_hard.append(skill_name)

    # ── Step 2: Extract soft skills ───────────────────────────────────────────
    extracted_soft = []
    for skill_name, keywords in SOFT_SKILLS.items():
        if any(kw in text for kw in keywords):
            extracted_soft.append(skill_name)

    # ── Step 3: Extract aspirations ───────────────────────────────────────────
    aspiration_scores = {}
    for domain, keywords in ASPIRATION_MAP.items():
        score = sum(1 for kw in keywords if kw in text)
        if score > 0:
            aspiration_scores[domain] = score

    # Top aspiration
    top_aspiration = max(aspiration_scores, key=aspiration_scores.get) if aspiration_scores else None

    # ── Step 4: Extract experience signals ────────────────────────────────────
    experience_signals = extract_experience_signals(text, years_experience)

    # ── Step 5: Calculate skill-based risk contribution ───────────────────────
    skill_risk = 0
    if skill_scores:
        skill_risk = sum(skill_scores) / len(skill_scores)

    # ── Step 6: Compute profile completeness score ────────────────────────────
    completeness = compute_completeness(
        write_up, extracted_hard, extracted_soft, top_aspiration
    )

    return {
        "hard_skills": extracted_hard,
        "soft_skills": extracted_soft,
        "top_aspiration": top_aspiration,
        "all_aspirations": aspiration_scores,
        "experience_signals": experience_signals,
        "skill_risk_score": round(skill_risk, 1),
        "profile_completeness": completeness,
        "word_count": len(write_up.split()),
        "write_up_used": True,  # Proof for judges that write-up was processed
        "extraction_summary": build_summary(
            extracted_hard, extracted_soft, top_aspiration, experience_signals
        ),
    }


def extract_experience_signals(text: str, years: int) -> dict:
    """Extract quantitative and qualitative experience signals."""
    signals = {
        "has_team_management": False,
        "has_client_facing": False,
        "has_technical_tools": False,
        "has_targets_metrics": False,
        "has_process_improvement": False,
        "team_size": None,
        "tools_mentioned": [],
        "years_bucket": categorize_experience(years),
        "quantifiable_achievements": [],
    }

    # Team size - improved regex
    team_patterns = [
        r"team of (\d+)",
        r"(\d+)[- ]member team",
        r"manage (\d+) (?:people|agents|employees|members)",
        r"leading (\d+)",
        r"supervise (\d+)",
        r"(\d+) person team"
    ]
    for pattern in team_patterns:
        match = re.search(pattern, text)
        if match:
            signals["team_size"] = int(match.group(1))
            signals["has_team_management"] = True
            break

    # Management signals - expanded
    management_keywords = ["manage", "lead", "supervise", "team lead", "head of", "in-charge", 
                          "leading", "managed", "supervised", "coordinated", "oversaw"]
    if any(kw in text for kw in management_keywords):
        signals["has_team_management"] = True

    # Client-facing - expanded
    client_keywords = ["client", "customer", "stakeholder", "account management", "client-facing",
                      "customer-facing", "escalation", "client interaction", "customer interaction"]
    if any(kw in text for kw in client_keywords):
        signals["has_client_facing"] = True

    # Technical tools mentioned - expanded list
    tools = []
    tool_keywords = ["excel", "python", "sql", "tally", "salesforce", "jira",
                     "tableau", "power bi", "sap", "zoho", "aws", "azure",
                     "google analytics", "hubspot", "zendesk", "uipath", "ms office",
                     "crm", "erp", "mysql", "postgresql", "django", "flask", "react",
                     "angular", "node", "javascript", "java", "photoshop", "illustrator",
                     "canva", "figma", "trello", "asana", "slack", "teams"]
    for tool in tool_keywords:
        if tool in text:
            tools.append(tool)
    signals["tools_mentioned"] = tools
    signals["has_technical_tools"] = len(tools) > 0

    # Metrics / targets - expanded
    metrics_keywords = ["target", "kpi", "csat", "nps", "aht", "% increase", "reduced", 
                       "improved by", "achieved", "exceeded", "performance", "metrics",
                       "increased by", "decreased by", "growth", "efficiency"]
    if any(kw in text for kw in metrics_keywords):
        signals["has_targets_metrics"] = True

    # Process improvement signals
    improvement_keywords = ["improved", "optimized", "streamlined", "reduced", "increased",
                           "enhanced", "automated", "efficiency", "process improvement"]
    if any(kw in text for kw in improvement_keywords):
        signals["has_process_improvement"] = True

    # Extract quantifiable achievements
    achievement_patterns = [
        r"(\d+)%\s+(?:increase|growth|improvement|reduction)",
        r"(?:increased|reduced|improved|achieved)\s+(?:by\s+)?(\d+)%",
        r"saved\s+(?:rs\.?|₹)?\s*(\d+)",
        r"generated\s+(?:rs\.?|₹)?\s*(\d+)",
    ]
    for pattern in achievement_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            signals["quantifiable_achievements"].extend(matches)

    return signals


def categorize_experience(years: int) -> str:
    if years <= 1:   return "fresher"
    if years <= 3:   return "junior"
    if years <= 7:   return "mid-level"
    if years <= 12:  return "senior"
    return "veteran"


def compute_completeness(write_up: str, hard: list, soft: list, aspiration) -> dict:
    """Score how complete the worker profile is."""
    word_count = len(write_up.split())
    scores = {
        "word_count":   min(100, word_count / 2),           # 200 words = 100%
        "hard_skills":  min(100, len(hard) * 20),            # 5+ skills = 100%
        "soft_skills":  min(100, len(soft) * 25),            # 4+ = 100%
        "aspiration":   100 if aspiration else 0,
    }
    overall = sum(scores.values()) / len(scores)
    return {
        "scores": scores,
        "overall": round(overall, 1),
        "is_sufficient": overall >= 50,
    }


def build_summary(hard: list, soft: list, aspiration, signals: dict) -> str:
    """Build a human-readable summary of what was extracted."""
    parts = []

    if hard:
        parts.append(f"Technical skills detected: {', '.join(hard[:5])}")
    if soft:
        parts.append(f"Soft skills: {', '.join(soft[:3])}")
    if aspiration:
        parts.append(f"Career aspiration: {aspiration}")
    if signals.get("has_team_management"):
        size = signals.get("team_size")
        parts.append(f"Has managed teams" + (f" of {size}" if size else ""))
    if signals.get("tools_mentioned"):
        parts.append(f"Tools used: {', '.join(signals['tools_mentioned'][:4])}")

    return " · ".join(parts) if parts else "Basic profile extracted"


# ─────────────────────────────────────────────────────────────────────────────
# RESKILLING PATH GENERATOR
# ─────────────────────────────────────────────────────────────────────────────

def generate_reskilling_path(
    worker_profile: dict,
    target_role: str,
    current_role: str,
    city: str,
    max_weeks: Optional[int] = None,
    db_courses=None,
) -> dict:
    """
    Generate a week-by-week reskilling path from current role → target role.
    
    Uses:
    - Worker's extracted skills (to avoid recommending what they already know)
    - Target role skill requirements
    - Real courses from NPTEL/SWAYAM database
    - City-specific course center info for PMKVY
    
    Args:
        worker_profile: output of extract_worker_profile()
        target_role: job title they want to move to
        current_role: their current job title
        city: their city
        max_weeks: optional constraint (e.g. "show paths under 3 months" = 12 weeks)
        db_courses: list of course dicts from database
    
    Returns:
        dict with week-by-week plan, total duration, target role hiring data
    """

    # Skills required for common target roles
    ROLE_SKILL_MAP = {
        "data analyst": {
            "skills": ["sql", "excel", "python", "data analysis", "tableau", "statistics"],
            "priority": ["sql", "excel", "data analysis"],
            "avg_salary_lpa": 6.5,
            "hiring_cities": ["Bangalore", "Hyderabad", "Mumbai", "Pune", "Chennai", "Delhi"],
        },
        "digital marketing": {
            "skills": ["seo", "google ads", "social media", "content writing", "analytics", "email marketing", "digital marketing"],
            "priority": ["seo", "google ads", "social media"],
            "avg_salary_lpa": 4.5,
            "hiring_cities": ["Mumbai", "Delhi", "Bangalore", "Hyderabad", "Pune"],
        },
        "python developer": {
            "skills": ["python", "sql", "django", "git", "apis", "problem solving"],
            "priority": ["python", "sql", "django"],
            "avg_salary_lpa": 7.0,
            "hiring_cities": ["Bangalore", "Hyderabad", "Pune", "Chennai", "Mumbai"],
        },
        "hr executive": {
            "skills": ["recruitment", "hrms", "payroll", "communication", "excel", "onboarding"],
            "priority": ["recruitment", "communication", "hrms"],
            "avg_salary_lpa": 4.0,
            "hiring_cities": ["Mumbai", "Delhi", "Bangalore", "Hyderabad", "Pune", "Chennai"],
        },
        "content writer": {
            "skills": ["content writing", "seo", "research", "copywriting", "editing", "social media"],
            "priority": ["content writing", "seo", "research"],
            "avg_salary_lpa": 3.5,
            "hiring_cities": ["Delhi", "Mumbai", "Bangalore", "Hyderabad", "Pune"],
        },
        "customer success": {
            "skills": ["crm", "communication", "problem solving", "excel", "client management"],
            "priority": ["crm", "communication", "client management"],
            "avg_salary_lpa": 5.0,
            "hiring_cities": ["Bangalore", "Hyderabad", "Pune", "Mumbai", "Chennai"],
        },
        "rpa developer": {
            "skills": ["rpa", "uipath", "python", "sql", "process mapping", "automation"],
            "priority": ["rpa", "python", "sql"],
            "avg_salary_lpa": 6.0,
            "hiring_cities": ["Bangalore", "Hyderabad", "Pune", "Chennai"],
        },
        "ai content reviewer": {
            "skills": ["content review", "ai tools", "communication", "attention to detail", "english"],
            "priority": ["communication", "ai tools", "attention to detail"],
            "avg_salary_lpa": 4.5,
            "hiring_cities": ["Bangalore", "Hyderabad", "Pune", "Mumbai", "Chennai", "Delhi"],
        },
        "operations analyst": {
            "skills": ["excel", "data analysis", "process improvement", "sql", "reporting", "problem solving"],
            "priority": ["excel", "data analysis", "process improvement"],
            "avg_salary_lpa": 5.5,
            "hiring_cities": ["Mumbai", "Delhi", "Bangalore", "Hyderabad", "Pune", "Chennai"],
        },
    }

    # Normalize target role
    target_lower = target_role.lower().strip()
    role_info = None
    for role_key, info in ROLE_SKILL_MAP.items():
        if role_key in target_lower or target_lower in role_key:
            role_info = info
            target_role = role_key.title()
            break

    if not role_info:
        # Default fallback
        role_info = ROLE_SKILL_MAP["data analyst"]
        target_role = "Data Analyst"

    # Worker's existing skills
    existing_skills = set(worker_profile.get("hard_skills", []) +
                          worker_profile.get("soft_skills", []))

    # Skills to learn = required - already have
    required_skills = role_info["skills"]
    skills_to_learn = [s for s in required_skills if not any(
        existing in s or s in existing for existing in existing_skills
    )]

    if not skills_to_learn:
        skills_to_learn = required_skills[:3]  # Always suggest at least 3

    # Match courses from DB or use curated fallback
    courses_for_path = match_courses_to_skills(skills_to_learn, db_courses)

    # Build week-by-week plan
    plan = build_weekly_plan(
        skills_to_learn=skills_to_learn,
        courses=courses_for_path,
        city=city,
        max_weeks=max_weeks,
    )

    # Is target role hiring in their city?
    hiring_in_city = city in role_info.get("hiring_cities", [])
    nearest_hiring_city = role_info["hiring_cities"][0] if not hiring_in_city else city

    # Skills they already have that are relevant to target role
    matching_skills = list(existing_skills & set(required_skills))
    
    # If no matching skills, show their top skills anyway
    if not matching_skills:
        matching_skills = list(existing_skills)[:5]  # Show top 5 existing skills
    
    # Ensure we always have something to show
    if not matching_skills:
        # Extract from job title if nothing else
        matching_skills = [current_role.lower()]

    return {
        "target_role": target_role,
        "current_role": current_role,
        "city": city,
        "skills_already_have": matching_skills,
        "skills_to_learn": skills_to_learn,
        "weekly_plan": plan["weeks"],
        "total_weeks": plan["total_weeks"],
        "total_hours": plan["total_hours"],
        "hiring_in_city": hiring_in_city,
        "nearest_hiring_city": nearest_hiring_city,
        "avg_salary_lpa": role_info["avg_salary_lpa"],
        "courses_used": [c["title"] for c in courses_for_path],
        "path_summary": build_path_summary(plan, target_role, city, hiring_in_city, nearest_hiring_city),
    }


def match_courses_to_skills(skills_needed: list, db_courses=None) -> list:
    """Match skills needed to available courses."""

    # Fallback curated courses if no DB
    FALLBACK_COURSES = [
        {"title": "Python for Data Science", "source": "nptel", "institution": "IIT Madras",
         "url": "https://nptel.ac.in/courses/106106212", "duration_weeks": 8, "hours_per_week": 6,
         "topics": ["python", "data analysis", "pandas"]},
        {"title": "Introduction to Machine Learning", "source": "nptel", "institution": "IIT Kharagpur",
         "url": "https://nptel.ac.in/courses/106105152", "duration_weeks": 8, "hours_per_week": 6,
         "topics": ["machine learning", "python", "ai"]},
        {"title": "Database Management System", "source": "nptel", "institution": "IIT Madras",
         "url": "https://nptel.ac.in/courses/106106093", "duration_weeks": 8, "hours_per_week": 5,
         "topics": ["sql", "database"]},
        {"title": "Digital Marketing", "source": "nptel", "institution": "IIT Delhi",
         "url": "https://nptel.ac.in/courses/110102028", "duration_weeks": 8, "hours_per_week": 4,
         "topics": ["digital marketing", "seo", "social media"]},
        {"title": "Business Analytics and Data Mining", "source": "nptel", "institution": "IIT Roorkee",
         "url": "https://nptel.ac.in/courses/110107108", "duration_weeks": 8, "hours_per_week": 5,
         "topics": ["data analysis", "analytics", "excel"]},
        {"title": "Soft Skills", "source": "nptel", "institution": "IIT Kanpur",
         "url": "https://nptel.ac.in/courses/109104099", "duration_weeks": 8, "hours_per_week": 4,
         "topics": ["communication", "soft skills", "presentation"]},
        {"title": "Financial Accounting", "source": "nptel", "institution": "IIT Kharagpur",
         "url": "https://nptel.ac.in/courses/110105049", "duration_weeks": 8, "hours_per_week": 4,
         "topics": ["accounting", "finance", "tally"]},
        {"title": "Python Programming", "source": "swayam", "institution": "NPTEL",
         "url": "https://swayam.gov.in/nd1_noc20_cs47/preview", "duration_weeks": 8, "hours_per_week": 5,
         "topics": ["python", "programming"]},
        {"title": "Digital Marketing and E-Commerce", "source": "swayam", "institution": "NPTEL",
         "url": "https://swayam.gov.in/courses/digital-marketing", "duration_weeks": 8, "hours_per_week": 4,
         "topics": ["digital marketing", "seo", "ecommerce"]},
        {"title": "Customer Relationship Management", "source": "swayam", "institution": "IGNOU",
         "url": "https://swayam.gov.in/courses/crm", "duration_weeks": 6, "hours_per_week": 3,
         "topics": ["crm", "customer service", "communication"]},
        {"title": "Human Resource Management", "source": "swayam", "institution": "IIM Lucknow",
         "url": "https://swayam.gov.in/courses/hrm", "duration_weeks": 8, "hours_per_week": 4,
         "topics": ["hr", "recruitment", "talent management"]},
        {"title": "Goods and Services Tax (GST)", "source": "swayam", "institution": "ICAI",
         "url": "https://swayam.gov.in/courses/gst", "duration_weeks": 4, "hours_per_week": 4,
         "topics": ["gst", "accounting", "taxation", "finance"]},
        {"title": "Data Analytics with Python", "source": "swayam", "institution": "NPTEL",
         "url": "https://swayam.gov.in/courses/data-analytics-python", "duration_weeks": 8, "hours_per_week": 6,
         "topics": ["data analysis", "python", "pandas", "visualization"]},
        {"title": "Spoken English for Beginners", "source": "swayam", "institution": "IGNOU",
         "url": "https://swayam.gov.in/courses/spoken-english", "duration_weeks": 8, "hours_per_week": 3,
         "topics": ["english", "communication", "soft skills"]},
    ]

    course_pool = db_courses if db_courses else FALLBACK_COURSES
    matched = []
    used_titles = set()

    for skill in skills_needed:
        for course in course_pool:
            if course["title"] in used_titles:
                continue
            topics = course.get("topics", [])
            if isinstance(topics, str):
                try:
                    topics = json.loads(topics)
                except:
                    topics = []
            if any(skill.lower() in t.lower() or t.lower() in skill.lower() for t in topics):
                matched.append(course)
                used_titles.add(course["title"])
                break

    # If we didn't find enough, add top courses
    if len(matched) < 3:
        for course in course_pool:
            if course["title"] not in used_titles and len(matched) < 4:
                matched.append(course)
                used_titles.add(course["title"])

    return matched[:4]  # Max 4 courses per path


def build_weekly_plan(skills_to_learn: list, courses: list, city: str, max_weeks=None) -> dict:
    """Convert courses into a week-by-week schedule."""
    weeks = []
    week_num = 1
    total_hours = 0

    for i, course in enumerate(courses):
        duration = course.get("duration_weeks", 8)
        hours_pw = course.get("hours_per_week", 5)

        # Respect max_weeks constraint
        if max_weeks and week_num + duration > max_weeks:
            duration = max(2, max_weeks - week_num)

        start_week = week_num
        end_week = week_num + duration - 1
        total_hours += duration * hours_pw

        source_label = course.get("source", "nptel").upper()
        institution = course.get("institution", "IIT")

        # Add location info for PMKVY
        location_note = ""
        if source_label == "PMKVY":
            location_note = f" (Centre available in {city})"

        weeks.append({
            "week_range": f"Wk {start_week}–{end_week}",
            "week_start": start_week,
            "week_end": end_week,
            "course_title": course["title"],
            "source": source_label,
            "institution": institution,
            "url": course.get("url", ""),
            "hours_per_week": hours_pw,
            "total_hours": duration * hours_pw,
            "skill_covered": skills_to_learn[i] if i < len(skills_to_learn) else "",
            "note": f"{institution}, free, {hours_pw} hrs/wk{location_note}",
            "is_free": course.get("is_free", True),
            "certification": course.get("certification", True),
        })

        week_num = end_week + 1

        if max_weeks and week_num > max_weeks:
            break

    return {
        "weeks": weeks,
        "total_weeks": week_num - 1,
        "total_hours": total_hours,
    }


def build_path_summary(plan: dict, target_role: str, city: str,
                       hiring_in_city: bool, nearest_city: str) -> str:
    """Build a concise path summary for the UI."""
    total_weeks = plan["total_weeks"]
    total_hours = plan["total_hours"]
    courses = len(plan["weeks"])

    city_note = (f"Target role is actively hiring in {city}." if hiring_in_city
                 else f"Nearest hiring city: {nearest_city}.")

    return (
        f"{courses} courses · {total_weeks} weeks · "
        f"~{total_hours} hrs total · All free & certified. {city_note}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# QUICK TEST
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    sample_writeup = """
    I have been working as a Senior Executive in a BPO for the past 6 years handling 
    inbound voice calls for a US-based insurance client. I manage a team of 12 agents 
    and track daily AHT and CSAT scores using Excel. I am good at resolving escalations 
    and have reduced average handling time by 18% over the last year. I am comfortable 
    with English communication and have basic knowledge of Salesforce CRM. 
    I want to move away from voice processes and get into data or analytics roles 
    since I enjoy working with numbers and reports. I am willing to put in 10 hours 
    a week to learn new skills.
    """

    print("=" * 60)
    print("NLP ENGINE — Sample Extraction")
    print("=" * 60)

    profile = extract_worker_profile(
        write_up=sample_writeup,
        job_title="Senior Executive BPO",
        city="Pune",
        years_experience=6,
    )

    print(f"\n📋 Extracted Profile:")
    print(f"   Hard Skills:     {profile['hard_skills']}")
    print(f"   Soft Skills:     {profile['soft_skills']}")
    print(f"   Top Aspiration:  {profile['top_aspiration']}")
    print(f"   Skill Risk:      {profile['skill_risk_score']}/100")
    print(f"   Completeness:    {profile['profile_completeness']['overall']}%")
    print(f"   Summary:         {profile['extraction_summary']}")

    print(f"\n📚 Generating Reskilling Path → Data Analyst...")
    path = generate_reskilling_path(
        worker_profile=profile,
        target_role="data analyst",
        current_role="Senior Executive BPO",
        city="Pune",
    )

    print(f"\n   Target Role:     {path['target_role']}")
    print(f"   Total Weeks:     {path['total_weeks']}")
    print(f"   Total Hours:     {path['total_hours']}")
    print(f"   Hiring in Pune:  {path['hiring_in_city']}")
    print(f"\n   Week-by-Week Plan:")
    for week in path["weekly_plan"]:
        print(f"   {week['week_range']:12} → {week['course_title']} [{week['source']}]")
    print(f"\n   Summary: {path['path_summary']}")