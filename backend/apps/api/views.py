"""
API Views - Admin Apps
Dashboard y endpoints generales
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.utils import timezone
from django.db.models import Count, Q

from apps.organizations.models import Organization
from apps.users.models import User, UserActivityLog
from apps.subscriptions.models import Subscription, Plan, Invoice
from apps.users.permissions import IsAdmin


class HealthCheckView(APIView):
    """Health check endpoint"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        return Response({
            'status': 'healthy',
            'service': 'Admin Apps API',
            'version': '1.0.0',
            'timestamp': timezone.now().isoformat()
        })


class DashboardView(APIView):
    """
    Dashboard principal de Admin Apps
    Estadísticas globales del sistema
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def get(self, request):
        now = timezone.now()
        today = now.date()
        this_month_start = now.replace(day=1, hour=0, minute=0, second=0)
        last_30_days = now - timezone.timedelta(days=30)
        
        # Estadísticas de organizaciones
        org_stats = {
            'total': Organization.objects.count(),
            'active': Organization.objects.filter(status='active').count(),
            'trial': Organization.objects.filter(status='trial').count(),
            'suspended': Organization.objects.filter(status='suspended').count(),
            'new_this_month': Organization.objects.filter(created_at__gte=this_month_start).count(),
        }
        
        # Estadísticas de usuarios
        user_stats = {
            'total': User.objects.count(),
            'active': User.objects.filter(is_active=True).count(),
            'new_this_month': User.objects.filter(created_at__gte=this_month_start).count(),
            'active_today': User.objects.filter(last_activity_at__date=today).count(),
            'by_role': dict(
                User.objects.values('role').annotate(count=Count('id')).values_list('role', 'count')
            ),
        }
        
        # Estadísticas de suscripciones
        subscription_stats = {
            'active': Subscription.objects.filter(status='active').count(),
            'trial': Subscription.objects.filter(status='trial').count(),
            'expiring_soon': Subscription.objects.filter(
                status='active',
                current_period_end__lte=now + timezone.timedelta(days=7)
            ).count(),
            'by_plan': list(
                Subscription.objects.filter(status__in=['active', 'trial'])
                .values('plan__name')
                .annotate(count=Count('id'))
                .order_by('-count')
            ),
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
        
        # Organizaciones recientes
        recent_orgs = Organization.objects.order_by('-created_at')[:5]
        recent_orgs_list = [
            {
                'id': str(org.id),
                'code': org.code,
                'name': org.name,
                'status': org.status,
                'created_at': org.created_at.isoformat(),
            }
            for org in recent_orgs
        ]
        
        # Alertas del sistema
        alerts = []
        
        # Suscripciones por expirar
        expiring = Subscription.objects.filter(
            status='active',
            current_period_end__lte=now + timezone.timedelta(days=7)
        ).select_related('plan').prefetch_related('organizations')[:5]
        
        for sub in expiring:
            org = sub.organizations.first()
            if org:
                alerts.append({
                    'type': 'warning',
                    'message': f'Suscripción de {org.name} expira pronto',
                    'date': sub.current_period_end.isoformat() if sub.current_period_end else None,
                })
        
        # Trials por expirar
        trials_expiring = Organization.objects.filter(
            status='trial',
            trial_ends_at__lte=now + timezone.timedelta(days=3)
        )[:5]
        
        for org in trials_expiring:
            alerts.append({
                'type': 'info',
                'message': f'Periodo de prueba de {org.name} expira pronto',
                'date': org.trial_ends_at.isoformat() if org.trial_ends_at else None,
            })
        
        return Response({
            'organizations': org_stats,
            'users': user_stats,
            'subscriptions': subscription_stats,
            'recent_activity': activity_list,
            'recent_organizations': recent_orgs_list,
            'alerts': alerts,
            'generated_at': now.isoformat(),
        })


class SystemStatsView(APIView):
    """
    Estadísticas detalladas del sistema
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
        
        # Uso de módulos (basado en configuraciones)
        from apps.organizations.models import OrganizationSettings
        module_usage = {
            'sca': OrganizationSettings.objects.filter(module_sca_enabled=True).count(),
            'sie': OrganizationSettings.objects.filter(module_sie_enabled=True).count(),
            'asb': OrganizationSettings.objects.filter(module_asb_enabled=True).count(),
            'spm': OrganizationSettings.objects.filter(module_spm_enabled=True).count(),
            'documents': OrganizationSettings.objects.filter(module_documents_enabled=True).count(),
            'risks': OrganizationSettings.objects.filter(module_risks_enabled=True).count(),
            'objectives': OrganizationSettings.objects.filter(module_objectives_enabled=True).count(),
        }
        
        # Planes más populares
        popular_plans = list(
            Subscription.objects.filter(status__in=['active', 'trial'])
            .values('plan__name', 'plan__price')
            .annotate(count=Count('id'))
            .order_by('-count')[:5]
        )
        
        return Response({
            'industry_distribution': industry_distribution,
            'size_distribution': size_distribution,
            'module_usage': module_usage,
            'popular_plans': popular_plans,
        })


class QuickActionsView(APIView):
    """
    Acciones rápidas para el dashboard
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def get(self, request):
        """Obtener acciones rápidas disponibles"""
        actions = [
            {
                'id': 'create_org',
                'label': 'Nueva Organización',
                'icon': 'building',
                'url': '/organizations/new',
            },
            {
                'id': 'create_user',
                'label': 'Nuevo Usuario',
                'icon': 'user-plus',
                'url': '/users/new',
            },
            {
                'id': 'view_invoices',
                'label': 'Ver Facturas',
                'icon': 'file-text',
                'url': '/invoices',
            },
            {
                'id': 'manage_plans',
                'label': 'Gestionar Planes',
                'icon': 'package',
                'url': '/plans',
            },
        ]
        return Response(actions)
