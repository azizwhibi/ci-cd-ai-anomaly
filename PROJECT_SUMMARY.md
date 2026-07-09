# CI/CD AI Anomaly Detection Platform - Project Summary

## Overview

A comprehensive AIOps platform that combines CI/CD automation with machine learning-based anomaly detection to monitor, analyze, and identify unusual patterns in pipeline build and deployment logs. The system automatically collects metrics from GitHub Actions, trains isolation forest models to detect anomalies, and provides an interactive dashboard for visualization and monitoring.

**Repository**: [azizwhibi/ci-cd-ai-anomaly](https://github.com/azizwhibi/ci-cd-ai-anomaly)  
**Badge**: ![CI Pipeline](https://github.com/azizwhibi/ci-cd-ai-anomaly/actions/workflows/ci.yml/badge.svg)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     GitHub Actions Workflows                     │
│                                                                  │
│  ┌──────────────┐   ┌──────────────────┐   ┌─────────────────┐ │
│  │  CI Pipeline  │   │ Collect Metrics  │   │ Detect Anomalies│ │
│  │  (ci.yml)     │──▶│  (collect-metrics│   │  (detect-anoma- │ │
│  │               │   │   .yml)           │   │   lies.yml)     │ │
│  └──────────────┘   └────────┬─────────┘   └────────┬────────┘ │
│                              │                       │           │
│                     Generates │  Fetches GitHub API   │  Triggers  │
│                     Test &    │  metrics & synthetic   │ on CI     │
│                     Docker    │  data                  │ complete  │
│                             │                       │           │
└──────────────┬───────────────┴───────────────────────┼───────────┘
               │                                       │
               ▼                                       ▼
┌──────────────────────────┐       ┌──────────────────────────────────────┐
│      Data Layer          │       │        ML / Anomaly Detection         │
│                          │       │                                      │
│  • data/metrics.db       │       │  • scripts/train_model.py            │
│    (SQLite database)     │       │    - Isolation Forest training       │
│  • data/scored_runs.csv  │◀─────▶│    - Feature engineering             │
│  • data/anomalies.png    │       │    - Anomaly scoring & labeling      │
│  • data/model.joblib     │       │  • scripts/detect_latest_run.py      │
│  • data/latest_detection │       │    - Real-time run scoring           │
└──────────────┬───────────┘       └──────────────────────────────────────┘
               │
               ▼
┌──────────────────────────┐       ┌──────────────────────────────────────┐
│     Metrics Collection   │       │        Dashboard & API Server         │
│                          │       │                                      │
│  • scripts/fetch_metrics.py◀─────│  • app/main.py (Flask)               │
│    - GitHub Actions API  │       │    - REST API endpoints              │
│    - SQLite persistence  │       │    - Interactive dashboard           │
│    - Synthetic data gen. │       │    - Auto-refresh (5 min intervals)  │
└──────────────────────────┘       └──────────────────────────────────────┘
```

---

## Features

| Feature | Description |
|---------|-------------|
| **CI/CD Pipeline Monitoring** | Tracks build durations, success/failure rates, and test results from GitHub Actions |
| **AI-Powered Anomaly Detection** | Uses Isolation Forest algorithm to identify unusual pipeline behavior |
| **Feature Engineering** | Automatic feature extraction including duration, failure status, build hour, log-transformed metrics |
| **Interactive Dashboard** | Real-time visualization with stats cards, data tables, and anomaly charts |
| **Auto-Refresh API** | Background thread fetches fresh metrics from GitHub API every 5 minutes |
| **RESTful API** | JSON endpoints for programmatic access to metrics and dashboard data |
| **Docker Deployment** | Containerized application with docker-compose for easy deployment |
| **Automated Workflows** | Schedule-based metric collection (every 6 hours) and trigger-based anomaly detection |
| **Model Persistence** | Trained ML models saved as `.joblib` files for reuse in production |

---

## Tech Stack

### Backend
- **Python 3.10** - Primary programming language
- **Flask 3.1.3** - Web framework and API server
- **FastAPI-compatible JSON** endpoints

### Machine Learning & Data Science
- **scikit-learn 1.7.2** - Isolation Forest anomaly detection algorithm
- **pandas 2.3.3** - Data manipulation and analysis
- **numpy 2.2.6** - Numerical computing
- **joblib 1.5.3** - Model serialization/deserialization
- **matplotlib 3.10.9** - Data visualization (anomaly distribution charts)

### DevOps & CI/CD
- **GitHub Actions** - Workflow automation, CI/CD pipelines
- **Docker** - Containerization and deployment
- **docker-compose** - Multi-container orchestration

### Data Storage
- **SQLite** - Lightweight embedded database for metrics storage (`data/metrics.db`)
- **CSV files** - Persisted dashboard data (`data/scored_runs.csv`, `data/workflow_runs_data.csv`)

### HTTP & APIs
- **requests 2.34.2** - GitHub REST API client
- **blinker / Werkzeug / Jinja2** - Flask ecosystem components

---

## Project Structure

```
ci-cd-ai-anomaly/
├── .github/                          # GitHub Actions CI/CD workflows
│   ├── workflows/
│   │   ├── ci.yml                    # Main CI pipeline (test + Docker build)
│   │   ├── collect-metrics.yml       # Scheduled metric collection & synthetic data
│   │   ├── detect-anomalies.yml      # ML anomaly detection on completed runs
│   │   └── deploy-data.yml           # Dashboard data synchronization
│   └── workflows/collect-metrics.yml # Metrics with built-in ML pipeline
├── .gitignore                        # Git ignore rules (data files, logs, etc.)
├── app/                              # Flask web application
│   ├── __init__.py                   # Package initialization
│   ├── main.py                       # Main Flask application (284 lines)
│   └── templates/
│       └── dashboard.html            # AIOps Dashboard UI (300 lines)
├── ci_cd_ai_anomaly.egg-info/        # Python package metadata
├── data/                             # Runtime data directory
│   ├── metrics.db                    # SQLite database (runtime-generated)
│   ├── scored_runs.csv               # ML-scored pipeline runs (version-controlled)
│   ├── anomalies.png                 # Anomaly visualization chart (version-controlled)
│   ├── model.joblib                  # Trained Isolation Forest model (version-controlled)
│   └── latest_detection.json         # Latest anomaly detection result
├── scripts/                          # Utility and ML scripts
│   ├── bootstrap.sh                  # Environment bootstrapping script
│   ├── fetch_metrics.py              # GitHub API metrics collector (99 lines)
│   ├── train_model.py                # Isolation Forest training pipeline (91 lines)
│   └── detect_latest_run.py          # Real-time anomaly detection (89 lines)
├── tests/                            # Test suite
│   └── test_app.py                   # Flask app unit tests (20 lines)
├── Dockerfile                        # Container build definition
├── docker-compose.yml                # Multi-container orchestration
├── requirements.txt                  # Python dependency list (37 packages)
├── setup.py                          # Python package configuration
├── Vagrantfile                       # Vagrant VM configuration
└── README.md                         # Project documentation
```

---

## CI/CD Workflows

### 1. CI Pipeline (`ci.yml`)

**Trigger**: Push or pull request to `main` branch  
**Purpose**: Standard continuous integration checks

| Step | Description |
|------|-------------|
| Checkout | Uses `actions/checkout@v4` |
| Python Setup | Configures Python 3.10 via `actions/setup-python@v5` |
| Dependencies | Installs requirements from `requirements.txt` |
| Run Tests | Executes `pytest -v tests/test_app.py` with `PYTHONPATH=.` |
| Docker Build | Builds image tagged as `anomaly-detector:{commit_sha}` |

**Concurrency**: Groups by `ci-{ref}`, cancels in-progress runs for same branch.  
**Timeout**: 10 minutes maximum.

---

### 2. Collect Synthetic Metrics (`collect-metrics.yml`)

**Trigger**: Manual dispatch OR cron schedule (every 6 hours)  
**Purpose**: Generate and collect pipeline metrics from GitHub API or synthetic data

**Process Flow**:
1. **Generate Synthetic Metrics** - Creates randomized build data simulating CI runs:
   - Random status (success/failed with weighted probability toward success)
   - Variable durations: 35s (fast), 42s (normal), 145s (slow), 170s (very slow)
   - Failed tests count correlated with failure status

2. **Upload Artifact** - Saves `artifacts/synthetic_metrics.csv` as GitHub Actions artifact

3. **Merge into Database** - Python heredoc script that:
   - Reads synthetic CSV and merges into SQLite database (`data/metrics.db`)
   - Standardizes column names to match `workflow_runs` schema
   - Creates/reuses table with columns: run_id, name, status, conclusion, event, branch, created_at, duration_seconds, html_url, test_count, failed_tests, duration_log

4. **Train Model & Save Results** - Retrains Isolation Forest on all data and generates `scored_runs.csv`

5. **Upload Dashboard Data Artifact** - Packages `data/scored_runs.csv` and `data/metrics.db` for downstream workflows

---

### 3. Detect CI Anomalies (`detect-anomalies.yml`)

**Trigger**: Completion of any workflow (specifically "CI Pipeline")  
**Purpose**: ML-based anomaly detection on the latest pipeline runs

**Process Flow**:
1. **Checkout Code** with persisted credentials for write access

2. **Install Dependencies** - pandas, scikit-learn, joblib, requests, numpy, matplotlib

3. **Fetch Latest Metrics from GitHub API** (`scripts/fetch_metrics.py`):
   - Authenticates using `GITHUB_TOKEN` secret
   - Queries `$REPO/actions/runs` endpoint for up to 100 recent runs
   - Calculates duration in seconds from created_at/updated_at timestamps
   - Saves to both CSV and SQLite database

4. **Train Model on All Fetched Data** (`scripts/train_model.py`):
   - Feature engineering: `is_failed`, `build_hour`, `duration_log` (natural log of duration + 1)
   - Trains Isolation Forest with default `script/detect_latest_run.py` parameters

5. **Detect Anomalies in Latest Run** (`scripts/detect_latest_run.py`):
   - Loads trained model from `data/model.joblib`
   - Scores most recent database entry
   - Outputs JSON result: `{run_id, status, duration_seconds, is_anomaly, anomaly_score}`

6. **Handle Anomaly Warning**: Displays GitHub Actions error annotation if anomaly detected

7. **Commit and Push Updated Data** to repository for dashboard persistence

---

### 4. Deploy Dashboard Data (`deploy-data.yml`)

**Trigger**: Manual dispatch OR daily cron (midnight UTC)  
**Purpose**: Synchronize local data files with the git repository

- Checks for uncommitted changes in `data/` directory
- Commits and pushes any changes using GitHub Actions bot identity
- Acts as periodic backup/persistence mechanism for ML artifacts and metrics

---

## Application Code

### Flask Backend (`app/main.py`)

**Port**: 5000  
**Auto-refresh Background Thread**: Periodically fetches fresh metrics from GitHub API every 300 seconds (5 minutes)

#### Endpoints

| Endpoint | Method | Description | Response Format |
|----------|--------|-------------|-----------------|
| `/health` | GET | Health check for monitoring/load balancers | `{"status": "ok"}` |
| `/api/metrics` | GET | Dashboard metrics data (primary API) | JSON with records array + stats object |
| `/build-log` | GET | Simulated build log data (for testing/demo) | Randomized JWT-like mock response |
| `/simulate?status=X&duration=Y&failed_tests=Z` | GET | Simulate pipeline run with specific parameters | Controlled response with provided values |
| `/dashboard` | GET | HTML dashboard page with embedded data | Full HTML page rendering |

#### `get_dashboard_data()` - Data Priority System

The Flask app implements a cascading data source priority:

1. **Priority 1**: `data/scored_runs.csv` (contains ML anomaly labels and scores)
2. **Priority 2**: SQLite database (`data/metrics.db`, queries `workflow_runs` table)
3. **Priority 3**: `data/workflow_runs_data.csv` (backup CSV source)

#### `auto_refresh_metrics()` - Background Auto-Refresh

Running as a daemon thread, this function:
1. Calls GitHub REST API for recent workflow runs
2. Parses timestamps to calculate build duration in seconds
3. Creates/recreates the SQLite schema if needed
4. Clears and re-inserts push/workflow_dispatch/schedule events (avoids duplicates)
5. Handles authentication via `GITHUB_TOKEN` environment variable

---

### Dashboard UI (`app/templates/dashboard.html`)

**Theme**: Dark mode modern dashboard design using CSS custom properties

#### Layout Components:
1. **Header Bar** - Title ("AIOps Anomaly Dashboard") with live status indicator and manual refresh button
2. **Stats Cards (4-column grid)**:
   | Card | Content | Styling |
   |------|---------|---------|
   | Total Runs | Count of all workflow runs | Standard white text |
   | Failed Builds | Count where conclusion = "failure" | Red (`#ef4444`) |
   | Anomalies Detected | Count where anomaly_label = -1 | Yellow (`#fbbf24`) |
   | Avg Duration | Mean build duration in seconds (e.g. "93s") | Standard white text |

3. **Chart Section** - Displays anomaly distribution visualization from `static/anomalies.png`
   - Uploaded by CI workflow as artifact and served at `/static/anomalies.png`

4. **Data Table**:
   | Column | Source Field | Notes |
   |--------|--------------|-------|
   | Run ID | run_id | Integer workflow run identifier |
   | Status | conclusion | Badged: green="Success", red="Failed" |
   | Name/Branch | name \|\| branch | Combined into single cell |
   | Duration (s) | duration_seconds | Raw seconds |
   | Anomaly Label | anomaly_label | "Anomalous" badge or "Normal" text |
   | Score | anomaly_score | 4-decimal precision, monospace font |
   | Created At | created_at | Localized date/time string |

#### JavaScript Features:
- **Auto-refresh**: Every 60 seconds via `setInterval`
- **Cache Busting**: Appends timestamp query parameter to API requests (`?t=timestamp`)
- **Loading Overlay**: Full-screen spinner during data fetches
- **Live Status Indicator**: Pulsing green dot at status="live" when connected
- **Error Handling**: Graceful fallback messages on API failures

---

## ML Pipeline Scripts

### `scripts/fetch_metrics.py` - GitHub Metrics Collector

1. Reads credentials from environment variables (`GITHUB_TOKEN`, `GITHUB_REPO`)
2. Queries GitHub REST API: `GET /repos/{owner}/{repo}/actions/runs?per_page=100`
3. Calculates duration in seconds for each run
4. Saves results to both CSV and SQLite simultaneously

### `scripts/train_model.py` - Anomaly Detection Model Trainer

**Algorithm**: Isolation Forest (ensemble of iTrees)  
**Parameters**:
- `n_estimators=100` - Number of trees in the forest
- `contamination=0.1` - Expects ~10% of data to be anomalous
- `random_state=42` - Reproducibility

#### Feature Engineering Pipeline:
| Original Field | Transformed Feature | Formula/Method |
|---------------|-------------------|----------------|
| conclusion | is_failed | Map("success"→0, "failure"→1), fillna(0) |
| created_at | build_hour | Extract hour component from UTC datetime |
| duration_seconds | duration_log | ln(duration + 1) - natural log transform |

#### Anomaly Scoring:
- **Label**: `model.predict(X)` returns `1` (normal) or `-1` (anomalous)
- **Score**: `model.decision_function(X)` - more negative = more anomalous

#### Output Artifacts:
1. `data/model.joblib` - Serialized scikit-learn model for inference
2. `data/scored_runs.csv` - Full dataset with added columns: anomaly_label, anomaly_score
3. `data/anomalies.png` - Scatter plot visualization (green=normal, red=anomalous)

### `scripts/detect_latest_run.py` - Real-time Run Scorer

**Purpose**: Score the most recent pipeline run using the pre-trained model

1. Validates model file exists at `data/model.joblib`
2. Queries SQLite database for latest workflow run (ORDER BY created_at DESC LIMIT 1)
3. Prepares feature vector matching training schema exactly:
   ```python
   features_df = pd.DataFrame([{
       "duration_seconds": latest_run["duration_seconds"],
       "is_failed": int(latest_run.get("conclusion") == "failure"),
       "build_hour": pd.to_datetime(latest_run["created_at"], utc=True).hour,
       "duration_log": np.log1p(latest_run["duration_seconds"])
   }])
   ```
4. Runs prediction and decision function on the feature vector

---

## Data Schema

### SQLite Database (`data/metrics.db`) - `workflow_runs` Table:

| Column | Type | Description |
|--------|----Description |
| run_id | INTEGER (PRIMARY KEY) | Unique GitHub Actions run identifier, unique for every CI/CD step |
| name | TEXT | Workflow name (e.g., "CI Pipeline", "Collect Synthetic Metrics") |
| status | TEXT | Workflow status: "completed", "in_progress", etc. |
| conclusion | TEXT | Final result: "success", "failure", "cancelled" |
| event | TEXT | Triggering event:  The trigger that caused the workflow to run ("push", "pull_request", "workflow_dispatch", "schedule") |
| branch | TEXT | Source branch of the run (e.g., "main") |
| created_at | TEXT | ISO 8601 UTC timestamp when the run was created |
| duration_seconds | INTEGER | Total execution time in seconds |
| html_url | TEXT - URL to the GitHub Actions run page for direct navigation |
| test_count | INTEGER (DEFAULT: 0) | Number of test cases executed during the CI pipeline runs/test suites that ran |
| failed_tests | INTEGER (DEFAULT: 0) | Tests that failed during that specific build |
| duration_log | REAL | Feature engineering bylog(duration +1) for ML model input |

---

### CSV Files (`data/scored_runs.csv`) Schema:

Extended from `workflow_runs` with added ML columns:

| Column | Description | Example Value |
|--------|---------|-------------|
| run_id | GitHub Actions run ID | 12345678901 |
| name | Workflow name | "CI Pipeline" |
| status | Execution status | "completed" |
| conclusion | Final outcome | "success", "failure", or "cancelled" |
| event | Triggering event | "push", "pull_request", or "workflow_dispatch" |
| branch | Git branch name | "main" |
| created_at | ISO 8601 UTC timestamp | "2024-01-15T10:30:00Z" |
| duration_seconds | Build/duration in seconds | 42, 145, etc. |
| anomaly_label | ML-generated label (1=normal, -1=anomalous) | 1 or -1 |
| anomaly_score | Isolation Forest decision function output | -0.1234... |
| html_url | Link to the GitHub Actions run for direct inspection | "https://github.com/..." |

---

## Deployment & Operations

### Local Development

```bash
# Option 1: Direct Python execution
pip install -r requirements.txt
python app/main.py
# → http://localhost:5000/dashboard

# Option 2: Via setup.py (editable mode)
pip install -e .
python app/main.py
```

### Docker Deployment

```bash
# Build with docker-compose (includes hot-reload via volume mounts)
docker compose up -d --build

## Access the Dashboard
Open http://localhost:5000/dashboard in your browser.

## Configure Environment Variables
GITHUB_TOKEN=${GITHUB_TOKEN:-} # Optional: for auto-refresh from GitHub API
GITHUB_REPO=${GITHUB_REPO:-azizwhibi/ci-cd-ai-anomaly} # Optional: repo for auto-refresh

Data Persistence:
./data:/app/data:rw  Mounts local data directory into container with read-write access.

### Production Considerations

1. Set proper `GITHUB_TOKEN` via secrets for API access
2. Use production WSGI server (e.g., gunicorn) instead of Flask's dev server

---

## Testing

Location: `tests/test_app.py`

| Test Name | Endpoint Tested | Assertions |
|-----------|-----------------|------------|
| test_health | GET /health | Returns 200 with {"status": "ok"} |
| test_simulate_failed_build | GET /simulate?status=failed&duration=120&failed_tests=3 | Returns 200 with exact expected values |

Run tests: `pytest -v tests/test_app.py`

**Note**: Tests use Flask's built-in test client — no external services or database required.

---

## Dependencies Summary

### Core Framework
- **Flask**, **Werkzeug**, **Jinja2**, **itsdangerous**, **blinker**, **MarkupSafe** - Web framework ecosystem

### Data Science & ML
- **scikit-learn** (Isolation Forest), **pandas** (data manipulation, **numpy** (numerical computing), **scipy** (scientific computing)
- **matplotlib** (visualization), **joblib** (model serialization)

### HTTP & APIs
- **requests** - GitHub REST API client

### Testing
- **pytest**, **pluggy**, **iniconfig**, **exceptiongroup**, **tomli**, **packaging** — Test infrastructure

### Visualization & Charting
- **matplotlib**, **pillow**,   Font & layout: **fonttools**,  **kiwisolver**, **pyparsing**, **contourpy**

---

## GitHub Actions Bot Identity

Data commits use the GitHub Actions bot identity:
```
user.email = "41898282+github-actions[bot]@users.noreply.github.com"
user.name  = "github-actions[bot]"
```

This ensures consistent attribution for automated data updates pushed to the repository.

## Key Design Decisions

### Why Isolation Forest?

- **Unsupervised learning**: No labeled anomalies needed — the model discovers patterns from normal data alone. Only normal and anomalous labels are produced.
- **Handles high cardinality well**: Automatically handles outlying duration, failure counts, and time-of-day patterns without manual threshold tuning.
-Fast inference: `model.predict()` on new runs is near-instantaneous — ideal for a real-time dashboard scoring pipeline.

### Why Persistent Data in Git?

Model files (`model.joblib`), scored CSVs (`scored_runs.csv`), and visualization charts (`anomalies.png`) are committed directly to the repository (specified in `.gitignore`). This provides:
- **Versioned ML history**: Track how anomaly patterns evolve over time.
- **Zero external storage**: No need for S3, GCP Storage, or dedicated model registry.
- **Transparent debugging**: Anyone can inspect `scored_runs.csv` to verify scoring.

### Why SQLite?

SQLite was chosen as the central data store because it provides:
- A single-file database that requires no separate server process.
- Zero-config setup — just a file on disk. Perfect for prototyping and lightweight deployment scenarios.
- Simple SQL queries (`SELECT * FROM workflow_runs WHERE conclusion = 'failure'`) via pandas `read_sql()`.

---

## Future Enhancements (Potential)

1. **Expanded Feature Set**: Add test count, changed files, commit message complexity as features
2. **Time Series Analysis**: Implement Prophet or ARIMA for temporal pattern detection
3. **Alerting Integration**: Slack webhook, email notifications, or Teams alerts on anomalies
4. **Multi-Repo Support**: Extend to monitor multiple repositories from a single dashboard
5. **Advanced Visualization**: Real-time D3.js charts instead of static PNGs
6. **Webhook-Based Triggers**: Replace cron-based collection with GitHub webhook receivers for lower-latency updates

---

## License & Attribution

This project is part of the CI/CD AI Anomaly Detection research, exploring the intersection of DevOps automation and artificial intelligence for identifying pipeline failures before they impact production systems.
</parameter>