"""
API Views - Admin Apps
Dashboard y endpoints generales para Comtech (backoffice)
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.utils import timezone
from django.db.models import Count, Q

from apps.organizations.models import Organization
from apps.users.models import User, UserActivityLog
from apps.products.models import ISOStandard, OrganizationModule
from apps.users.permissions import IsAdmin


class HealthCheckView(APIView):
    """Health check endpoint"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        return Response({
            'status': 'healthy',
            'service': 'Admin Apps API - Comtech Backoffice',
            'version': '1.0.0',
            'timestamp': timezone.now().isoformat()
        })


class DashboardView(APIView):
    """
    Dashboard principal de Admin Apps
    Panel de control interno de Comtech
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def get(self, request):
        now = timezone.now()
        this_month_start = now.replace(day=1, hour=0, minute=0, second=0)
        
        # Estadísticas de organizaciones (clientes)
        org_stats = {
            'total': Organization.objects.count(),
            'active': Organization.objects.filter(status='active').count(),
            'trial': Organization.objects.filter(status='trial').count(),
            'suspended': Organization.objects.filter(status='suspended').count(),
            'new_this_month': Organization.objects.filter(created_at__gte=this_month_start).count(),
        }
        
        # Estadísticas de módulos ISO
        iso_stats = {
            'standards_available': ISOStandard.objects.filter(status__in=['active', 'beta']).count(),
            'standards_in_dev': ISOStandard.objects.filter(status='development').count(),
            'total_assignments': OrganizationModule.objects.count(),
            'active_assignments': OrganizationModule.objects.filter(is_enabled=True, status='active').count(),
            'trial_assignments': OrganizationModule.objects.filter(status='trial').count(),
            'expiring_soon': OrganizationModule.objects.filter(
                status='trial',
                expires_at__lte=now + timezone.timedelta(days=7)
            ).count(),
        }
        
        # Módulos más usados
        popular_modules = list(
            OrganizationModule.objects.filter(is_enabled=True)
            .values('iso_standard__code', 'iso_standard__name')
            .annotate(count=Count('id'))
            .order_by('-count')[:5]
        )
        
        # Estadísticas de usuarios (del equipo Comtech)
        user_stats = {
            'total_admins': User.objects.filter(role__in=['superadmin', 'admin']).count(),
            'active_today': User.objects.filter(
                role__in=['superadmin', 'admin'],
                last_activity_at__date=now.date()
            ).count(),
        }
        
        # Actividad reciente
        recent_activity = UserActivityLog.objects.select_related(
            'user', 'organization'
        ).order_by('-created_at')[:10]
        
        activity_list = [
            {
                'id': str(log.id),
                'user': log.user.email if log.user else 'Sistema',
                'action': log.action,
                'module': log.module,
                'description': log.description,
                'organization': log.organization.name if log.organization else None,
                'created_at': log.created_at.isoformat(),
            }
            for log in recent_activity
        ]
        
        # Organizaciones recientes (nuevos clientes)
        recent_orgs = Organization.objects.order_by('-created_at')[:5]
        recent_orgs_list = [
            {
                'id': str(org.id),
                'code': org.code,
                'name': org.name,
                'status': org.status,
                'industry': org.industry,
                'created_at': org.created_at.isoformat(),
            }
            for org in recent_orgs
        ]
        
        # Alertas del sistema
        alerts = []
        
        # Trials por expirar
        expiring_trials = OrganizationModule.objects.filter(
            status='trial',
            expires_at__lte=now + timezone.timedelta(days=3)
        ).select_related('organization', 'iso_standard')[:5]
        
        for module in expiring_trials:
            alerts.append({
                'type': 'warning',
                'message': f'Trial de {module.iso_standard.code} para {module.organization.name} expira pronto',
                'date': module.expires_at.isoformat() if module.expires_at else None,
            })
        
        # Organizaciones en trial
        org_trials_expiring = Organization.objects.filter(
            status='trial',
            trial_ends_at__lte=now + timezone.timedelta(days=3)
        )[:5]
        
        for org in org_trials_expiring:
            alerts.append({
                'type': 'info',
                'message': f'Periodo de prueba de {org.name} expira pronto',
                'date': org.trial_ends_at.isoformat() if org.trial_ends_at else None,
            })
        
        return Response({
            'organizations': org_stats,
            'iso_modules': iso_stats,
            'popular_modules': popular_modules,
            'team': user_stats,
            'recent_activity': activity_list,
            'recent_organizations': recent_orgs_list,
            'alerts': alerts,
            'generated_at': now.isoformat(),
        })


class SystemStatsView(APIView):
    """
    Estadísticas detalladas del sistema
    Métricas internas de Comtech
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def get(self, request):
        # Distribución por industria
        industry_distribution = dict(
            Organization.objects.filter(status='active')
            .values('industry')
            .annotate(count=Count('id'))
            .values_list('industry', 'count')
        )
        
        # Distribución por tamaño
        size_distribution = dict(
            Organization.objects.filter(status='active')
            .values('size')
            .annotate(count=Count('id'))
            .values_list('size', 'count')
        )
        
        # Adopción de módulos ISO
        module_adoption = list(
            ISOStandard.objects.filter(status__in=['active', 'beta'])
            .annotate(
                total_orgs=Count('organization_assignments'),
                active_orgs=Count('organization_assignments', filter=Q(
                    organization_assignments__is_enabled=True,
                    organization_assignments__status='active'
                ))
            )
            .values('code', 'name', 'total_orgs', 'active_orgs')
            .order_by('-total_orgs')
        )
        
        return Response({
            'industry_distribution': industry_distribution,
            'size_distribution': size_distribution,
            'module_adoption': module_adoption,
        })


class QuickActionsView(APIView):
    """
    Acciones rápidas para el dashboard de Comtech
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def get(self, request):
        """Obtener acciones rápidas disponibles"""
        actions = [
            {
                'id': 'new_client',
                'label': 'Nuevo Cliente',
                'icon': 'building',
                'url': '/organizations/new',
                'description': 'Registrar nueva organización'
            },
            {
                'id': 'assign_module',
                'label': 'Asignar Módulo ISO',
                'icon': 'package-plus',
                'url': '/modules/assign',
                'description': 'Activar módulo para un cliente'
            },
            {
                'id': 'view_trials',
                'label': 'Ver Trials Activos',
                'icon': 'clock',
                'url': '/modules?status=trial',
                'description': 'Revisar periodos de prueba'
            },
            {
                'id': 'new_iso',
                'label': 'Nuevo Estándar ISO',
                'icon': 'file-certificate',
                'url': '/iso-standards/new',
                'description': 'Agregar estándar ISO al catálogo'
            },
        ]
        return Response(actions)
