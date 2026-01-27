"""
Views for Subscriptions - Admin Apps
"""
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db.models import Sum, Count, Q
from decimal import Decimal

from .models import Plan, Subscription, Invoice, PaymentMethod
from .serializers import (
    PlanListSerializer,
    PlanDetailSerializer,
    SubscriptionListSerializer,
    SubscriptionDetailSerializer,
    SubscriptionCreateSerializer,
    InvoiceListSerializer,
    InvoiceDetailSerializer,
    PaymentMethodSerializer,
    SubscriptionStatsSerializer,
)
from apps.users.permissions import IsSuperAdmin, IsAdmin, IsOrgAdmin


class PlanViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de planes
    """
    queryset = Plan.objects.all()
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['is_active', 'is_featured', 'billing_cycle']
    ordering_fields = ['display_order', 'price', 'name']
    ordering = ['display_order', 'price']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return PlanListSerializer
        return PlanDetailSerializer
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsSuperAdmin()]
    
    def get_queryset(self):
        queryset = Plan.objects.all()
        # Si no es admin, solo mostrar planes activos
        if not self.request.user.is_authenticated or not self.request.user.is_admin:
            queryset = queryset.filter(is_active=True)
        return queryset
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Obtener planes destacados"""
        plans = Plan.objects.filter(is_active=True, is_featured=True)
        serializer = PlanListSerializer(plans, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def compare(self, request, pk=None):
        """Comparar plan con otros"""
        plan = self.get_object()
        other_plans = Plan.objects.filter(is_active=True).exclude(pk=pk)
        
        comparison = {
            'current_plan': PlanDetailSerializer(plan).data,
            'other_plans': PlanListSerializer(other_plans, many=True).data
        }
        return Response(comparison)


class SubscriptionViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de suscripciones
    """
    queryset = Subscription.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'plan']
    ordering_fields = ['created_at', 'current_period_end']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return SubscriptionListSerializer
        elif self.action == 'create':
            return SubscriptionCreateSerializer
        return SubscriptionDetailSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'destroy']:
            return [IsAdmin()]
        return [IsAuthenticated()]
    
    def get_queryset(self):
        user = self.request.user
        queryset = Subscription.objects.all()
        
        if not user.is_admin:
            # Solo ver suscripción de su organización
            if user.organization:
                queryset = queryset.filter(organizations=user.organization)
            else:
                queryset = queryset.none()
        
        return queryset.select_related('plan')
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdmin])
    def activate(self, request, pk=None):
        """Activar suscripción"""
        subscription = self.get_object()
        subscription.activate()
        return Response({'status': 'activated'})
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdmin])
    def cancel(self, request, pk=None):
        """Cancelar suscripción"""
        subscription = self.get_object()
        subscription.cancel()
        return Response({'status': 'cancelled'})
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdmin])
    def change_plan(self, request, pk=None):
        """Cambiar plan de suscripción"""
        subscription = self.get_object()
        new_plan_id = request.data.get('plan_id')
        
        if not new_plan_id:
            return Response(
                {'error': 'Se requiere plan_id'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            new_plan = Plan.objects.get(pk=new_plan_id, is_active=True)
        except Plan.DoesNotExist:
            return Response(
                {'error': 'Plan no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        subscription.plan = new_plan
        subscription.amount = new_plan.price
        subscription.save()
        
        return Response({
            'status': 'plan_changed',
            'new_plan': new_plan.name
        })
    
    @action(detail=False, methods=['get'], permission_classes=[IsAdmin])
    def stats(self, request):
        """Obtener estadísticas de suscripciones"""
        now = timezone.now()
        this_month_start = now.replace(day=1, hour=0, minute=0, second=0)
        last_month_start = (this_month_start - timezone.timedelta(days=1)).replace(day=1)
        
        stats = {
            'total_active': Subscription.objects.filter(status='active').count(),
            'total_trial': Subscription.objects.filter(status='trial').count(),
            'total_cancelled': Subscription.objects.filter(status='cancelled').count(),
            'revenue_this_month': Invoice.objects.filter(
                status='paid',
                paid_at__gte=this_month_start
            ).aggregate(total=Sum('total'))['total'] or Decimal('0.00'),
            'revenue_last_month': Invoice.objects.filter(
                status='paid',
                paid_at__gte=last_month_start,
                paid_at__lt=this_month_start
            ).aggregate(total=Sum('total'))['total'] or Decimal('0.00'),
            'churn_rate': 0.0  # TODO: Calcular tasa de abandono
        }
        
        serializer = SubscriptionStatsSerializer(stats)
        return Response(serializer.data)


class InvoiceViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de facturas
    """
    queryset = Invoice.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'organization']
    search_fields = ['number']
    ordering_fields = ['issued_at', 'due_date', 'total']
    ordering = ['-issued_at']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return InvoiceListSerializer
        return InvoiceDetailSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdmin()]
        return [IsAuthenticated()]
    
    def get_queryset(self):
        user = self.request.user
        queryset = Invoice.objects.all()
        
        if not user.is_admin:
            queryset = queryset.filter(organization=user.organization)
        
        return queryset.select_related('organization', 'subscription__plan')
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdmin])
    def mark_paid(self, request, pk=None):
        """Marcar factura como pagada"""
        invoice = self.get_object()
        invoice.status = 'paid'
        invoice.paid_at = timezone.now()
        invoice.payment_reference = request.data.get('payment_reference', '')
        invoice.save()
        
        # Activar suscripción si estaba pendiente
        if invoice.subscription and invoice.subscription.status in ['trial', 'past_due']:
            invoice.subscription.activate()
        
        return Response({'status': 'paid'})
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Descargar factura en PDF"""
        invoice = self.get_object()
        # TODO: Generar PDF
        return Response({'url': f'/api/invoices/{invoice.id}/pdf/'})


class PaymentMethodViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de métodos de pago
    """
    queryset = PaymentMethod.objects.all()
    serializer_class = PaymentMethodSerializer
    permission_classes = [IsAuthenticated, IsOrgAdmin]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_admin:
            org_id = self.request.query_params.get('organization')
            if org_id:
                return PaymentMethod.objects.filter(organization_id=org_id)
            return PaymentMethod.objects.all()
        return PaymentMethod.objects.filter(organization=user.organization)
    
    def perform_create(self, serializer):
        organization = self.request.user.organization
        if self.request.user.is_admin:
            org_id = self.request.data.get('organization')
            if org_id:
                from apps.organizations.models import Organization
                organization = Organization.objects.get(pk=org_id)
        
        serializer.save(organization=organization)
    
    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        """Establecer como método de pago predeterminado"""
        payment_method = self.get_object()
        
        # Quitar default de otros
        PaymentMethod.objects.filter(
            organization=payment_method.organization,
            is_default=True
        ).update(is_default=False)
        
        payment_method.is_default = True
        payment_method.save()
        
        return Response({'status': 'default_set'})
