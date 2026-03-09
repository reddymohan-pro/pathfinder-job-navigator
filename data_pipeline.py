import requests
import pandas as pd
import os
import re
from datetime import datetime

# ─────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────
ADZUNA_APP_ID  = "f14082e2"
ADZUNA_APP_KEY = "a90e4e74c96464e54be17538c77eea93"

DATA_DIR       = "data"
RAW_JOBS_PATH  = os.path.join(DATA_DIR, "raw_jobs.csv")
LAST_UPDATED   = os.path.join(DATA_DIR, "last_updated.txt")

# ─────────────────────────────────────────
# HTML CLEANER
# ─────────────────────────────────────────
def clean_html(raw):
    if not raw:
        return ""
    clean = re.sub(r'<[^>]+>', ' ', raw)
    clean = re.sub(r'&[a-zA-Z0-9#]+;', ' ', clean)
    clean = re.sub(r'&#?\w+;', ' ', clean)
    clean = re.sub(r'#\d+;', ' ', clean)
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean

# ─────────────────────────────────────────
# COUNTRY DETECTOR
# ─────────────────────────────────────────
def detect_country(geo):
    if not geo:
        return "Remote"
    geo_lower = geo.lower()
    if any(x in geo_lower for x in [
        "india", "bangalore", "mumbai", "delhi",
        "hyderabad", "chennai", "pune", "kolkata"
    ]):
        return "India"
    elif any(x in geo_lower for x in [
        "usa", "united states", "new york", "san francisco",
        "seattle", "austin", "chicago", "boston", "remote, us"
    ]):
        return "USA"
    else:
        return "Remote"

# ─────────────────────────────────────────
# JOBICY FETCHER
# ─────────────────────────────────────────
def fetch_jobicy_jobs():
    print("\n[Jobicy] Fetching remote jobs...")
    all_jobs = []
    urls = [
        "https://jobicy.com/api/v2/remote-jobs?count=50&industry=data-science",
        "https://jobicy.com/api/v2/remote-jobs?count=50&industry=dev",
        "https://jobicy.com/api/v2/remote-jobs?count=50&tag=python",
        "https://jobicy.com/api/v2/remote-jobs?count=50&tag=machine+learning",
        "https://jobicy.com/api/v2/remote-jobs?count=50&tag=data+analyst",
        "https://jobicy.com/api/v2/remote-jobs?count=50&tag=ai",
    ]
    for url in urls:
        try:
            response = requests.get(url, timeout=10)
            jobs = response.json().get("jobs", [])
            print(f"  Got {len(jobs)} jobs — {url.split('tag=')[-1].split('&')[0]}")
            all_jobs.extend(jobs)
        except Exception as e:
            print(f"  Failed: {e}")

    seen = set()
    unique_jobs = []
    for job in all_jobs:
        if job.get("id") not in seen:
            seen.add(job.get("id"))
            unique_jobs.append(job)

    rows = []
    for job in unique_jobs:
        rows.append({
            "title":       clean_html(job.get("jobTitle", "")),
            "company":     job.get("companyName", ""),
            "location":    job.get("jobGeo", "Remote"),
            "country":     detect_country(job.get("jobGeo", "")),
            "level":       job.get("jobLevel", ""),
            "industry":    job.get("jobIndustry", ""),
            "description": clean_html(job.get("jobDescription", "") or job.get("jobExcerpt", "")),
            "salary_min":  None,
            "salary_max":  None,
            "url":         job.get("url", ""),
            "source":      "jobicy"
        })

    print(f"[Jobicy] Total unique jobs: {len(rows)}")
    return rows

# ─────────────────────────────────────────
# ADZUNA FETCHER
# ─────────────────────────────────────────
def fetch_adzuna_jobs():
    print("\n[Adzuna] Fetching India + USA jobs...")
    all_jobs = []

    searches = [
        {"country": "in", "label": "India"},
        {"country": "us", "label": "USA"},
    ]
    keywords = [
        "data scientist",
        "machine learning engineer",
        "data analyst",
        "python developer",
        "ai engineer",
        "software engineer",
        "data engineer",
        "mlops engineer",
        "business analyst",
        "backend developer",
    ]

    for search in searches:
        for keyword in keywords:
            url = f"https://api.adzuna.com/v1/api/jobs/{search['country']}/search/1"
            params = {
                "app_id":           ADZUNA_APP_ID,
                "app_key":          ADZUNA_APP_KEY,
                "results_per_page": 50,
                "what":             keyword,
                "content-type":     "application/json"
            }
            try:
                response = requests.get(url, params=params, timeout=10)
                jobs = response.json().get("results", [])
                print(f"  Got {len(jobs)} — {search['label']} — '{keyword}'")
                for job in jobs:
                    salary_min = job.get("salary_min", None)
                    salary_max = job.get("salary_max", None)
                    all_jobs.append({
                        "title":       clean_html(job.get("title", "")),
                        "company":     job.get("company", {}).get("display_name", ""),
                        "location":    job.get("location", {}).get("display_name", ""),
                        "country":     search["label"],
                        "level":       "",
                        "industry":    job.get("category", {}).get("label", ""),
                        "description": clean_html(job.get("description", "")),
                        "salary_min":  salary_min,
                        "salary_max":  salary_max,
                        "url":         job.get("redirect_url", ""),
                        "source":      "adzuna"
                    })
            except Exception as e:
                print(f"  Failed — {search['label']} — {keyword}: {e}")

    print(f"[Adzuna] Total jobs: {len(all_jobs)}")
    return all_jobs

# ─────────────────────────────────────────
# MAIN PIPELINE
# ─────────────────────────────────────────
def run_pipeline():
    print("=" * 55)
    print("JOB NAVIGATOR — DATA PIPELINE")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 55)

    os.makedirs(DATA_DIR, exist_ok=True)

    # Fetch from both sources
    jobicy_jobs  = fetch_jobicy_jobs()
    adzuna_jobs  = fetch_adzuna_jobs()

    # Combine
    all_jobs = jobicy_jobs + adzuna_jobs
    df = pd.DataFrame(all_jobs)

    # Deduplicate
    before = len(df)
    df.drop_duplicates(subset=["title", "company"], inplace=True)
    after = len(df)
    print(f"\nDeduplication: {before} → {after} jobs")

    # Save
    df.to_csv(RAW_JOBS_PATH, index=False)

    # Save timestamp
    with open(LAST_UPDATED, "w") as f:
        f.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    print(f"\nSaved {len(df)} jobs to {RAW_JOBS_PATH}")
    print(f"\nCountry distribution:")
    print(df["country"].value_counts().to_string())
    print(f"\nSource distribution:")
    print(df["source"].value_counts().to_string())
    print(f"\nSalary data available: {df['salary_min'].notna().sum()} jobs")

    return df

if __name__ == "__main__":
    run_pipeline()  