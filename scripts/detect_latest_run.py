# scripts/detect_latest_run.py
import json
import sqlite3
import pandas as pd
import numpy as np
import joblib

print("Loading model and latest data...")

# 1. Load the pre-trained model
model_path = "data/model.joblib"
if not os.path.exists(model_path):
    print(f"Error: Model file {model_path} not found.")
    exit(1)

model = joblib.load(model_path)

# 2. Fetch only the most recent run from the database
db_path = "data/metrics.db"
conn = sqlite3.connect(db_path)
query = """
    SELECT * FROM workflow_runs 
    ORDER BY created_at DESC 
    LIMIT 1
"""
df = pd.read_sql(query, conn)
conn.close()

if df.empty:
    print("Error: No data found in database.")
    exit(1)

latest_run = df.iloc[0]

# 3. Prepare features for the model (must match training exactly!)
features_df = pd.DataFrame([{
    "duration_seconds": latest_run["duration_seconds"],
    "is_failed": int(latest_run.get("conclusion") == "failure"),
    "build_hour": pd.to_datetime(latest_run["created_at"], utc=True).hour,
    "duration_log": np.log1p(latest_run["duration_seconds"])
}])

# 4. Predict and Score
anomaly_label = model.predict(features_df)[0]
anomaly_score = model.decision_function(features_df)[0]

# 5. Output Results as JSON (for GitHub Actions to read)
result = {
    "run_id": int(latest_run["run_id"]),
    "status": latest_run.get("conclusion"),
    "duration_seconds": int(latest_run["duration_seconds"]),
    "is_anomaly": anomaly_label == -1,
    "anomaly_score": float(anomaly_score)
}

print(json.dumps(result))

# Save to file for the artifact upload step
with open("data/latest_detection.json", "w") as f:
    json.dump(result, f, indent=2)

if result["is_anomaly"]:
    print(f"::warning::Anomaly detected in run {result['run_id']}! Score: {anomaly_score:.4f}")
else:
    print("Latest run is normal.")
