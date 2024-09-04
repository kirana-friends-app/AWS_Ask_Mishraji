# Gunicorn configuration file
import multiprocessing

# Socket Path
bind = 'unix:/tmp/gunicorn.sock'

# Worker Options
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = 'sync'

# Logging Options
loglevel = 'debug'
accesslog = '/var/log/gunicorn/access.log'
errorlog = '/var/log/gunicorn/error.log'
