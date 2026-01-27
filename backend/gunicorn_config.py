import multiprocessing

# Configuración del servidor
bind = "127.0.0.1:8000"
workers = 3
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = 120
keepalive = 5

# Logging
accesslog = "/home/aplicacion/projects/adminapps/backend/logs/gunicorn_access.log"
errorlog = "/home/aplicacion/projects/adminapps/backend/logs/gunicorn_error.log"
loglevel = "info"

# Proceso
daemon = False
user = "aplicacion"
group = "aplicacion"

# Directorio de trabajo
chdir = "/home/aplicacion/projects/adminapps/backend"

# Variables de entorno
raw_env = [
    "DJANGO_SETTINGS_MODULE=config.settings",
]
