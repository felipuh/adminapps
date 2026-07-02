"""
API Views - Admin Apps
Dashboard y endpoints generales para Comtech (backoffice)
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.utils import timezone
from django.db.models import Count, Q
from django.utils.dateparse import parse_date

from apps.organizations.models import Organization, OrganizationFeatureFlag
from apps.users.models import User, UserActivityLog
from apps.products.models import ISOStandard, OrganizationModule, OrganizationProductEntitlement, ProductSystem
from apps.products.services import build_product_access_readiness_report
from apps.users.permissions import IsAdmin
from apps.integration.models import LandingAnalyticsEvent


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

        entitlement_qs = OrganizationProductEntitlement.objects.select_related('product', 'organization')
        iso_smart_orgs = entitlement_qs.filter(
            product__code='ISO_SMART',
            enabled=True,
            status__in=['active', 'trial'],
        ).values('organization_id')
        medsupplier_orgs = entitlement_qs.filter(
            product__code='MEDSUPPLIER',
            enabled=True,
            status__in=['active', 'trial'],
        ).values('organization_id')
        product_stats = {
            'systems_total': ProductSystem.objects.count(),
            'systems_active': ProductSystem.objects.filter(status__in=['active', 'beta']).count(),
            'entitlements_total': entitlement_qs.count(),
            'entitlements_active': entitlement_qs.filter(enabled=True, status='active').count(),
            'entitlements_trial': entitlement_qs.filter(enabled=True, status='trial').count(),
            'entitlements_suspended': entitlement_qs.filter(status='suspended').count(),
            'iso_smart_customers': iso_smart_orgs.distinct().count(),
            'medsupplier_customers': medsupplier_orgs.distinct().count(),
            'customers_with_both': Organization.objects.filter(
                product_entitlements__product__code='ISO_SMART',
                product_entitlements__enabled=True,
                product_entitlements__status__in=['active', 'trial'],
            ).filter(
                product_entitlements__product__code='MEDSUPPLIER',
                product_entitlements__enabled=True,
                product_entitlements__status__in=['active', 'trial'],
            ).distinct().count(),
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
            'products': product_stats,
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


class ProductReadinessView(APIView):
    """Read-only SaaS product access readiness report for AdminApps operators."""

    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        return Response(build_product_access_readiness_report())


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


class LandingAnalyticsSummaryView(APIView):
    """Resumen centralizado de analítica del landing para backoffice."""
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        campaign = str(request.query_params.get('campaign') or '').strip()
        from_date = parse_date(str(request.query_params.get('from') or '').strip())
        to_date = parse_date(str(request.query_params.get('to') or '').strip())

        queryset = LandingAnalyticsEvent.objects.all()
        if campaign:
            queryset = queryset.filter(campaign=campaign)
        if from_date:
            queryset = queryset.filter(event_date__gte=from_date)
        if to_date:
            queryset = queryset.filter(event_date__lte=to_date)

        total_events = queryset.count()
        cta_events = queryset.filter(event_name='cta_click')

        by_variant = []
        for item in queryset.values('variant').annotate(total=Count('id')).order_by('variant'):
            variant_key = item['variant'] or 'N/A'
            total = item['total']
            cta_total = cta_events.filter(variant=item['variant']).count()
            cta_rate = round((cta_total / total) * 100, 2) if total else 0
            by_variant.append({
                'variant': variant_key,
                'events': total,
                'cta_clicks': cta_total,
                'cta_rate_percent': cta_rate,
            })

        by_day = list(
            queryset.values('event_date', 'campaign', 'variant')
            .annotate(total=Count('id'))
            .order_by('-event_date', 'campaign', 'variant')
        )

        winner = None
        sortable = [item for item in by_variant if item['variant'] in {'A', 'B'}]
        if sortable:
            winner = sorted(sortable, key=lambda row: (row['cta_rate_percent'], row['cta_clicks']), reverse=True)[0]['variant']

        return Response({
            'campaign': campaign,
            'filters': {
                'from': from_date.isoformat() if from_date else None,
                'to': to_date.isoformat() if to_date else None,
            },
            'totals': {
                'events': total_events,
                'cta_clicks': cta_events.count(),
            },
            'winner_variant': winner,
            'by_variant': by_variant,
            'by_day': by_day,
        })


class FeatureFlagsView(APIView):
    """Resolve feature flags for the current user organization context."""

    permission_classes = [IsAuthenticated]

    def _resolve_organization(self, request):
        requested_org_id = str(request.query_params.get('organization_id') or '').strip()
        user = request.user

        if requested_org_id:
            if not user.is_admin:
                raise PermissionDenied('Only admins can query feature flags for another organization')
            try:
                return Organization.objects.get(id=requested_org_id)
            except Organization.DoesNotExist as exc:
                raise ValidationError({'organization_id': 'Organization not found'}) from exc

        return user.organization

    def get(self, request):
        organization = self._resolve_organization(request)
        if organization is None and not request.user.is_admin:
            raise ValidationError({'organization_id': 'User has no organization assigned'})

        flags = OrganizationFeatureFlag.objects.resolve_for_organization(organization)

        return Response({
            'organization_id': str(organization.id) if organization else None,
            'flags': flags,
            'total_flags': len(flags),
        })
