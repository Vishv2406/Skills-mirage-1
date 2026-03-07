import os
import requests
import time
import json
from datetime import datetime
from loguru import logger
from dotenv import load_dotenv

load_dotenv()

APIFY_TOKEN = os.getenv("APIFY_API_TOKEN")
ACTOR_ID = os.getenv("APIFY_NAUKRI_ACTOR")

# convert actor format for API
ACTOR_API_ID = ACTOR_ID.replace("/", "~")

CITIES = ["Mumbai", "Delhi", "Bangalore", "Pune"]


def scrape_naukri_apify(max_results_per_city=20):

    all_jobs = []

    for city in CITIES:

        try:

            logger.info(f"🔍 Scraping Naukri for city: {city}")

            run_url = f"https://api.apify.com/v2/acts/{ACTOR_API_ID}/runs?token={APIFY_TOKEN}"

            payload = {
                "location": city,
                "maxItems": max_results_per_city
            }

            response = requests.post(run_url, json=payload)

            run_data = response.json()

            if "data" not in run_data:
                logger.error(f"❌ Apify error response: {run_data}")
                continue

            run_id = run_data["data"]["id"]

            # wait for scraping to finish
            time.sleep(10)

            dataset_url = f"https://api.apify.com/v2/actor-runs/{run_id}/dataset/items?token={APIFY_TOKEN}"

            items = requests.get(dataset_url).json()

            if isinstance(items, list):

                for job in items:

                    all_jobs.append({
                        "title": job.get("title"),
                        "company": job.get("companyName"),
                        "location": job.get("location"),
                        "description": job.get("description"),
                        "source": "naukri"
                    })

                logger.info(f"   ✅ {len(items)} jobs collected")

        except Exception as e:

            logger.error(f"❌ Failed for {city}: {e}")

    logger.info(f"\n📊 Total jobs scraped: {len(all_jobs)}")

    return all_jobs


def save_jobs_to_json(jobs):

    os.makedirs("data/raw", exist_ok=True)

    filename = f"data/raw/naukri_jobs_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(jobs, f, indent=2, ensure_ascii=False)

    logger.info(f"💾 Saved raw jobs → {filename}")

    return filename


def save_jobs_to_db(jobs):

    from db.schema import get_session, JobListing

    session = get_session()

    added = 0

    for job in jobs:

        try:

            entry = JobListing(
                title=job.get("title"),
                company=job.get("company"),
                city=job.get("location"),
                description=job.get("description"),
                source="naukri",
                scraped_at=datetime.utcnow(),
                is_active=True
            )

            session.add(entry)
            added += 1

        except Exception:
            continue

    session.commit()
    session.close()

    logger.info(f"💾 {added} jobs saved to database")

    return added