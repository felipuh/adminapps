"""
URLs principales de Admin Apps
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Admin de Django
    path('admin/', admin.site.urls),
    
    # API de autenticación
    path('api/auth/', include('users.urls')),
    
    # API de organizaciones
    path('api/organizations/', include('organizations.urls')),
    
    # API de suscripciones
    path('api/subscriptions/', include('subscriptions.urls')),
    
    # API de integración (para ISO Smart y otros servicios)
    path('api/integration/', include('integration.urls')),
]

# Servir archivos media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
