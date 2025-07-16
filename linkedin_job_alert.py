import requests
import json
import os
from datetime import datetime
from dotenv import load_dotenv

# === CONFIGURATION ===
load_dotenv()
SERPAPI_KEY = os.getenv("SERPAPI_KEY")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
LOCATION = "United States"
SLEEP_SECONDS = 28800

SEEN_IDS_FILE = 'seen_jobs.txt'

# === SMART ROLE MAPPING ===
ROLE_SYNONYMS = {
    "software engineer": [
        "software engineer", "software developer", "backend engineer", "frontend engineer", "software development engineer",
        "sde", "sde 1", "sde 2", "software engineer 1", "software engineer 2", "software engineer intern",
        "junior developer", "full stack engineer", "full stack developer", "intern"
    ],
    "data analyst": [
        "data analyst", "data analytics", "business analyst", "analytics intern", "data visualization", "data analyst intern"
    ],
    "data scientist": [
        "data scientist", "ml engineer", "machine learning engineer", "ai scientist", "ml intern", "data science intern"
    ],
    "data engineer": [
        "data engineer", "etl engineer", "data pipeline engineer", "big data", "data platform engineer", "data engineer intern"
    ],
    "ai engineer": [
        "ai engineer", "artificial intelligence engineer", "machine learning developer",
        "llm engineer", "deep learning", "ai intern", "ai engineer intern"
    ]
}

# === UTILS ===
def get_all_keywords():
    keywords = []
    for group in ROLE_SYNONYMS.values():
        keywords.extend(group)
    return list(set(keywords))

def load_seen_jobs():
    try:
        with open(SEEN_IDS_FILE, 'r') as f:
            return set(line.strip() for line in f)
    except FileNotFoundError:
        return set()

def save_seen_jobs(seen_ids):
    with open(SEEN_IDS_FILE, 'w') as f:
        for job_id in seen_ids:
            f.write(job_id + '\n')

def fetch_jobs(keywords, seen_jobs):
    url = 'https://serpapi.com/search'
    params = {
        'engine': 'google_jobs',
        'q': " OR ".join(keywords) + " site:linkedin.com/jobs",
        'location': LOCATION,
        'api_key': SERPAPI_KEY
    }

    response = requests.get(url, params=params)
    data = response.json()
    new_jobs = []

    for job in data.get('jobs_results', []):
        job_id = job.get('job_id')
        title = job.get('title', '').lower()

        if job_id and job_id not in seen_jobs and any(keyword in title for keyword in keywords):
            new_jobs.append(job)

    return new_jobs

def send_to_discord(job):
    title = job.get('title', 'N/A')
    company = job.get('company_name', 'N/A')
    location = job.get('location', 'N/A')
    link = job.get('link', '')
    job_type = job.get('detected_extensions', {}).get('employment_type', 'Unknown')
    posted = job.get('detected_extensions', {}).get('posted_at', 'N/A')

    content = {
        "embeds": [{
            "title": f"{title} @ {company}",
            "url": link,
            "description": f"📍 **Location**: {location}\n🕒 **Posted**: {posted}\n💼 **Type**: {job_type}",
            "color": 5814783  # Optional: bluish color
        }]
    }

    headers = {"Content-Type": "application/json"}
    response = requests.post(DISCORD_WEBHOOK_URL, data=json.dumps(content), headers=headers)

    if response.status_code != 204:
        print(f"❌ Failed to send to Discord: {response.status_code} {response.text}")
    else:
        print(f"✅ Sent job to Discord: {title}")

# === MAIN LOOP ===
def run_loop():
    seen_jobs = load_seen_jobs()
    keywords = get_all_keywords()

    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🔍 Checking for new jobs...")
    new_jobs = fetch_jobs(keywords, seen_jobs)

    if new_jobs:
        for job in new_jobs:
            send_to_discord(job)
            seen_jobs.add(job.get('job_id'))
        save_seen_jobs(seen_jobs)
        print(f"🔔 {len(new_jobs)} new job(s) notified!")
    else:
        print("📭 No new jobs found.")

# === ENTRY POINT ===
if __name__ == '__main__':
    run_loop()
