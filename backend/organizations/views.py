"""
Views para Organizaciones
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta

from .models import Organization, OrganizationInvitation
from .serializers import (
    OrganizationSerializer,
    OrganizationListSerializer,
    OrganizationCreateSerializer,
    OrganizationInvitationSerializer,
)


class IsPlatformAdmin(permissions.BasePermission):
    """Permiso para administradores de plataforma"""
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_platform_admin or request.user.is_superuser
        )


class OrganizationViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de organizaciones
    Solo accesible para administradores de plataforma
    """
    
    queryset = Organization.objects.all()
    permission_classes = [IsPlatformAdmin]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return OrganizationListSerializer
        if self.action == 'create':
            return OrganizationCreateSerializer
        return OrganizationSerializer
    
    def get_queryset(self):
        queryset = Organization.objects.all()
        
        # Filtros
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        plan_filter = self.request.query_params.get('plan')
        if plan_filter:
            queryset = queryset.filter(plan=plan_filter)
        
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(name__icontains=search)
        
        return queryset.order_by('-created_at')
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activar una organización"""
        org = self.get_object()
        org.status = 'active'
        org.save()
        return Response({'status': 'Organización activada'})
    
    @action(detail=True, methods=['post'])
    def suspend(self, request, pk=None):
        """Suspender una organización"""
        org = self.get_object()
        org.status = 'suspended'
        org.save()
        return Response({'status': 'Organización suspendida'})
    
    @action(detail=True, methods=['post'])
    def extend_trial(self, request, pk=None):
        """Extender período de prueba"""
        org = self.get_object()
        days = request.data.get('days', 7)
        
        if org.trial_ends_at:
            org.trial_ends_at += timedelta(days=days)
        else:
            org.trial_ends_at = timezone.now() + timedelta(days=days)
        
        org.save()
        return Response({
            'status': 'Período de prueba extendido',
            'trial_ends_at': org.trial_ends_at.isoformat()
        })
    
    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """Estadísticas de la organización"""
        org = self.get_object()
        
        return Response({
            'id': org.id,
            'name': org.name,
            'user_count': org.user_count,
            'max_users': org.max_users,
            'usage_percentage': (org.user_count / org.max_users * 100) if org.max_users > 0 else 0,
            'plan': org.plan,
            'status': org.status,
            'enabled_modules': len(org.get_enabled_modules()),
            'created_at': org.created_at.isoformat(),
        })
    
    @action(detail=True, methods=['post'])
    def upload_logo(self, request, pk=None):
        """Subir logo de la organización"""
        org = self.get_object()
        
        if 'logo' not in request.FILES:
            return Response(
                {'error': 'No se proporcionó archivo de logo'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        org.logo = request.FILES['logo']
        org.save()
        
        return Response({
            'status': 'Logo actualizado',
            'logo_url': org.logo.url
        })


class OrganizationInvitationViewSet(viewsets.ModelViewSet):
    """ViewSet para invitaciones a organizaciones"""
    
    queryset = OrganizationInvitation.objects.all()
    serializer_class = OrganizationInvitationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        # Administradores ven todas
        if user.is_platform_admin or user.is_superuser:
            return OrganizationInvitation.objects.all()
        
        # Usuarios normales solo ven invitaciones de sus organizaciones
        org_ids = user.memberships.filter(
            role='org_admin',
            is_active=True
        ).values_list('organization_id', flat=True)
        
        return OrganizationInvitation.objects.filter(organization_id__in=org_ids)
    
    def perform_create(self, serializer):
        # Establecer fecha de expiración (7 días)
        expires_at = timezone.now() + timedelta(days=7)
        serializer.save(
            invited_by=self.request.user,
            expires_at=expires_at
        )
    
    @action(detail=True, methods=['post'])
    def resend(self, request, pk=None):
        """Reenviar invitación"""
        invitation = self.get_object()
        
        if invitation.status != 'pending':
            return Response(
                {'error': 'Solo se pueden reenviar invitaciones pendientes'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Actualizar fecha de expiración
        invitation.expires_at = timezone.now() + timedelta(days=7)
        invitation.save()
        
        # TODO: Enviar email
        
        return Response({'status': 'Invitación reenviada'})
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancelar invitación"""
        invitation = self.get_object()
        
        if invitation.status != 'pending':
            return Response(
                {'error': 'Solo se pueden cancelar invitaciones pendientes'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        invitation.status = 'cancelled'
        invitation.save()
        
        return Response({'status': 'Invitación cancelada'})
