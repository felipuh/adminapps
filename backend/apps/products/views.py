"""
Views for Products - Admin Apps
Control maestro de módulos ISO por cliente
"""
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db.models import Count, Q

from .models import (
    ISOStandard,
    ModuleActivityLog,
    OrganizationModule,
    OrganizationProductEntitlement,
    ProductSystem,
)
from .serializers import (
    ISOStandardSerializer,
    ISOStandardListSerializer,
    OrganizationModuleSerializer,
    OrganizationModuleCreateSerializer,
    OrganizationModuleToggleSerializer,
    ModuleActivityLogSerializer,
    OrganizationModulesOverviewSerializer,
    OrganizationProductEntitlementCreateSerializer,
    OrganizationProductEntitlementSerializer,
    OrganizationProductEntitlementToggleSerializer,
    ProductSystemListSerializer,
    ProductSystemSerializer,
)
from apps.users.permissions import IsSuperAdmin, IsAdmin
from apps.organizations.models import Organization


class ProductSystemViewSet(viewsets.ModelViewSet):
    """Catalogo producto-neutral de sistemas administrables."""

    queryset = ProductSystem.objects.all()
    permission_classes = [IsAuthenticated, IsAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'product_type', 'billing_enabled']
    search_fields = ['code', 'name', 'slug', 'description']
    ordering_fields = ['name', 'code', 'created_at', 'updated_at']
    ordering = ['name']

    def get_serializer_class(self):
        if self.action == 'list':
            return ProductSystemListSerializer
        return ProductSystemSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsSuperAdmin()]
        return [IsAuthenticated(), IsAdmin()]

    @action(detail=False, methods=['get'])
    def active(self, request):
        products = ProductSystem.objects.filter(status__in=['active', 'beta'])
        serializer = ProductSystemListSerializer(products, many=True)
        return Response(serializer.data)


