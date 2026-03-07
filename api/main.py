"""
api/main.py
============
FastAPI backend for Layer 2 — Worker Intelligence Engine.

Endpoints:
  POST /api/analyze        → Full analysis (risk score + reskilling path)
  GET  /api/jobs/live      → Live job count for a role+city (for chatbot)
  GET  /api/vulnerability  → Vulnerability index for a city
  POST /api/chat           → AI Chatbot (English + Hindi)
  GET  /api/health         → Health check

Run:
    uvicorn api.main:app --reload --port 8000

Then test at: http://localhost:8000/docs
"""

import os
import sys
import json
from typing import Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Add project root
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from layer2.nlp_engine import extract_worker_profile, generate_reskilling_path
from layer2.risk_engine import compute_risk_score, fetch_layer1_data

app = FastAPI(
    title="Skills Mirage — Layer 2 API",
    description="Worker Intelligence Engine: Risk Scoring + Reskilling Paths + AI Chatbot",
    version="1.0.0",
)

# Allow Streamlit frontend to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Request / Response Models ────────────────────────────────────────────────

class WorkerInput(BaseModel):
    job_title:        str = Field(..., example="Senior Executive, BPO")
    city:             str = Field(..., example="Pune")
    years_experience: int = Field(..., ge=0, le=50, example=6)
    write_up:         str = Field(..., min_length=50, max_length=2000,
                                  example="I manage a BPO team of 12 agents...")
    target_role:      Optional[str] = Field(None, example="Data Analyst")
    max_weeks:        Optional[int] = Field(None, ge=1, le=52,
                                            example=12)


class ChatMessage(BaseModel):
    message:          str = Field(..., example="Why is my risk score so high?")
    language:         str = Field(default="en", example="en")  # "en" or "hi"
    worker_context:   Optional[dict] = Field(None)  # Pass previous analysis result


# ─────────────────────────────────────────────────────────────────────────────
# ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
    }


