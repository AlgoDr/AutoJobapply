import os
import logging
import requests
from firestore_helper import log_application, get_applications_for_today

logger = logging.getLogger(__name__)

ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID", "77724978")
ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY", "b8a81ab891bed03b1ecc1bb0d1f44dec")
ADZUNA_COUNTRY = "in"

def search_jobs_for_role(role: str):
    url = f"https://api.adzuna.com/v1/api/jobs/{ADZUNA_COUNTRY}/search/1"
    params = {
        "app_id": ADZUNA_APP_ID,
        "app_key": ADZUNA_APP_KEY,
        "results_per_page": 5,
        "what": role,
        "content-type": "application/json"
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        jobs = []
        for job in data.get("results", []):
            jobs.append({
                "id": str(job.get("id")),
                "title": job.get("title"),
                "company": job.get("company", {}).get("display_name", ""),
                "apply_url": job.get("redirect_url")
            })
        return jobs
    except Exception as e:
        logger.error("Adzuna API error: %s", e)
        return []

def apply_to_job(user_id: str, job_id: str) -> bool:
    return log_application(user_id, job_id)

def get_today_application_count(user_id: str) -> int:
    return len(get_applications_for_today(user_id))