class OrganizationProductEntitlementViewSet(viewsets.ModelViewSet):
    """Habilitacion producto-neutral por organizacion."""

    queryset = OrganizationProductEntitlement.objects.all()
    permission_classes = [IsAuthenticated, IsAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['organization', 'product', 'status', 'enabled']
    search_fields = ['organization__name', 'organization__code', 'product__code', 'product__name']
    ordering_fields = ['created_at', 'starts_at', 'ends_at', 'updated_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'create':
            return OrganizationProductEntitlementCreateSerializer
        return OrganizationProductEntitlementSerializer

    def get_queryset(self):
        return OrganizationProductEntitlement.objects.select_related(
            'organization', 'product', 'plan', 'subscription', 'activated_by'
        )

    def perform_create(self, serializer):
        serializer.save(activated_by=self.request.user)

    @action(detail=True, methods=['post'])
    def toggle(self, request, pk=None):
        entitlement = self.get_object()
        serializer = OrganizationProductEntitlementToggleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        action_type = serializer.validated_data['action']
        reason = serializer.validated_data.get('reason', '')

        if action_type == 'enable':
            entitlement.enable(user=request.user)
            message = f"Producto {entitlement.product.code} activado para {entitlement.organization.name}"
        elif action_type == 'disable':
            entitlement.disable(reason=reason)
            message = f"Producto {entitlement.product.code} suspendido para {entitlement.organization.name}"
        else:
            trial_days = serializer.validated_data.get('trial_days', 14)
            entitlement.enabled = True
            entitlement.status = 'trial'
            entitlement.ends_at = timezone.now() + timezone.timedelta(days=trial_days)
            entitlement.suspended_at = None
            entitlement.suspension_reason = ''
            entitlement.activated_by = request.user
            entitlement.save()
            message = f"Producto {entitlement.product.code} en prueba por {trial_days} dias"

        return Response({
            'status': 'success',
            'message': message,
            'entitlement': OrganizationProductEntitlementSerializer(entitlement).data,
        })

    @action(detail=False, methods=['get'])
    def by_organization(self, request):
        org_id = request.query_params.get('organization_id')
        if not org_id:
            return Response({'error': 'organization_id es requerido'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            organization = Organization.objects.get(pk=org_id)
        except Organization.DoesNotExist:
            return Response({'error': 'Organizacion no encontrada'}, status=status.HTTP_404_NOT_FOUND)

        entitlements = self.get_queryset().filter(organization=organization)
        return Response({
            'organization_id': str(organization.id),
            'organization_name': organization.name,
            'products': OrganizationProductEntitlementSerializer(entitlements, many=True).data,
        })


class ISOStandardViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de estándares ISO
    Solo administradores de Comtech pueden crear/editar
    """
    queryset = ISOStandard.objects.all()
    permission_classes = [IsAuthenticated, IsAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'is_base']
    search_fields = ['code', 'name', 'full_name']
    ordering_fields = ['display_order', 'code', 'created_at']
    ordering = ['display_order', 'code']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ISOStandardListSerializer
        return ISOStandardSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsSuperAdmin()]
        return [IsAuthenticated(), IsAdmin()]
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Listar solo estándares activos/disponibles"""
        standards = ISOStandard.objects.filter(status__in=['active', 'beta'])
        serializer = ISOStandardListSerializer(standards, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def organizations(self, request, pk=None):
        """Ver qué organizaciones tienen este módulo"""
        iso_standard = self.get_object()
        modules = OrganizationModule.objects.filter(
            iso_standard=iso_standard
        ).select_related('organization')
        
        serializer = OrganizationModuleSerializer(modules, many=True)
        return Response(serializer.data)


class OrganizationModuleViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de módulos por organización
    CONTROL MAESTRO - Solo equipo Comtech
    """
    queryset = OrganizationModule.objects.all()
    permission_classes = [IsAuthenticated, IsAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['organization', 'iso_standard', 'status', 'is_enabled']
    search_fields = ['organization__name', 'organization__code', 'iso_standard__code']
    ordering_fields = ['created_at', 'activated_at', 'expires_at']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return OrganizationModuleCreateSerializer
        return OrganizationModuleSerializer
    
    def get_queryset(self):
        return OrganizationModule.objects.select_related(
            'organization', 'iso_standard', 'activated_by'
        )
    
    def perform_create(self, serializer):
        module = serializer.save(activated_by=self.request.user)
        
        # Registrar en log
        ModuleActivityLog.objects.create(
            organization_module=module,
            action='enabled',
            performed_by=self.request.user,
            notes=f"Módulo asignado inicialmente con status: {module.status}"
        )
    
    @action(detail=True, methods=['post'])
    def toggle(self, request, pk=None):
        """
        Activar/Desactivar módulo (abrir/cerrar la llave)
        POST /api/modules/{id}/toggle/
        Body: {"action": "enable|disable|trial", "reason": "...", "trial_days": 14}
        """
        module = self.get_object()
        serializer = OrganizationModuleToggleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        action_type = serializer.validated_data['action']
        reason = serializer.validated_data.get('reason', '')
        
        if action_type == 'enable':
            module.enable(user=request.user)
            log_action = 'enabled'
            message = f"Módulo {module.iso_standard.code} ACTIVADO para {module.organization.name}"
            
        elif action_type == 'disable':
            module.disable(reason=reason)
            log_action = 'disabled'
            message = f"Módulo {module.iso_standard.code} DESACTIVADO para {module.organization.name}"
            
        elif action_type == 'trial':
            trial_days = serializer.validated_data.get('trial_days', 14)
            module.set_trial(days=trial_days)
            log_action = 'trial_started'
            message = f"Módulo {module.iso_standard.code} en PRUEBA ({trial_days} días) para {module.organization.name}"
        
        # Registrar en log
        ModuleActivityLog.objects.create(
            organization_module=module,
            action=log_action,
            performed_by=request.user,
            notes=reason or message
        )
        
        return Response({
            'status': 'success',
            'message': message,
            'module': OrganizationModuleSerializer(module).data
        })
    
    @action(detail=False, methods=['get'])
    def by_organization(self, request):
        """
        Ver módulos agrupados por organización
        GET /api/modules/by_organization/?organization_id=xxx
        """
        org_id = request.query_params.get('organization_id')
        
        if org_id:
            # Validar que org_id sea un UUID válido
            if org_id == 'new' or len(org_id) < 10:
                return Response(
                    {'error': 'ID de organización inválido'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                organization = Organization.objects.get(pk=org_id)
            except Organization.DoesNotExist:
                return Response(
                    {'error': 'Organización no encontrada'},
                    status=status.HTTP_404_NOT_FOUND
                )
            except Exception as e:
                return Response(
                    {'error': 'ID de organización inválido'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            modules = OrganizationModule.objects.filter(
                organization=organization
            ).select_related('iso_standard')
            
            data = {
                'organization_id': str(organization.id),
                'organization_name': organization.name,
                'total_modules': modules.count(),
                'active_modules': modules.filter(is_enabled=True, status='active').count(),
                'trial_modules': modules.filter(status='trial').count(),
                'suspended_modules': modules.filter(status='suspended').count(),
                'modules': OrganizationModuleSerializer(modules, many=True).data
            }
            
            return Response(data)
        
        # Si no se especifica organización, devolver resumen de todas
        organizations = Organization.objects.annotate(
            modules_count=Count('iso_modules'),
            active_modules=Count('iso_modules', filter=Q(iso_modules__is_enabled=True, iso_modules__status='active'))
        ).filter(modules_count__gt=0)
        
        result = []
        for org in organizations:
            result.append({
                'organization_id': str(org.id),
                'organization_name': org.name,
                'organization_code': org.code,
                'total_modules': org.modules_count,
                'active_modules': org.active_modules,
            })
        
        return Response(result)
    
    @action(detail=False, methods=['post'])
    def bulk_assign(self, request):
        """
        Asignar múltiples módulos a una organización
        POST /api/modules/bulk_assign/
        Body: {"organization_id": "xxx", "iso_standards": ["uuid1", "uuid2"], "status": "trial"}
        """
        org_id = request.data.get('organization_id')
        iso_ids = request.data.get('iso_standards', [])
        initial_status = request.data.get('status', 'trial')
        
        # Validar que org_id sea válido
        if not org_id or org_id == 'new' or len(str(org_id)) < 10:
            return Response(
                {'error': 'ID de organización inválido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            organization = Organization.objects.get(pk=org_id)
        except Organization.DoesNotExist:
            return Response(
                {'error': 'Organización no encontrada'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': 'ID de organización inválido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        created = []
        skipped = []
        
        for iso_id in iso_ids:
            try:
                iso_standard = ISOStandard.objects.get(pk=iso_id)
                
                # Verificar si ya existe
                if OrganizationModule.objects.filter(
                    organization=organization, 
                    iso_standard=iso_standard
                ).exists():
                    skipped.append(iso_standard.code)
                    continue
                
                module = OrganizationModule.objects.create(
                    organization=organization,
                    iso_standard=iso_standard,
                    status=initial_status,
                    activated_by=request.user
                )
                
                if initial_status == 'trial':
                    module.set_trial(days=14)
                
                ModuleActivityLog.objects.create(
                    organization_module=module,
                    action='enabled' if initial_status == 'active' else 'trial_started',
                    performed_by=request.user,
                    notes=f"Asignación masiva - Status inicial: {initial_status}"
                )
                
                created.append(iso_standard.code)
                
            except ISOStandard.DoesNotExist:
                continue
        
        return Response({
            'status': 'success',
            'created': created,
            'skipped': skipped,
            'message': f"{len(created)} módulos asignados, {len(skipped)} ya existían"
        })


class ModuleActivityLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para consultar logs de actividad (solo lectura)
    Auditoría interna de Comtech
    """
    queryset = ModuleActivityLog.objects.all()
    serializer_class = ModuleActivityLogSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['organization_module__organization', 'organization_module__iso_standard', 'action']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return ModuleActivityLog.objects.select_related(
            'organization_module__organization',
            'organization_module__iso_standard',
            'performed_by'
        )
