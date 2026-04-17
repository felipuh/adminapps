import multiprocessing
import os
from pathlib import Path


def _load_env_file(env_path):
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding='utf-8').splitlines():
        line = raw_line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, value = line.split('=', 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


BASE_DIR = Path(__file__).resolve().parent
_load_env_file(BASE_DIR / '.env')

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
    f"USE_SQLITE={os.environ.get('USE_SQLITE', '')}",
    f"SQLITE_NAME={os.environ.get('SQLITE_NAME', '')}",
    f"DB_NAME={os.environ.get('DB_NAME', '')}",
    f"DB_USER={os.environ.get('DB_USER', '')}",
    f"DB_PASSWORD={os.environ.get('DB_PASSWORD', '')}",
    f"DB_HOST={os.environ.get('DB_HOST', '')}",
    f"DB_PORT={os.environ.get('DB_PORT', '')}",
]
