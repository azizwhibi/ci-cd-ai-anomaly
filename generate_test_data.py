import sqlite3, os, random, time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.ensemble import IsolationForest
import joblib

os.makedirs("data", exist_ok=True)
db_path = "data/metrics.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS workflow_runs (
        run_id INTEGER PRIMARY KEY, name TEXT, status TEXT, conclusion TEXT,
        event TEXT, branch TEXT, created_at TEXT, duration_seconds INTEGER,
        html_url TEXT, test_count INTEGER DEFAULT 0, failed_tests INTEGER DEFAULT 0
    )
""")

# Génère 30 runs factices (majorité normaux, quelques anomalies)
now = datetime.utcnow()
for i in range(30):
    is_anomaly_case = random.random() < 0.15
    status = "failed" if is_anomaly_case and random.random() < 0.5 else "success"
    duration = random.choice([180, 220, 900, 1100]) if is_anomaly_case else random.randint(30, 60)
    created_at = (now - timedelta(hours=i)).strftime("%Y-%m-%dT%H:%M:%SZ")
    cursor.execute("""
        INSERT OR REPLACE INTO workflow_runs
        (run_id, name, status, conclusion, event, branch, created_at, duration_seconds, html_url, test_count, failed_tests)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (int(time.time()) - i, "CI Pipeline", "completed", status, "push", "main",
          created_at, duration, f"https://github.com/azizwhibi/ci-cd-ai-anomaly/actions/runs/{i}",
          20, 0 if status == "success" else random.randint(1, 5)))
conn.commit()

df = pd.read_sql("SELECT * FROM workflow_runs", conn)
conn.close()

df["is_failed"] = df["conclusion"].map({"success": 0, "failed": 1}).fillna(0).astype(int)
df["created_at_parsed"] = pd.to_datetime(df["created_at"], utc=True)
df["build_hour"] = df["created_at_parsed"].dt.hour
df["duration_log"] = np.log1p(df["duration_seconds"])

features = ["duration_seconds", "is_failed", "build_hour", "duration_log"]
X = df[features]

model = IsolationForest(n_estimators=100, contamination=0.15, random_state=42)
model.fit(X)
joblib.dump(model, "data/model.joblib")

df["anomaly_label"] = model.predict(X)
df["anomaly_score"] = model.decision_function(X)
df.to_csv("data/scored_runs.csv", index=False)
print(f"✅ {len(df)} runs générés, dont {(df['anomaly_label']==-1).sum()} anomalies détectées.")
