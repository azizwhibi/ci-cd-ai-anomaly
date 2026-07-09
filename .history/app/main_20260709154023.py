from flask import Flask, jsonify, request, render_template, Response
import os
import pandas as pd
import json
from datetime import datetime
import sqlite3
import random
import threading
import time
import numpy as np

app = Flask(__name__)

# Path constants
CSV_PATH = "data/scored_runs.csv"
DB_PATH = "data/metrics.db"
WORKFLOW_CSV_PATH = "data/workflow_runs_data.csv"

# Default GitHub config - can be overridden via environment variables
GITHUB_REPO = os.getenv("GITHUB_REPO", "azizwhibi/ci-cd-ai-anomaly")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")


def fetch_from_github_api():
    """Fetch workflow runs directly from GitHub API. Returns DataFrame or None."""
    try:
        import requests
        
        url = f"https://api.github.com/repos/{GITHUB_REPO}/actions/runs"
        headers = {
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json"
        } if GITHUB_TOKEN else {"Accept": "application/vnd.github+json"}
        
        response = requests.get(url, headers=headers, params={"per_page": 100}, timeout=30)
        if response.status_code == 200:
            data = response.json()
            runs = data.get("workflow_runs", [])
            return runs
        elif response.status_code == 404:
            print(f"Warning: Repository '{GITHUB_REPO}' not found or is private.")
        else:
            print(f"Warning: GitHub API returned status {response.status_code}: {response.text}")
    except Exception as e:
        print(f"Error fetching from GitHub API: {e}")
    return None


def runs_to_dataframe(runs):
    """Convert raw GitHub API runs into a standardized DataFrame with anomaly detection."""
    if not runs:
        return pd.DataFrame()
    
    rows = []
    for run in runs:
        try:
            created_at = datetime.fromisoformat(run["created_at"].replace("Z", "+00:00"))
            updated_at = datetime.fromisoformat(run["updated_at"].replace("Z", "+00:00"))
            duration_seconds = int((updated_at - created_at).total_seconds())
        except Exception:
            duration_seconds = 0
        
        rows.append({
            "run_id": run.get("id", 0),
            "name": run.get("name", "Unknown"),
            "status": run.get("status", "unknown"),
            "conclusion": run.get("conclusion"),
            "event": run.get("event", "unknown"),
            "branch": run.get("head_branch", "unknown"),
            "created_at": run.get("created_at", datetime.utcnow().isoformat()),
            "duration_seconds": duration_seconds,
            "html_url": run.get("html_url", ""),
            "test_count": 0,
            "failed_tests": 0,
        })
    
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    
    # Standardize columns
    required_cols = ['run_id', 'name', 'status', 'conclusion', 'event', 'branch', 
                     'created_at', 'duration_seconds', 'html_url', 'test_count', 'failed_tests']
    for col in required_cols:
        if col not in df.columns:
            if col == 'html_url':
                df[col] = ''
            elif df['run_id'].dtype.name.startswith('int'):
                df[col] = 0
            else:
                df[col] = ''
    
    # Add anomaly scoring using Isolation Forest (in-memory, no file dependency)
    if len(df) >= 3:
        try:
            from sklearn.ensemble import IsolationForest
            
            # Engineer features for anomaly detection
            df['created_at_parsed'] = pd.to_datetime(df['created_at'], utc=True, errors='coerce')
            df['build_hour'] = df['created_at_parsed'].dt.hour
            df['is_failed'] = df['conclusion'].map({'success': 0, 'failure': 1}).fillna(0).astype(int)
            df['duration_log_feat'] = np.log1p(df['duration_seconds'])
            
            features = ["duration_seconds", "is_failed", "build_hour", "duration_log_feat"]
            X = df[features]
            
            # Train Isolation Forest model (in-memory, no file saving)
            model = IsolationForest(n_estimators=100, contamination=0.15, random_state=42)
            model.fit(X)
            
            df["anomaly_label"] = model.predict(X)  # -1 for anomaly, 1 for normal
            df["anomaly_score"] = model.decision_function(X)
        except Exception as e:
            print(f"Anomaly detection warning: {e}")
            df["anomaly_label"] = 1
            df["anomaly_score"] = 0.0
    else:
        # Not enough data for anomaly detection
        df["anomaly_label"] = 1
        df["anomaly_score"] = 0.0
    
    return df


