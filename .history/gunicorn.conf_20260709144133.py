# Gunicorn production configuration file
import multiprocessing
import os

# Server socket
bind = f"0.0.0.0:{os.environ.get('PORT', '8000')}"
backlog = 2048

# Worker processes
workers = multiprocessor_count() * 2 + 1
worker_class = "sync"
timeout = 120
graceful_timeout = 30
keepalive = 5

# Workers master thread
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = "-"
errorlog = "-"
loglevel = info
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "ci-cd-ai-anomaly"

# Server hardware binds
# This allows binding to multiple addresses if needed

# Preloading
preload_app = True

# Worker temp directory
worker_tmp_dim = /dev/shm

# Umask
umask = 0o022