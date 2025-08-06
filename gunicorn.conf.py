
import multiprocessing

bind = "0.0.0.0:8000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 10000
max_requests_jitter = 1000
preload_app = True
timeout = 30
keepalive = 2
max_requests_jitter = 50

# Logging
accesslog = "/app/logs/access.log"
errorlog = "/app/logs/error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = 'skinlytics-api'

# SSL (if enabled)
# keyfile = "/app/ssl/key.pem"
# certfile = "/app/ssl/cert.pem"