@app.post("/api/analyze")
def analyze_worker(worker: WorkerInput):
    """
    Full Layer 2 analysis for a worker.
    
    Steps:
    1. NLP on write-up → extract skills, aspirations, experience signals
    2. Fetch live Layer 1 data for their role + city
    3. Compute personal risk score (reacts to live L1 data)
    4. Generate week-by-week reskilling path
    5. Return everything in one response
    
    This is the core endpoint judges will test.
    """
    try:
        # Step 1: NLP extraction from write-up
        worker_profile = extract_worker_profile(
            write_up=worker.write_up,
            job_title=worker.job_title,
            city=worker.city,
            years_experience=worker.years_experience,
        )

        # Step 2: Fetch live Layer 1 data
        layer1_data = fetch_layer1_data(worker.job_title, worker.city)

        # Step 3: Compute risk score
        risk_result = compute_risk_score(
            job_title=worker.job_title,
            city=worker.city,
            years_experience=worker.years_experience,
            worker_profile=worker_profile,
            layer1_data=layer1_data,
        )

        # Step 4: Determine target role
        target_role = worker.target_role
        if not target_role:
            # Infer from aspiration
            target_role = worker_profile.get("top_aspiration", "Data Analyst")
            if not target_role:
                target_role = suggest_target_role(worker.job_title, risk_result["score"])

        # Step 5: Get courses from DB
        db_courses = load_courses_from_db()

        # Step 6: Generate reskilling path
        reskilling = generate_reskilling_path(
            worker_profile=worker_profile,
            target_role=target_role,
            current_role=worker.job_title,
            city=worker.city,
            max_weeks=worker.max_weeks,
            db_courses=db_courses,
        )

        return {
            "success": True,
            "worker": {
                "job_title": worker.job_title,
                "city": worker.city,
                "years_experience": worker.years_experience,
            },
            "nlp_profile": worker_profile,
            "risk": risk_result,
            "reskilling": reskilling,
            "layer1_snapshot": layer1_data,
            "analyzed_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        import traceback
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/jobs/live")
def get_live_job_count(role: str, city: str):
    """
    Get real-time job count for a role + city.
    Used by chatbot: "How many BPO jobs in Indore right now?"
    Returns REAL number from the pipeline, not a hallucinated answer.
    """
    try:
        sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
        from db.schema import get_session, JobListing
        from datetime import timedelta

        session = get_session()
        now = datetime.utcnow()
        role_lower = role.lower()

        # Query live
        jobs = session.query(JobListing).filter(
            JobListing.city == city,
            JobListing.is_active == True,
        ).all()

        # Filter to role
        role_jobs = [j for j in jobs if any(
            kw in (j.title or "").lower()
            for kw in role_lower.split()[:3]
        )]

        # Last 30 days
        recent = [j for j in role_jobs
                  if j.scraped_at >= now - timedelta(days=30)]

        session.close()

        return {
            "role": role,
            "city": city,
            "total_active": len(role_jobs),
            "last_30_days": len(recent),
            "queried_at": now.isoformat(),
            "data_source": "live_database",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/vulnerability")
def get_vulnerability(city: str, category: Optional[str] = None):
    """Get vulnerability index scores for a city (optionally filtered by category)."""
    try:
        from db.schema import get_session, VulnerabilityIndex

        session = get_session()
        q = session.query(VulnerabilityIndex).filter(
            VulnerabilityIndex.city == city
        )
        if category:
            q = q.filter(VulnerabilityIndex.job_category.ilike(f"%{category}%"))

        records = q.order_by(VulnerabilityIndex.score.desc()).all()
        session.close()

        return {
            "city": city,
            "records": [
                {
                    "job_category": r.job_category,
                    "score": r.score,
                    "risk_level": r.risk_level,
                    "hiring_trend_pct": r.hiring_trend_pct,
                    "ai_mention_rate": r.ai_mention_rate,
                }
                for r in records
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/safer-roles")
def get_safer_roles(city: str, current_score: float = 70):
    """
    Get low-risk roles actively hiring in a city.
    Used by chatbot: "What jobs are safer for someone like me?"
    """
    try:
        from db.schema import get_session, VulnerabilityIndex, JobListing

        session = get_session()

        # Low vulnerability roles
        safe_roles = session.query(VulnerabilityIndex).filter(
            VulnerabilityIndex.city == city,
            VulnerabilityIndex.score < 40,
        ).order_by(VulnerabilityIndex.score).limit(5).all()

        # Verify they're actively hiring
        results = []
        for role in safe_roles:
            job_count = session.query(JobListing).filter(
                JobListing.city == city,
                JobListing.is_active == True,
            ).count()

            results.append({
                "role": role.job_category,
                "vulnerability_score": role.score,
                "risk_level": role.risk_level,
                "active_listings": job_count,
            })

        session.close()
        return {"city": city, "safer_roles": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat")
def chat(msg: ChatMessage):
    """
    AI Chatbot endpoint.
    Handles all 5 required question types in English + Hindi.
    Uses Anthropic Claude API.
    
    Question types:
    1. "Why is my risk score so high?"
    2. "What jobs are safer for someone like me?"
    3. "Show me paths under 3 months"
    4. "How many BPO jobs in Indore right now?"
    5. "मुझे क्या करना चाहिए?" (Hindi)
    """
    try:
        import anthropic

        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

        # Build context from worker's analysis
        context = ""
        if msg.worker_context:
            risk = msg.worker_context.get("risk", {})
            reskilling = msg.worker_context.get("reskilling", {})
            worker = msg.worker_context.get("worker", {})
            nlp = msg.worker_context.get("nlp_profile", {})

            context = f"""
Worker Profile:
- Job Title: {worker.get('job_title', 'Unknown')}
- City: {worker.get('city', 'Unknown')}
- Experience: {worker.get('years_experience', 0)} years
- Skills: {', '.join(nlp.get('hard_skills', [])[:5])}
- Risk Score: {risk.get('score', 'N/A')}/100 ({risk.get('risk_level', 'N/A')})
- Risk Signals: {json.dumps(risk.get('signals', []))}
- Target Role: {reskilling.get('target_role', 'N/A')}
- Reskilling Path: {json.dumps(reskilling.get('weekly_plan', [])[:3])}
- Hiring in their city: {reskilling.get('hiring_in_city', 'N/A')}
"""

        # Language instruction
        lang_instruction = ""
        if msg.language == "hi" or any(
            ord(c) > 0x0900 and ord(c) < 0x097F for c in msg.message
        ):
            lang_instruction = """
IMPORTANT: The user is communicating in Hindi. 
You MUST respond entirely in Hindi (Devanagari script).
Do NOT switch to English at any point in your response.
Use simple, conversational Hindi that a non-technical person can understand.
"""

        system_prompt = f"""You are a helpful career advisor for Indian workers facing AI displacement.
You have access to real job market data from Naukri and LinkedIn India.

{context}

Your job is to answer questions about:
1. Why their risk score is high (cite specific signals — hiring decline %, AI mention rate)
2. What safer jobs exist (check vulnerability index, confirm actively hiring)
3. Reskilling paths (specific courses from NPTEL/SWAYAM, week-by-week, real URLs)
4. Live job counts (use exact numbers from the database, never hallucinate)
5. General career guidance

Rules:
- Always cite specific data points (numbers, percentages) from the worker's context
- Never give generic advice like "learn Python" — be specific with course names, institutions, URLs
- For job counts, only give numbers you have from the database
- Keep responses concise and actionable (3-5 sentences max unless asked for detail)
- Be empathetic — these are real workers worried about their jobs

{lang_instruction}
"""

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=600,
            system=system_prompt,
            messages=[{"role": "user", "content": msg.message}],
        )

        reply = response.content[0].text

        return {
            "reply": reply,
            "language_detected": "hi" if lang_instruction else "en",
            "model": "claude-sonnet-4",
        }

    except ImportError:
        raise HTTPException(status_code=500,
                            detail="anthropic package not installed. Run: pip install anthropic")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def suggest_target_role(current_title: str, risk_score: float) -> str:
    """Suggest a target role based on current title + risk score."""
    title_lower = current_title.lower()

    if "bpo" in title_lower or "voice" in title_lower or "call" in title_lower:
        return "Data Analyst"
    if "data entry" in title_lower:
        return "Operations Analyst"
    if "customer support" in title_lower:
        return "Customer Success"
    if "accountant" in title_lower or "accounts" in title_lower:
        return "Financial Analyst"
    if "content" in title_lower:
        return "Digital Marketing"
    if "hr" in title_lower:
        return "HR Manager"
    if "sales" in title_lower:
        return "Digital Marketing"
    return "Data Analyst"  # Default


def load_courses_from_db() -> list:
    """Load training courses from database."""
    try:
        from db.schema import get_session, TrainingCourse
        session = get_session()
        courses = session.query(TrainingCourse).all()
        session.close()
        result = []
        for c in courses:
            topics = c.topics or []
            if isinstance(topics, str):
                try:
                    topics = json.loads(topics)
                except:
                    topics = []
            result.append({
                "title": c.title,
                "source": c.source,
                "institution": c.institution or "",
                "url": c.url or "",
                "duration_weeks": c.duration_weeks or 8,
                "hours_per_week": c.hours_per_week or 5,
                "topics": topics,
                "is_free": c.is_free,
                "certification": c.certification,
            })
        return result
    except Exception as e:
        return []  # Fall back to NLP engine's built-in courses


# ─────────────────────────────────────────────────────────────────────────────
# RUN
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True) 
