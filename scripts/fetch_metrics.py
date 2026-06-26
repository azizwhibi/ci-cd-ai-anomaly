# scripts/fetch_metrics.py
import os
import sqlite3
from datetime import datetime
import requests
import pandas as pd

# 1. Load credentials from environment variables
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO = os.getenv("GITHUB_REPO") # Format: "username/repo"

if not GITHUB_TOKEN or not REPO:
    print("Error: Please set GITHUB_TOKEN and GITHUB_REPO in your .env file.")
    exit(1)

# 2. Set up the API request
url = f"https://api.github.com/repos/{REPO}/actions/runs"
headers = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

print(f"Fetching workflow runs from: {url}")

try:
    response = requests.get(url, headers=headers, params={"per_page": 100}, timeout=30)
    response.raise_for_status() # Raise error if login failed or rate limit hit
    
    data = response.json()
    runs = data.get("workflow_runs", [])
    
    if not runs:
        print("No workflow runs found. Make sure you have run the CI pipeline at least once.")
        exit(0)

    rows = []
    for run in runs:
        # Calculate duration manually since GitHub API doesn't always give it directly for completed runs
        created_at = datetime.fromisoformat(run["created_at"].replace("Z", "+00:00"))
        updated_at = datetime.fromisoformat(run["updated_at"].replace("Z", "+00:00"))
        duration_seconds = int((updated_at - created_at).total_seconds())

        rows.append({
            "run_id": run["id"],
            "name": run["name"], # e.g., "CI Pipeline" or "Collect Synthetic Metrics"
            "status": run["status"],
            "conclusion": run.get("conclusion"), # success, failure, cancelled
            "event": run["event"], # push, pull_request, workflow_dispatch
            "branch": run["head_branch"],
            "created_at": run["created_at"],
            "duration_seconds": duration_seconds,
            "html_url": run["html_url"]
        })

    # 3. Save to CSV for easy viewing
    df = pd.DataFrame(rows)
    os.makedirs("data", exist_ok=True)
    csv_path = "data/workflow_runs.csv"
    df.to_csv(csv_path, index=False)
    print(f"Saved {len(df)} records to {csv_path}")

    # 4. Save to SQLite Database (The AIOps Data Lake)
    db_path = "data/metrics.db"
    conn = sqlite3.connect(db_path)
    
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS workflow_runs (
            run_id INTEGER PRIMARY KEY,
            name TEXT,
            status TEXT,
            conclusion TEXT,
            event TEXT,
            branch TEXT,
            created_at TEXT,
            duration_seconds INTEGER,
            html_url TEXT
        )
    """)
    
    # Clear existing data to avoid duplicates on reruns (for this simple lab)
    cursor.execute("DELETE FROM workflow_runs")
    conn.commit()

    for row in rows:
        cursor.execute("""
            INSERT INTO workflow_runs 
            (run_id, name, status, conclusion, event, branch, created_at, duration_seconds, html_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (row["run_id"], row["name"], row["status"], row["conclusion"], row["event"], row["branch"], row["created_at"], row["duration_seconds"], row["html_url"]))

    conn.commit()
    conn.close()
    print(f"Database updated at {db_path}")

except requests.exceptions.RequestException as e:
    print(f"Error fetching data: {e}")
    if "401" in str(e):
        print("-> Did you copy the correct GITHUB_TOKEN?")
