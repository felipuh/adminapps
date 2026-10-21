"""Human authentication process; no business or Django Admin routes."""
from django.urls import include, path
from apps.users.urls import urlpatterns as human_urls

# The final include is the management router, served by control_plane instead.
urlpatterns = [path('api/auth/', include(human_urls[:-1]))]
