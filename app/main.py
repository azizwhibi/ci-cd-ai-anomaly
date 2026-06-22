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
