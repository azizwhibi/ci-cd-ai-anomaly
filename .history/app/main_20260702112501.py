from flask import Flask, jsonify, request, render_template, Response
import os
import pandas as pd
import json
from datetime import datetime
import sqlite3
import random
import threading
import time

app = Flask(__name__)

# Path constants
CSV_PATH = "data/scored_runs.csv"
DB_PATH = "data/metrics.db"
WORKFLOW_CSV_PATH = "data/workflow_runs_data.csv"


def read_csv_fallback(csv_path):
    """Read CSV file with error handling, return empty DataFrame if failed."""
    try:
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            if not df.empty:
                return df
    except Exception as e:
        print(f"Error reading {csv_path}: {e}")
    return None


def read_from_database():
    """Read workflow data from SQLite database."""
    try:
        if os.path.exists(DB_PATH):
            conn = sqlite3.connect(DB_PATH)
            query = "SELECT * FROM workflow_runs ORDER BY created_at DESC"
            df = pd.read_sql(query, conn)
            conn.close()
            
            if not df.empty and 'anomaly_label' in df.columns:
                # If anomaly detection has been run on the data
                required_cols = ['run_id', 'anomaly_label', 'duration_seconds', 'conclusion']
                if all(col in df.columns for col in required_cols):
                    return df
            
            # Without anomaly labels, just show raw metrics
            if len(df) > 0:
                df['anomaly_label'] = 1  # default to normal
                df['anomaly_score'] = 0.0
                added = False
                for col in ['status', 'name']:
                    if col in df.columns and 'conclusion' not in df.columns:
                        df = df.rename(columns={'name': 'name', 'status': 'status'})
                        added = True
                return df
    except Exception as e:
        print(f"Error reading database: {e}")
    return None


def get_dashboard_data():
    """Get dashboard data from best available source."""
    # Priority 1 scored_runs.csv (has anomaly labels)
    df = read_csv_fallback(CSV_PATH)
    if df is not None and not df.empty:
        print(f"Loaded {len(df)} records from {CSV_PATH}")
        return df
    
    # Priority 2: Database with full data
    df = read_from_database()
    if df is not None and not df.empty:
        print(f"Loaded {len(df)} records from database")
        return df
    
    # Priority 3: Workflow runs CSV backup
    df = read_csv_fallback(WORKFLOW_CSV_PATH)
    if df is not None and not df.empty:
        print(f"Loaded {len(df)} records from {WORKFLOW_CSV_PATH}")
        return df
    
    return pd.DataFrame()


