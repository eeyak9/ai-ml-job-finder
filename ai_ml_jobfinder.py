import os
import csv
import json
import smtplib
import requests
from datetime import datetime, timezone


# ---------------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------------

#KEYWORD SEARCH
INCLUDE_KEYWORDS = [
    "machine learning",
    "ml engineering",
    "ai engineering",
    "artificial intelligence",
    "nlp",
    "computer vision",
    "data scientist",
    "llm",
    "research scientist",
]

EXCLUDE_KEYWORDS = [
    "senior",
    "staff",
    "principal",
    "lead",
    "director",
    "head of",
    "10+ years",
    "8+ years",
    "7+ years",
]

JUNIOR_KEYWORDS = [
    "junior",
    "entry-level",
    "entry level",
    "graduate",
    "new grad",
    "early career",
    "associate",
    "0-2 years",
    "1-3 years",
]
REQUIRE_JUNIOR_KEYWORDS = False

UK_LOCATION_KEYWORDS = [
        "uk", "u.k.", "united kingdom", "england", "scotland", "wales",
    "northern ireland", "london", "manchester", "birmingham", "edinburgh",
    "glasgow", "bristol", "leeds", "cambridge", "oxford", "belfast",
    "cardiff", "reading", "sheffield", "liverpool", "newcastle","nottingham",
]

INCLUDE_WORLDWIDE_REMOTE = True
WORLDWIDE_LOCATION_KEYWORDS = ["worldwide", "anywhere", "global", "remote"]
 
def is_uk_job(location):
    loc = (location or "").lower()
    if any(kw in loc for kw in UK_LOCATION_KEYWORDS):
        return True
    if INCLUDE_WORLDWIDE_REMOTE and any(kw in loc for kw in WORLDWIDE_LOCATION_KEYWORDS):
        return True
    return False
 

SEEN_FILE = "seen_job.json"
OUTPUT_CSV = "ai_ml_jobs.csv"

# ---------------------------------------------------------------------------
# DATA FETCHING
# ---------------------------------------------------------------------------

def fetch_remotive():
    jobs = []
    try:
        resp = requests.get(
            "https://remotive.com/api/remote-jobs",
            params={"category": "software-dev"},
            timeout=20,
        )
        resp.raise_for_status()
        for j in resp.json().get("jobs", []):
            jobs.append({
                "id":f"remotive-{j.get("id")}",
                "title":j.get("title",""),
                "company":j.get("company_name", ""),
                "location":j.get("candidate_required_location", ""),
                "url":j.get("url", ""),
                "description":j.get("description", ""),
                "source":"Remotive",
                "posted":j.get("publication_date", ""),
            })
    except requests.RequestException as e:
        print(f"[Remotive] fetch failed: {e}")
    return jobs

def fetch_arbeitnow():
    jobs = []
    try:
        resp = requests.get("https://www.arbeitnow.co.uk/api/job-board-api", timeout=20)
        resp.raise_for_status()
        for j in resp.json().get("data", []):
            jobs.append({
                "id": f"arbeitnow-{j.get('slug')}",
                "title": j.get("title", ""),
                "company": j.get("company_name", ""),
                "location": j.get("location", ""),
                "url": j.get("url", ""),
                "description": j.get("description", ""),
                "source": "Arbeitnow",
                "posted": j.get("created_at", ""),
            })
    except requests.RequestException as e:
        print(f"[Arbeitnow] fetch failed: {e}")
    return jobs

# ---------------------------------------------------------------------------
# FILTERING
# ---------------------------------------------------------------------------

def matches_filters(job):
    text = f"{job['title']}{job['description']}".lower()

    if not any(kw in text for kw in INCLUDE_KEYWORDS):
        return False

    if any(kw in text for kw in EXCLUDE_KEYWORDS):
        return False

    if REQUIRE_JUNIOR_KEYWORDS and not any(kw in text for kw in JUNIOR_KEYWORDS):
        return False

    return True

# ---------------------------------------------------------------------------
# Persistence 
# ---------------------------------------------------------------------------

def load_seen():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r") as f:
            return set(json.load(f))
    return set()


def save_seen(seen_ids):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen_ids), f)


def append_to_csv(jobs):
    file_exists = os.path.exists(OUTPUT_CSV)
    with open(OUTPUT_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["found_at", "title", "company", "location", "source", "url"]
        )
        if not file_exists:
            writer.writeheader()
        for j in jobs:
            writer.writerow({
                "found_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "title": j["title"],
                "company": j["company"],
                "location": j["location"],
                "source": j["source"],
                "url": j["url"],
            })


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    print("Fetching jobs from free sources...")
    all_jobs = fetch_remotive() + fetch_arbeitnow()
    print(f"Fetched {len(all_jobs)} total postings.")

    seen = load_seen()
    new_matches = []

    for job in all_jobs:
        if job["id"] in seen:
            continue
        seen.add(job["id"])
        if matches_filters(job):
            new_matches.append(job)

    save_seen(seen)

    if new_matches:
        append_to_csv(new_matches)
        print(f"Found {len(new_matches)} new matching jobs. Saved to {OUTPUT_CSV}.")
        for j in new_matches:
            print(f" - {j['title']} @ {j['company']} ({j['source']}) -> {j['url']}")
    else:
        print("No new matching jobs this run.")


if __name__ == "__main__":
    main()
