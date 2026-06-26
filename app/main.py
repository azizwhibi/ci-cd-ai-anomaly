from flask import Flask, jsonify, request
from datetime import datetime
import random

app = Flask(__name__)

@app.get("/health")
def health():
    return jsonify({"status": "ok"}), 200

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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

@app.route("/dashboard")
def dashboard():
    csv_path = "data/scored_runs.csv"
    
    # If no data exists yet, show an empty state
    if not os.path.exists(csv_path):
        return render_template("dashboard.html", rows=[], stats={}, chart_path=None)

    try:
        df = pd.read_csv(csv_path)
        
        # Calculate summary statistics for the "cards" at the top
        total_runs = len(df)
        failed_runs = int((df["conclusion"] == "failure").sum()) if "conclusion" in df.columns else 0
        anomalies = int((df["anomaly_label"] == -1).sum())
        avg_duration = round(df["duration_seconds"].mean(), 2)

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
                               chart_path="/static/anomalies.png")
    except Exception as e:
        return f"Error loading data: {str(e)}", 500
