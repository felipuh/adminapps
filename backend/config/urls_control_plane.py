"""Human control-plane process. Technical integration and billing remain held."""
from django.urls import include, path
from apps.users.urls import router

urlpatterns = [
    path('api/auth/', include(router.urls)),
    path('api/organizations/', include('apps.organizations.urls')),
    path('api/products/', include('apps.products.urls')),
    path('api/subscriptions/', include('apps.subscriptions.urls')),
]
