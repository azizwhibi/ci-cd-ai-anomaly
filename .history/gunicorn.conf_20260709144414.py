# Gunicorn production configuration file
import multiprocessing
import os

# Server socket
bind = f"0.0.0.0:{os.environ.get('PORT', '8000')}"
backlog = 2048

# Worker processes: 2 * CPU cores + 1, at least 2
workers = max(2, multiprocessing.cpu_count() * 2 + 1)
worker_class = "sync"
timeout = 120
graceful_timeout = 30
keepalive = 5

# Workers master thread
max_requests = 1000
max_requests_jitter = 50

# Logging (outputs to stdout/stderr for Docker/containerized environments)
accesslog = "-"
errorlog = "-"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "ci-cd-ai-anomaly"

# Preloading - load app before forking worker processes
preload_app = True

# Worker temp directory (for handling graceful restarts)
worker_temp_dir = "/dev/shm" if os.path.exists("/dev/shm") else None

# Umask file permissions
umask = 0o022
