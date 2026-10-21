"""Dedicated human Django Admin process."""
from apps.users.runtime_admin import site
from django.urls import path

urlpatterns = [path('admin/', site.urls)]
