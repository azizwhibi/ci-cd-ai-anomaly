# scripts/train_model.py
import os
import sqlite3
import pandas as pd
import numpy as np
import joblib # To save the trained model
import matplotlib.pyplot as plt # To visualize the results
from sklearn.ensemble import IsolationForest

print("Loading data from SQLite database...")

# 1. Connect to your database and load into a Pandas DataFrame
db_path = "data/metrics.db"
conn = sqlite3.connect(db_path)
query = "SELECT * FROM workflow_runs"
df = pd.read_sql(query, conn)
conn.close()

if df.empty:
    print("Error: No data found in database. Run fetch_metrics.py first.")
    exit(1)

print(f"Loaded {len(df)} records. Preparing features...")

# 2. Feature Engineering (Making the data AI-ready)
# The model needs numbers, not text. We convert 'conclusion' to 0 or 1.
df["is_failed"] = df["conclusion"].map({"success": 0, "failure": 1}).fillna(0).astype(int)

# We also want to know what time of day the build happened (hour 0-23)
df["created_at"] = pd.to_datetime(df["created_at"], utc=True)
df["build_hour"] = df["created_at"].dt.hour

# Log transform for duration helps the model handle extreme outliers better
df["duration_log"] = np.log1p(df["duration_seconds"])

# 3. Select the features the model will look at
features = ["duration_seconds", "is_failed", "build_hour", "duration_log"]
X = df[features]

print("Training Isolation Forest model...")

# 4. Initialize and Train the Model
# contamination=0.1 means we expect ~10% of our data to be anomalous
model = IsolationForest(
    n_estimators=100,      # How many "trees" in the forest
    contamination=0.1,     # Expected percentage of anomalies
    random_state=42        # For reproducibility
)

# Fit the model to our data (This is where the learning happens)
model.fit(X)

# 5. Generate Scores and Labels
# predict() returns 1 for normal, -1 for anomaly
df["anomaly_label"] = model.predict(X)
# decision_function() gives a score: lower/more negative means more anomalous
df["anomaly_score"] = model.decision_function(X)

print("Saving results...")

# Save the trained model so we can use it later in Week 7/8
joblib.dump(model, "data/model.joblib")

# Save the scored data to CSV for visualization
output_path = "data/scored_runs.csv"
df.to_csv(output_path, index=False)
print(f"Saved labeled data to {output_path}")

# --- Visualization ---
plt.figure(figsize=(12, 6))
colors = df["anomaly_label"].map({1: "#4dd4a0", -1: "#ff7c98"}) # Green for normal, Red for anomaly
plt.scatter(df.index, df["duration_seconds"], c=colors, s=50)
plt.title("CI/CD Pipeline Anomalies Detected by Isolation Forest")
plt.xlabel("Run Index")
plt.ylabel("Duration (seconds)")
plt.axhline(y=df["duration_seconds"].quantile(0.9), color='gray', linestyle='--', label="Top 10% Duration Threshold")
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()

chart_path = "data/anomalies.png"
plt.savefig(chart_path, dpi=150)
print(f"Saved visualization to {chart_path}")

# Print a summary of what was found
anomalies = df[df["anomaly_label"] == -1]
if not anomalies.empty:
    print("\n--- Anomalous Runs Detected ---")
    print(anomalies[["run_id", "status", "duration_seconds", "anomaly_score"]])
else:
    print("\nNo significant anomalies detected in this dataset. Try generating more diverse data!")
