"""Gunicorn configuration."""
bind = "0.0.0.0:80"
workers = 5
worker_tmp_dir = "/dev/shm"
timeout = 120
graceful_timeout = 120
keepalive = 5
loglevel = "info"
accesslog = "-"
errorlog = "-"
