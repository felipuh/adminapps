"""
Views for Organizations - Admin Apps
"""
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db.models import Count, Q

from .models import Organization, OrganizationSettings, OrganizationInvitation
from .serializers import (
    OrganizationListSerializer,
    OrganizationDetailSerializer,
    OrganizationCreateSerializer,
    OrganizationUpdateSerializer,
    OrganizationSettingsSerializer,
    OrganizationInvitationSerializer,
    OrganizationInvitationCreateSerializer,
    OrganizationStatsSerializer,
)
from apps.users.permissions import IsSuperAdmin, IsAdmin, IsOrgAdmin


class OrganizationViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de organizaciones
    """
    queryset = Organization.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'industry', 'size']
    search_fields = ['name', 'code', 'email', 'legal_name']
    ordering_fields = ['name', 'created_at', 'status']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return OrganizationListSerializer
        elif self.action == 'create':
            return OrganizationCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return OrganizationUpdateSerializer
        return OrganizationDetailSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'destroy']:
            return [IsSuperAdmin()]
        elif self.action in ['update', 'partial_update']:
            return [IsAdmin()]
        return [IsAuthenticated()]
    
    def get_queryset(self):
        user = self.request.user
        queryset = Organization.objects.all()
        
        # Si no es admin, solo puede ver su organización
        if not user.is_admin:
            queryset = queryset.filter(id=user.organization_id)
        
        return queryset.select_related('subscription__plan')
    
    @action(detail=True, methods=['get', 'patch'])
    def organization_settings(self, request, pk=None):
        """Obtener o actualizar configuración de la organización"""
        organization = self.get_object()
        org_settings, created = OrganizationSettings.objects.get_or_create(
            organization=organization
        )
        
        if request.method == 'PATCH':
            serializer = OrganizationSettingsSerializer(
                org_settings, data=request.data, partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        
        serializer = OrganizationSettingsSerializer(org_settings)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """Obtener estadísticas de la organización"""
        organization = self.get_object()
        
        # Calcular estadísticas
        users = organization.users.all()
        stats = {
            'total_users': users.count(),
            'active_users': users.filter(is_active=True).count(),
            'total_documents': 0,  # Se conectará con ISO Smart
            'storage_used_mb': 0,
            'storage_percentage': 0,
            'risks_count': 0,
            'critical_risks': 0,
            'objectives_count': 0,
            'completed_objectives': 0,
            'last_activity': users.order_by('-last_activity_at').values_list(
                'last_activity_at', flat=True
            ).first()
        }
        
        serializer = OrganizationStatsSerializer(stats)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def users(self, request, pk=None):
        """Listar usuarios de la organización"""
        organization = self.get_object()
        from apps.users.serializers import UserListSerializer
        
        users = organization.users.all()
        serializer = UserListSerializer(users, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activar una organización"""
        organization = self.get_object()
        organization.status = 'active'
        organization.save()
        return Response({'status': 'activated'})
    
    @action(detail=True, methods=['post'])
    def suspend(self, request, pk=None):
        """Suspender una organización"""
        organization = self.get_object()
        organization.status = 'suspended'
        organization.save()
        return Response({'status': 'suspended'})


class OrganizationInvitationViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de invitaciones
    """
    queryset = OrganizationInvitation.objects.all()
    permission_classes = [IsAuthenticated, IsOrgAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['organization', 'status']
    search_fields = ['email']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return OrganizationInvitationCreateSerializer
        return OrganizationInvitationSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.is_admin:
            return OrganizationInvitation.objects.all()
        return OrganizationInvitation.objects.filter(organization=user.organization)
    
    def perform_create(self, serializer):
        serializer.save(
            invited_by=self.request.user,
            expires_at=timezone.now() + timezone.timedelta(days=7)
        )
        # TODO: Enviar email de invitación
    
    @action(detail=True, methods=['post'])
    def resend(self, request, pk=None):
        """Reenviar invitación"""
        invitation = self.get_object()
        if invitation.status != 'pending':
            return Response(
                {'error': 'Solo se pueden reenviar invitaciones pendientes'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        invitation.expires_at = timezone.now() + timezone.timedelta(days=7)
        invitation.save()
        # TODO: Enviar email
        
        return Response({'status': 'resent'})
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancelar invitación"""
        invitation = self.get_object()
        invitation.status = 'cancelled'
        invitation.save()
        return Response({'status': 'cancelled'})
    
    @action(detail=False, methods=['post'], permission_classes=[])
    def accept(self, request):
        """Aceptar invitación (endpoint público con token)"""
        token = request.data.get('token')
        if not token:
            return Response(
                {'error': 'Token requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            invitation = OrganizationInvitation.objects.get(token=token)
        except OrganizationInvitation.DoesNotExist:
            return Response(
                {'error': 'Invitación no válida'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if invitation.is_expired:
            invitation.status = 'expired'
            invitation.save()
            return Response(
                {'error': 'La invitación ha expirado'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if invitation.status != 'pending':
            return Response(
                {'error': f'La invitación ya fue {invitation.get_status_display().lower()}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Retornar datos para registro
        return Response({
            'invitation_id': str(invitation.id),
            'organization_name': invitation.organization.name,
            'email': invitation.email,
            'role': invitation.role,
        })