def auto_refresh_metrics():
    """Background thread that periodically fetches fresh metrics from GitHub API."""
    while True:
        try:
            # Try to run the Python equivalent of fetch_metrics.py inline
            import requests
            ghtoken = os.getenv("GITHUB_TOKEN")
            repo = os.getenv("GITHUB_REPO", "azizwhibi/ci-cd-ai-anomaly")
            
            if not ghtoken:
                # Try GITHUB_TOKEN from environment or default to using fetch_metrics.py script
                pass
            
            url = f"https://api.github.com/repos/{repo}/actions/runs"
            headers = {
                "Authorization": f"Bearer {os.getenv('GITHUB_TOKEN', '')}",
                "Accept": "application/vnd.github+json"
            }
            
            response = requests.get(url, headers=headers, params={"per_page": 100}, timeout=30)
            if response.status_code == 200:
                data = response.json()
                runs = data.get("workflow_runs", [])
                
                if runs:
                    import sqlite3 as _sqlite3
                    import numpy as np
                    
                    os.makedirs("data", exist_ok=True)
                    conn = _sqlite3.connect("data/metrics.db")
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
                            html_url TEXT,
                            test_count INTEGER DEFAULT 0,
                            failed_tests INTEGER DEFAULT 0,
                            duration_log REAL
                        )
                    """)
                    
                    # Delete existing to avoid duplicates and re-insert fresh data (for simplicity)
                    cursor.execute("DELETE FROM workflow_runs WHERE event = 'push' OR event = 'workflow_dispatch' OR event = 'schedule'")
                    
                    rows_to_insert = []
                    for run in runs:
                        try:
                            created_at = datetime.fromisoformat(run["created_at"].replace("Z", "+00:00"))
                            updated_at = datetime.fromisoformat(run["updated_at"].replace("Z", "+00:00"))
                            duration_seconds = int((updated_at - created_at).total_seconds())
                        except Exception:
                            duration_seconds = 0
                        
                        rows_to_insert.append((
                            run["id"],
                            run.get("name", "Unknown"),
                            run.get("status", "completed"),
                            run.get("conclusion", None),
                            run.get("event", None),
                            run.get("head_branch", None),
                            run.get("created_at", datetime.utcnow().isoformat()),
                            duration_seconds,
                            run.get("html_url", ""),
                            0,  # test_count
                            0   # failed_tests
                        ))
                        
                        cursor.execute("""
                            INSERT OR REPLACE INTO workflow_runs 
                            (run_id, name, status, conclusion, event, branch, created_at, duration_seconds, html_url, test_count, failed_tests)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, rows_to_insert[-1])
                    
                    
                    # Insert all the rows
                    cursor.executemany("""
                        INSERT OR REPLACE INTO workflow_runs 
                        (run_id, name, status, conclusion, event, branch, created_at, duration_seconds, html_url, test_count, failed_tests)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, rows_to_insert)
                    
                    conn.commit()
                    conn.close()
        except Exception as e:
            print(f"Auto-refresh error: {e}")
        
        # Wait 5 minutes between refreshes
        time.sleep(300)


def start_auto_refresh():
    """Start the auto-refresh background thread."""
    thread = threading.Thread(target=auto_refresh_metrics, daemon=True)
    thread.start()
    print("Auto-metrics refresh started in background")


@app.get("/health")
def health():
    return jsonify({"status": "ok"}), 200


@app.get("/api/metrics")
def api_metrics():
    """API endpoint that returns fresh metrics data (with optional cache busting)."""
    df = get_dashboard_data()
    
    if df.empty:
        return jsonify({"error": "No metrics available. Run a CI pipeline or trigger the Collect Metrics workflow.", "records": 0}), 404
    
    # Convert to records
    rows = df.to_dict(orient="records")
    
    # Calculate stats
    total_runs = len(df)
    failed_runs = int((df["conclusion"] == "failure").sum()) if "conclusion" in df.columns else 0
    anomalies = int((df["anomaly_label"] == -1).sum()) if "anomaly_label" in df.columns else 0
    avg_duration = round(float(df["duration_seconds"].mean()), 2) if "duration_seconds" in df.columns else 0
    
    return jsonify({
        "records": rows,
        "stats": {
            "total": total_runs,
            "failed": failed_runs,
            "anomalies": anomalies,
            "avg_duration": avg_duration
        },
        "last_updated": datetime.utcnow().isoformat() + "Z"
    })


@app.get("/build-log")
def build_log():
    payload = {
        "build_id": random.randint(1000, 9999),
        "status": random.choice(["success", "success", "failed"]),
        "duration_seconds": random.randint(20, 180),
        "test_count": random.randint(10, 30),
        "failed_tests": random.randint(0, 5),
        "timestamp": datetime.utcnow().isoformat()
    }
    return jsonify(payload)


@app.get("/simulate")
def simulate():
    status = request.args.get("status", "success")
    duration = int(request.args.get("duration", 45))
    failed_tests = int(request.args.get("failed_tests", 0))
    return jsonify({
        "build_id": random.randint(10000, 99999),
        "status": status,
        "duration_seconds": duration,
        "test_count": 20,
        "failed_tests": failed_tests,
        "timestamp": datetime.utcnow().isoformat()
    })


@app.route("/dashboard")
def dashboard():
    try:
        df = get_dashboard_data()
        
        # If no data exists yet, show an empty state
        if df.empty:
            return render_template("dashboard.html", rows=[], stats={"total": 0, "failed": 0, "anomalies": 0, "avg_duration": 0}, chart_path=None)
        
        # Calculate summary statistics for the "cards" at the top
        total_runs = len(df)
        failed_runs = int((df["conclusion"] == "failure").sum()) if "conclusion" in df.columns else 0
        anomalies = int((df["anomaly_label"] == -1).sum()) if "anomaly_label" in df.columns else 0
        avg_duration = round(float(df["duration_seconds"].mean()), 2) if "duration_seconds" in df.columns else 0

        # Get the last 20 runs for the table (so it doesn't get too long)
        recent_runs = df.tail(20).to_dict(orient="records")

        return render_template("dashboard.html", 
                               rows=recent_runs, 
                               stats={
                                   "total": total_runs,
                                   "failed": failed_runs,
                                   "anomalies": anomalies,
                                   "avg_duration": avg_duration
                               }, 
                               chart_path="/static/anomalies.png" if os.path.exists("data/anomalies.png") else None)
    except Exception as e:
        return f"Error loading data: {str(e)}", 500


# Start auto-refresh when the app starts
if __name__ == "__main__":
    start_auto_refresh()
    app.run(host="0.0.0.0", port=5000)