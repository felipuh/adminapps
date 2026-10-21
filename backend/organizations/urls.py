"""
URLs de Organizaciones
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'', views.OrganizationViewSet, basename='organization')
router.register(r'invitations', views.OrganizationInvitationViewSet, basename='invitation')

urlpatterns = [
    path('', include(router.urls)),
]
