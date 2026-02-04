"""
WSGI config for Admin Apps
"""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'adminapps.settings')
application = get_wsgi_application()