def read_csv_fallback(csv_path):
    """Read CSV file with error handling, return empty DataFrame if failed."""
    try:
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            if not df.empty:
                print(f"Loaded {len(df)} records from {csv_path}")
                # Normalize anomaly columns for CSV data
                if 'anomaly_label' in df.columns:
                    df['anomaly_label'] = df['anomaly_label'].apply(lambda x: -1 if (isinstance(x, (int, float)) and int(x) == -1) else 1)
                if 'conclusion' not in df.columns and 'status' in df.columns:
                    df['conclusion'] = df['status'].map({'success': 'success', 'failure': 'failure'})
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
                required_cols = ['run_id', 'anomaly_label', 'duration_seconds', 'conclusion']
                if all(col in df.columns for col in required_cols):
                    return df
            
            # Without anomaly labels, add defaults
            if len(df) > 0:
                df['anomaly_label'] = 1
                df['anomaly_score'] = 0.0
                if 'conclusion' not in df.columns and 'status' in df.columns:
                    df['conclusion'] = df['status']
                return df
    except Exception as e:
        print(f"Error reading database: {e}")
    return None


def get_dashboard_data():
    """Get dashboard data - tries multiple sources, falls back to GitHub API."""
    # Priority 1: scored_runs.csv (has anomaly labels from git)
    df = read_csv_fallback(CSV_PATH)
    if df is not None and not df.empty:
        return normalize_dashboard_df(df)
    
    # Priority 2: Database with full data
    df = read_from_database()
    if df is not None and not df.empty:
        return normalize_dashboard_df(df)
    
    # Priority 3: Workflow runs CSV backup
    df = read_csv_fallback(WORKFLOW_CSV_PATH)
    if df is not None and not df.empty:
        return normalize_dashboard_df(df)
    
    # Priority 4 (PRIMARY FOR RENDER): Fetch fresh from GitHub API
    print("No local data found. Fetching fresh metrics from GitHub API...")
    runs = fetch_from_github_api()
    if runs and len(runs) > 0:
        df = runs_to_dataframe(runs)
        if not df.empty:
            # Save fetched data to disk for potential offline use
            try:
                os.makedirs("data", exist_ok=True)
                df.to_csv(CSV_PATH, index=False)
                # Also save to database
                conn = sqlite3.connect(DB_PATH)
                df_clean = df.drop(columns=['anomaly_label', 'anomaly_score', 'created_at_parsed', 'build_hour', 'is_failed', 'duration_log_feat'], errors='ignore')
                df_clean.to_sql('workflow_runs', conn, if_exists='replace', index=False)
                conn.close()
            except Exception as e:
                print(f"Warning: Could not save data to disk: {e}")
            return normalize_dashboard_df(df)
    
    return pd.DataFrame()


def normalize_dashboard_df(df):
    """Ensure DataFrame has the expected column format for the dashboard."""
    if df.empty:
        return df
    
    # Ensure anomaly_label is in standard format (-1 or 1)
    if 'anomaly_label' not in df.columns:
        df['anomaly_label'] = 1
    else:
        df['anomaly_label'] = df['anomaly_label'].apply(
            lambda x: -1 if (isinstance(x, (int, float)) and int(x) == -1) or 
                                 (isinstance(x, str) and ('-1' in str(x))) else 1
        )
    
    # Ensure anomaly_score exists
    if 'anomaly_score' not in df.columns:
        df['anomaly_score'] = 0.0
    
    # Ensure conclusion column exists for status display
    if 'conclusion' not in df.columns:
        if 'status' in df.columns:
            df['conclusion'] = df['status'].map({
                'success': 'success', 
                'failure': 'failure',
                'completed': 'success'
            }).fillna(df['status'])
    
    # Sort by created_at descending (newest first)
    if 'created_at' in df.columns:
        try:
            df = df.sort_values('created_at', ascending=False).reset_index(drop=True)
        except Exception:
            pass
    
    return df


def _background_data_fetcher():
    """Background thread that periodically fetches fresh metrics from GitHub API and writes to disk."""
    while True:
        try:
            runs = fetch_from_github_api()
            if runs and len(runs) > 0:
                df = runs_to_dataframe(runs)
                if not df.empty:
                    os.makedirs("data", exist_ok=True)
                    df.to_csv(CSV_PATH, index=False)
        except Exception as e:
            print(f"Background fetch error: {e}")
        time.sleep(300)  # 5 minutes


def start_auto_refresh():
    """Start the auto-refresh background thread."""
    if GITHUB_TOKEN:
        thread = threading.Thread(target=_background_data_fetcher, daemon=True)
        thread.start()
        print("Auto-metrics refresh started in background")
    else:
        print("GITHUB_TOKEN not set - skipping background auto-refresh (will fetch on-demand instead)")


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


# Gunicorn entry point - handles workers gracefully within Gunicorn
def create_app():
    """Application factory pattern for Gunicorn compatibility."""
    return app

# Allow running with gunicorn via: gunicorn --config gunicorn.conf.py app.main:create_app()
# Or directly: gunicorn --bind 0.0.0.0:8000 --workers 3 app.main:app
