import React, { useState, useEffect } from 'react';
import { 
  CreditCard, 
  Plus, 
  Search,
  Building2,
  Calendar,
  DollarSign,
  CheckCircle,
  AlertTriangle,
  Clock,
  XCircle,
  ExternalLink,
  FileText,
  BadgeCheck
} from 'lucide-react';
import { subscriptionService } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import toast from 'react-hot-toast';
import { showConfirm } from '../services/dialogs';

// Subscription Card Component
const SubscriptionCard = ({ subscription, t, isEnglish, onView, onManage }) => {
  const amount = subscription.amount ?? subscription.plan?.price ?? 0;
  const nextPaymentDate = subscription.next_payment_date || subscription.next_billing_date || subscription.current_period_end;
  const orgName = subscription.organization_name || `${isEnglish ? 'Subscription' : 'Suscripcion'} #${String(subscription.id).slice(0, 8)}`;

  const statusConfig = {
    active: { color: 'text-emerald-400', bg: 'bg-emerald-500/10', border: 'border-emerald-500/30', icon: CheckCircle, label: t.activeLabel },
    trial: { color: 'text-cyan-400', bg: 'bg-cyan-500/10', border: 'border-cyan-500/30', icon: Clock, label: 'Trial' },
    past_due: { color: 'text-amber-400', bg: 'bg-amber-500/10', border: 'border-amber-500/30', icon: AlertTriangle, label: t.overdue },
    cancelled: { color: 'text-red-400', bg: 'bg-red-500/10', border: 'border-red-500/30', icon: XCircle, label: t.cancelled },
    expired: { color: 'text-gray-400', bg: 'bg-gray-500/10', border: 'border-gray-500/30', icon: XCircle, label: t.expired },
  };

  const config = statusConfig[subscription.status] || statusConfig.active;
  const StatusIcon = config.icon;

  return (
    <div className="glass-card-hover p-6">
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary-500/20 to-primary-600/20 flex items-center justify-center">
            <Building2 className="w-6 h-6 text-primary-400" />
          </div>
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h3 className="font-semibold text-gray-100">{orgName}</h3>
              {subscription.billing_exempt && (
                <span className="inline-flex items-center gap-1 rounded-full border border-emerald-400/30 bg-emerald-500/10 px-2 py-0.5 text-[11px] font-medium text-emerald-300">
                  <BadgeCheck className="h-3 w-3" />
                  {t.billingExempt}
                </span>
              )}
            </div>
            <p className="text-sm text-gray-500">{subscription.plan_name}</p>
          </div>
        </div>
        <div className={`flex items-center gap-2 px-3 py-1 rounded-full ${config.bg} ${config.border} border`}>
          <StatusIcon className={`w-4 h-4 ${config.color}`} />
          <span className={`text-sm font-medium ${config.color}`}>{config.label}</span>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="p-3 bg-dark-400/30 rounded-lg">
          <div className="flex items-center gap-2 text-gray-500 text-sm mb-1">
            <DollarSign className="w-4 h-4" />
            <span>{t.amount}</span>
          </div>
          <p className="text-lg font-semibold text-gray-100">{subscription.billing_exempt ? t.exemptAmount : `$${Number(amount).toLocaleString()}/${isEnglish ? 'month' : 'mes'}`}</p>
        </div>
        <div className="p-3 bg-dark-400/30 rounded-lg">
          <div className="flex items-center gap-2 text-gray-500 text-sm mb-1">
            <Calendar className="w-4 h-4" />
            <span>{t.nextPayment}</span>
          </div>
          <p className="text-lg font-semibold text-gray-100">
            {nextPaymentDate 
              ? new Date(nextPaymentDate).toLocaleDateString(isEnglish ? 'en-US' : 'es-MX', { day: 'numeric', month: 'short' })
              : '-'
            }
          </p>
        </div>
      </div>

      <div className="flex gap-2">
        <button onClick={() => onView(subscription)} className="flex-1 btn-secondary py-2 text-sm">{t.viewDetails}</button>
        <button onClick={() => onManage(subscription)} className="flex-1 btn-primary py-2 text-sm">{t.manage}</button>
      </div>
    </div>
  );
};

// Plan Card Component
const PlanCard = ({ plan, featured, t, isEnglish, onSelect }) => (
  <div className={`
    glass-card p-6 relative overflow-hidden
    ${featured ? 'border-primary-500/50 ring-2 ring-primary-500/20' : ''}
  `}>
    {featured && (
      <div className="absolute top-4 right-4 px-3 py-1 bg-primary-500 text-white text-xs font-semibold rounded-full">
        {t.popular}
      </div>
    )}
    
    <h3 className="text-xl font-bold text-gray-100">{plan.name}</h3>
    <p className="text-gray-500 text-sm mt-1">{plan.description}</p>
    
    <div className="mt-4">
      <span className="text-3xl font-bold text-gray-100">${plan.price}</span>
      <span className="text-gray-500">/{isEnglish ? 'month' : 'mes'}</span>
    </div>
    
    <ul className="mt-6 space-y-3">
      {(plan.features || []).map((feature, index) => (
        <li key={index} className="flex items-center gap-2 text-sm text-gray-300">
          <CheckCircle className="w-4 h-4 text-emerald-400 flex-shrink-0" />
          {feature}
        </li>
      ))}
    </ul>
    
    <button onClick={() => onSelect(plan)} className={`w-full mt-6 py-2.5 ${featured ? 'btn-primary' : 'btn-secondary'}`}>
      {t.selectPlan}
    </button>
  </div>
);

const SubscriptionDetailModal = ({
  isOpen,
  onClose,
  details,
  plans,
  invoices,
  invoicesUnavailable,
  t,
  isEnglish,
  onActivate,
  onCancel,
  onChangePlan,
  onOpenInvoice,
  onMarkInvoicePaid,
  canMarkInvoices,
  invoiceUpdatingId,
  actionLoading,
}) => {
  const usage = details?.usage_percentage || {};
  const canActivate = details?.status === 'trial' || details?.status === 'past_due';
  const canCancel = details?.status === 'active' || details?.status === 'trial' || details?.status === 'past_due';
  const nextDate = details?.next_billing_date || details?.current_period_end;
  const currentPlanId = details?.plan?.id || details?.plan;
  const [selectedPlanId, setSelectedPlanId] = useState(currentPlanId || '');
  const [paymentReferences, setPaymentReferences] = useState({});

  useEffect(() => {
    setSelectedPlanId(currentPlanId || '');
  }, [currentPlanId, isOpen]);

  useEffect(() => {
    const initialRefs = {};
    invoices.forEach((invoice) => {
      initialRefs[invoice.id] = invoice.payment_reference || '';
    });
    setPaymentReferences(initialRefs);
  }, [invoices]);

  if (!isOpen || !details) return null;

  const getInvoiceStatusBadge = (status) => {
    const map = {
      paid: 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30',
      pending: 'bg-amber-500/10 text-amber-300 border-amber-500/30',
      overdue: 'bg-red-500/10 text-red-300 border-red-500/30',
      cancelled: 'bg-gray-500/10 text-gray-300 border-gray-500/30',
      draft: 'bg-cyan-500/10 text-cyan-300 border-cyan-500/30',
      refunded: 'bg-purple-500/10 text-purple-300 border-purple-500/30',
    };

    return map[status] || 'bg-gray-500/10 text-gray-300 border-gray-500/30';
  };

  const handleChangePlan = () => {
    if (!selectedPlanId || selectedPlanId === currentPlanId) return;
    onChangePlan(selectedPlanId);
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/65 backdrop-blur-sm p-4 md:p-6" onClick={onClose}>
      <div className="glass-card mx-auto w-full max-w-2xl max-h-[90vh] overflow-y-auto shadow-2xl" onClick={(e) => e.stopPropagation()}>
        <div className="border-b border-gray-700/50 px-5 py-4 md:px-6 md:py-5 flex items-center justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.2em] text-primary-300">{isEnglish ? 'Subscription detail' : 'Detalle de suscripcion'}</p>
            <div className="mt-1 flex flex-wrap items-center gap-2">
              <h2 className="text-xl font-semibold text-gray-100">{details.plan?.name || details.plan_name || '-'}</h2>
              {details.billing_exempt && (
                <span className="inline-flex items-center gap-1 rounded-full border border-emerald-400/30 bg-emerald-500/10 px-2 py-0.5 text-[11px] font-medium text-emerald-300">
                  <BadgeCheck className="h-3 w-3" />
                  {t.billingExempt}
                </span>
              )}
            </div>
            {details.organization_name && <p className="mt-1 text-sm text-gray-500">{details.organization_name}</p>}
          </div>
          <button onClick={onClose} className="rounded-lg p-2 text-gray-400 hover:bg-dark-300 hover:text-gray-200 transition-colors">✕</button>
        </div>

        <div className="px-5 py-5 md:px-6 md:py-6 space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="rounded-xl border border-gray-700/50 bg-dark-400/25 p-4">
              <p className="text-xs uppercase tracking-widest text-gray-500 mb-2">{isEnglish ? 'Status' : 'Estado'}</p>
              <p className="text-base font-semibold text-gray-100">{details.status}</p>
            </div>
            <div className="rounded-xl border border-gray-700/50 bg-dark-400/25 p-4">
              <p className="text-xs uppercase tracking-widest text-gray-500 mb-2">{t.nextPayment}</p>
              <p className="text-base font-semibold text-gray-100">{details.billing_exempt ? t.noChargeCycle : (nextDate ? new Date(nextDate).toLocaleDateString(isEnglish ? 'en-US' : 'es-MX') : '-')}</p>
            </div>
            <div className="rounded-xl border border-gray-700/50 bg-dark-400/25 p-4">
              <p className="text-xs uppercase tracking-widest text-gray-500 mb-2">{t.amount}</p>
              <p className="text-base font-semibold text-gray-100">{details.billing_exempt ? t.exemptAmount : `$${Number(details.amount || details.plan?.price || 0).toLocaleString()}`}</p>
            </div>
          </div>

          <div className="rounded-xl border border-gray-700/50 bg-dark-400/25 p-4 space-y-3">
            <p className="text-xs uppercase tracking-widest text-gray-500">{isEnglish ? 'Usage' : 'Uso'}</p>
            {[
              { key: 'users', label: isEnglish ? 'Users' : 'Usuarios' },
              { key: 'documents', label: isEnglish ? 'Documents' : 'Documentos' },
              { key: 'storage', label: isEnglish ? 'Storage' : 'Almacenamiento' },
            ].map((item) => {
              const value = Math.min(100, Math.max(0, Number(usage[item.key] || 0)));
              return (
                <div key={item.key}>
                  <div className="flex items-center justify-between text-sm text-gray-300 mb-1">
                    <span>{item.label}</span>
                    <span>{value.toFixed(0)}%</span>
                  </div>
                  <div className="h-2 rounded-full bg-dark-300 overflow-hidden">
                    <div className="h-full bg-primary-500" style={{ width: `${value}%` }} />
                  </div>
                </div>
              );
            })}
          </div>

          <div className="rounded-xl border border-gray-700/50 bg-dark-400/25 p-4 space-y-3">
            <p className="text-xs uppercase tracking-widest text-gray-500">{t.changePlan}</p>
            {details.billing_exempt ? (
              <div className="rounded-lg border border-emerald-400/25 bg-emerald-500/10 px-3 py-2 text-sm text-emerald-200">
                {t.ownerExemptNote}
              </div>
            ) : (
              <div className="flex flex-col sm:flex-row gap-3">
                <select
                  value={selectedPlanId}
                  onChange={(e) => setSelectedPlanId(e.target.value)}
                  className="input-glass flex-1"
                >
                  <option value="">{t.selectPlan}</option>
                  {plans.map((plan) => (
                    <option key={plan.id} value={plan.id}>
                      {plan.name} - ${Number(plan.price || 0).toLocaleString()}
                    </option>
                  ))}
                </select>
                <button
                  onClick={handleChangePlan}
                  disabled={actionLoading || !selectedPlanId || selectedPlanId === currentPlanId}
                  className="btn-secondary disabled:opacity-60"
                >
                  {actionLoading ? t.processing : t.updatePlan}
                </button>
              </div>
            )}
          </div>

          <div className="rounded-xl border border-gray-700/50 bg-dark-400/25 p-4 space-y-3">
            <p className="text-xs uppercase tracking-widest text-gray-500">{t.recentInvoices}</p>
            {invoicesUnavailable ? (
              <p className="text-sm text-gray-500">{t.invoicesUnavailable}</p>
            ) : invoices.length === 0 ? (
              <p className="text-sm text-gray-500">{t.noInvoices}</p>
            ) : (
              <div className="space-y-2">
                {invoices.slice(0, 4).map((invoice) => (
                  <div key={invoice.id} className="flex items-center justify-between rounded-lg border border-gray-700/40 px-3 py-2">
                    <div>
                      <p className="text-sm text-gray-200">{invoice.number || `INV-${String(invoice.id).slice(0, 8)}`}</p>
                      <div className="mt-1 flex flex-wrap items-center gap-2">
                        <span className={`inline-flex items-center px-2 py-0.5 rounded-full border text-[11px] ${getInvoiceStatusBadge(invoice.status)}`}>
                          {invoice.status || '-'}
                        </span>
                        {invoice.billing_exempt && (
                          <span className="inline-flex items-center gap-1 rounded-full border border-emerald-400/30 bg-emerald-500/10 px-2 py-0.5 text-[11px] font-medium text-emerald-300">
                            <BadgeCheck className="h-3 w-3" />
                            {t.billingExempt}
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="text-right flex items-center gap-3">
                      <button
                        onClick={() => onOpenInvoice(invoice)}
                        className="inline-flex items-center gap-1.5 text-xs text-primary-300 hover:text-primary-200 transition-colors"
                      >
                        <FileText className="w-3.5 h-3.5" />
                        {t.viewInvoice}
                        <ExternalLink className="w-3 h-3" />
                      </button>

                      {canMarkInvoices && (invoice.status === 'pending' || invoice.status === 'overdue' || invoice.status === 'draft') && (
                        <div className="flex items-center gap-2">
                          <input
                            type="text"
                            value={paymentReferences[invoice.id] || ''}
                            onChange={(e) => setPaymentReferences((prev) => ({ ...prev, [invoice.id]: e.target.value }))}
                            placeholder={t.paymentRefPlaceholder}
                            className="input-glass h-8 min-w-[180px] text-xs"
                          />
                          <button
                            onClick={() => onMarkInvoicePaid(invoice, paymentReferences[invoice.id] || '')}
                            disabled={invoiceUpdatingId === invoice.id}
                            className="inline-flex items-center gap-1.5 text-xs text-emerald-300 hover:text-emerald-200 transition-colors disabled:opacity-60"
                          >
                            <CheckCircle className="w-3.5 h-3.5" />
                            {invoiceUpdatingId === invoice.id ? t.processing : t.markPaid}
                          </button>
                        </div>
                      )}
                      
                      <div>
                      <p className="text-sm text-gray-100">${Number(invoice.total || 0).toLocaleString()}</p>
                      <p className="text-xs text-gray-500">
                        {invoice.issued_at ? new Date(invoice.issued_at).toLocaleDateString(isEnglish ? 'en-US' : 'es-MX') : '-'}
                      </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="flex flex-col sm:flex-row gap-3 sm:justify-end">
            {canActivate && (
              <button
                onClick={onActivate}
                disabled={actionLoading}
                className="btn-primary disabled:opacity-60"
              >
                {actionLoading ? (isEnglish ? 'Processing...' : 'Procesando...') : (isEnglish ? 'Activate' : 'Activar')}
              </button>
            )}
            {canCancel && (
              <button
                onClick={onCancel}
                disabled={actionLoading}
                className="btn-secondary text-red-300 border-red-500/40 hover:bg-red-500/10 disabled:opacity-60"
              >
                {actionLoading ? (isEnglish ? 'Processing...' : 'Procesando...') : (isEnglish ? 'Cancel subscription' : 'Cancelar suscripcion')}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

const SubscriptionsPage = () => {
  const { user } = useAuth();
  const isEnglish = user?.language === 'en';
  const t = {
    activeLabel: isEnglish ? 'Active' : 'Activa',
    overdue: isEnglish ? 'Overdue' : 'Vencida',
    cancelled: isEnglish ? 'Cancelled' : 'Cancelada',
    expired: isEnglish ? 'Expired' : 'Expirada',
    amount: isEnglish ? 'Amount' : 'Monto',
    nextPayment: isEnglish ? 'Next Payment' : 'Proximo Pago',
    viewDetails: isEnglish ? 'View Details' : 'Ver Detalles',
    manage: isEnglish ? 'Manage' : 'Gestionar',
    popular: isEnglish ? 'Popular' : 'Popular',
    selectPlan: isEnglish ? 'Select Plan' : 'Seleccionar Plan',
    pageTitle: isEnglish ? 'Subscriptions' : 'Suscripciones',
    pageSubtitle: isEnglish ? 'Manage plans and subscriptions' : 'Gestiona planes y suscripciones',
    newSubscription: isEnglish ? 'New Subscription' : 'Nueva Suscripcion',
    totalSubscriptions: isEnglish ? 'Total Subscriptions' : 'Total Suscripciones',
    active: isEnglish ? 'Active' : 'Activas',
    inTrial: isEnglish ? 'In Trial' : 'En Trial',
    subscriptionsTab: isEnglish ? 'Subscriptions' : 'Suscripciones',
    plansTab: isEnglish ? 'Plans' : 'Planes',
    searchPlaceholder: isEnglish ? 'Search by organization...' : 'Buscar por organizacion...',
    allStatuses: isEnglish ? 'All statuses' : 'Todos los estados',
    cancelledPlural: isEnglish ? 'Cancelled' : 'Canceladas',
    overduePlural: isEnglish ? 'Overdue' : 'Vencidas',
    noSubscriptions: isEnglish ? 'No subscriptions found' : 'No se encontraron suscripciones',
    loadError: isEnglish ? 'Could not load subscriptions from API, showing demo data.' : 'No se pudieron cargar suscripciones del API, mostrando datos demo.',
    createdOk: isEnglish ? 'Subscription created in trial mode.' : 'Suscripcion creada en modo prueba.',
    createdError: isEnglish ? 'Could not create subscription.' : 'No se pudo crear la suscripcion.',
    activatedOk: isEnglish ? 'Subscription activated.' : 'Suscripcion activada.',
    activateError: isEnglish ? 'Could not activate subscription.' : 'No se pudo activar la suscripcion.',
    cancelledOk: isEnglish ? 'Subscription cancelled.' : 'Suscripcion cancelada.',
    cancelError: isEnglish ? 'Could not cancel subscription.' : 'No se pudo cancelar la suscripcion.',
    confirmCancel: isEnglish ? 'Do you want to cancel this subscription?' : 'Deseas cancelar esta suscripcion?',
    changePlan: isEnglish ? 'Change plan' : 'Cambiar plan',
    updatePlan: isEnglish ? 'Update plan' : 'Actualizar plan',
    updatedPlanOk: isEnglish ? 'Plan updated successfully.' : 'Plan actualizado correctamente.',
    updatePlanError: isEnglish ? 'Could not update plan.' : 'No se pudo actualizar el plan.',
    recentInvoices: isEnglish ? 'Recent invoices' : 'Facturas recientes',
    noInvoices: isEnglish ? 'No invoices available.' : 'No hay facturas disponibles.',
    invoicesUnavailable: isEnglish ? 'Invoice endpoint is not available yet.' : 'El endpoint de facturas aun no esta disponible.',
    processing: isEnglish ? 'Processing...' : 'Procesando...',
    viewInvoice: isEnglish ? 'View invoice' : 'Ver factura',
    openInvoiceError: isEnglish ? 'Could not open invoice.' : 'No se pudo abrir la factura.',
    markPaid: isEnglish ? 'Mark paid' : 'Marcar pagada',
    markPaidOk: isEnglish ? 'Invoice marked as paid.' : 'Factura marcada como pagada.',
    markPaidError: isEnglish ? 'Could not mark invoice as paid.' : 'No se pudo marcar la factura como pagada.',
    paymentRefPlaceholder: isEnglish ? 'Payment reference (optional)' : 'Referencia de pago (opcional)',
    billingExempt: isEnglish ? 'Billing exempt' : 'Exenta de cobro',
    exemptAmount: isEnglish ? 'Exempt' : 'Exento',
    noChargeCycle: isEnglish ? 'No charge cycle' : 'Sin ciclo de cobro',
    ownerExemptNote: isEnglish ? 'This owner organization is exempt from billing, so manual plan changes and charge cycles do not apply.' : 'Esta organizacion dueña esta exenta de cobro, por lo que no aplican cambios manuales de plan ni ciclos de cobro.',
  };
  const [subscriptions, setSubscriptions] = useState([]);
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('subscriptions');
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [selectedSubscription, setSelectedSubscription] = useState(null);
  const [subscriptionDetails, setSubscriptionDetails] = useState(null);
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [invoiceUpdatingId, setInvoiceUpdatingId] = useState(null);
  const [subscriptionInvoices, setSubscriptionInvoices] = useState([]);
  const [invoicesUnavailable, setInvoicesUnavailable] = useState(false);
  const canMarkInvoices = Boolean(user?.is_admin || user?.role === 'admin' || user?.role === 'superadmin');

  const normalizeList = (data) => (Array.isArray(data) ? data : (data?.results || []));

  const fetchData = async () => {
    setLoading(true);
    try {
      const [subsData, plansData] = await Promise.all([
        subscriptionService.getAll(),
        subscriptionService.getPlans(),
      ]);
      setSubscriptions(normalizeList(subsData));
      setPlans(normalizeList(plansData));
    } catch (error) {
      toast.error(t.loadError);
      setSubscriptions([
        { id: '1', organization_name: 'Tech Corp', plan_name: 'Premium', status: 'active', amount: 499, next_payment_date: '2026-02-15' },
        { id: '2', organization_name: 'Acme Inc', plan_name: 'Basico', status: 'active', amount: 199, next_payment_date: '2026-02-20' },
        { id: '3', organization_name: 'StartupXYZ', plan_name: 'Trial', status: 'trial', amount: 0, next_payment_date: '2026-02-10' },
        { id: '4', organization_name: 'Global Services', plan_name: 'Enterprise', status: 'active', amount: 999, next_payment_date: '2026-03-01' },
        { id: '5', organization_name: 'Local Shop', plan_name: 'Basico', status: 'past_due', amount: 199, next_payment_date: '2026-01-25' },
        { id: '6', organization_name: 'Old Company', plan_name: 'Basico', status: 'cancelled', amount: 199, next_payment_date: null },
      ]);
      setPlans([
        {
          id: '1',
          name: isEnglish ? 'Basic' : 'Basico',
          description: isEnglish ? 'For small businesses' : 'Para pequenas empresas',
          price: 199,
          features: isEnglish
            ? ['Up to 5 users', '100 documents', '500 MB storage', 'Core ISO modules', 'Email support']
            : ['Hasta 5 usuarios', '100 documentos', '500 MB almacenamiento', 'Modulos basicos ISO', 'Soporte por email'],
        },
        {
          id: '2',
          name: 'Premium',
          description: isEnglish ? 'For growing businesses' : 'Para empresas en crecimiento',
          price: 499,
          features: isEnglish
            ? ['Up to 20 users', '500 documents', '2 GB storage', 'All ISO modules', 'AI analytics', 'Priority support']
            : ['Hasta 20 usuarios', '500 documentos', '2 GB almacenamiento', 'Todos los modulos ISO', 'Analisis IA', 'Soporte prioritario'],
        },
        {
          id: '3',
          name: 'Enterprise',
          description: isEnglish ? 'For enterprise organizations' : 'Para grandes corporativos',
          price: 999,
          features: isEnglish
            ? ['Unlimited users', 'Unlimited documents', '10 GB storage', 'All ISO modules', 'Advanced AI analytics', 'API access', '24/7 support']
            : ['Usuarios ilimitados', 'Documentos ilimitados', '10 GB almacenamiento', 'Todos los modulos ISO', 'Analisis IA avanzado', 'API acceso', 'Soporte 24/7'],
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [isEnglish]);

  const handleViewDetails = async (subscription) => {
    setSelectedSubscription(subscription);
    setDetailsOpen(true);
    setSubscriptionDetails(null);
    setSubscriptionInvoices([]);
    setInvoicesUnavailable(false);

    const [detailsResult, invoicesResult] = await Promise.allSettled([
      subscriptionService.getById(subscription.id),
      subscriptionService.getInvoices(subscription.id),
    ]);

    if (detailsResult.status === 'fulfilled') {
      setSubscriptionDetails(detailsResult.value);
    } else {
      setSubscriptionDetails(subscription);
    }

    if (invoicesResult.status === 'fulfilled') {
      const rawInvoices = invoicesResult.value;
      const normalized = Array.isArray(rawInvoices) ? rawInvoices : (rawInvoices?.results || []);
      setSubscriptionInvoices(normalized);
      setInvoicesUnavailable(false);
    } else {
      setSubscriptionInvoices([]);
      setInvoicesUnavailable(true);
    }
  };

  const handleManage = async (subscription) => {
    await handleViewDetails(subscription);
  };

  const handleSelectPlan = async (plan) => {
    try {
      await subscriptionService.create({ plan: plan.id });
      toast.success(t.createdOk);
      setActiveTab('subscriptions');
      await fetchData();
    } catch (error) {
      toast.error(error?.response?.data?.error || error?.response?.data?.detail || t.createdError);
    }
  };

  const handleActivate = async () => {
    if (!selectedSubscription) return;
    setActionLoading(true);
    try {
      await subscriptionService.activate(selectedSubscription.id);
      toast.success(t.activatedOk);
      await fetchData();
      await handleViewDetails(selectedSubscription);
    } catch (error) {
      toast.error(error?.response?.data?.error || t.activateError);
    } finally {
      setActionLoading(false);
    }
  };

  const handleCancelSubscription = async () => {
    if (!selectedSubscription) return;
    const isEnglish = document.documentElement.lang === 'en';
    const confirmed = await showConfirm({
      title: isEnglish ? 'Cancel subscription' : 'Cancelar suscripcion',
      text: t.confirmCancel,
      confirmButtonText: isEnglish ? 'Cancel subscription' : 'Cancelar suscripcion',
      cancelButtonText: isEnglish ? 'Keep active' : 'Mantener activa',
    });
    if (!confirmed) return;

    setActionLoading(true);
    try {
      await subscriptionService.cancel(selectedSubscription.id);
      toast.success(t.cancelledOk);
      await fetchData();
      await handleViewDetails(selectedSubscription);
    } catch (error) {
      toast.error(error?.response?.data?.error || t.cancelError);
    } finally {
      setActionLoading(false);
    }
  };

  const handleChangePlan = async (planId) => {
    if (!selectedSubscription || !planId) return;
    setActionLoading(true);
    try {
      await subscriptionService.changePlan(selectedSubscription.id, planId);
      toast.success(t.updatedPlanOk);
      await fetchData();
      await handleViewDetails(selectedSubscription);
    } catch (error) {
      toast.error(error?.response?.data?.error || t.updatePlanError);
    } finally {
      setActionLoading(false);
    }
  };

  const handleOpenInvoice = async (invoice) => {
    if (!invoice?.id) return;

    try {
      const response = await subscriptionService.downloadInvoice(invoice.id);
      const rawUrl = response?.url;
      const baseUrl = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '');
      const finalUrl = rawUrl
        ? (rawUrl.startsWith('http') ? rawUrl : `${baseUrl}${rawUrl}`)
        : `${baseUrl}/subscriptions/invoices/${invoice.id}/download/`;

      window.open(finalUrl, '_blank', 'noopener,noreferrer');
    } catch (error) {
      toast.error(t.openInvoiceError);
    }
  };

  const handleMarkInvoicePaid = async (invoice, paymentReference = '') => {
    if (!invoice?.id || !selectedSubscription) return;

    setInvoiceUpdatingId(invoice.id);
    try {
      await subscriptionService.markInvoicePaid(invoice.id, paymentReference);
      toast.success(t.markPaidOk);
      await fetchData();
      await handleViewDetails(selectedSubscription);
    } catch (error) {
      toast.error(error?.response?.data?.error || t.markPaidError);
    } finally {
      setInvoiceUpdatingId(null);
    }
  };

  const filteredSubscriptions = subscriptions.filter((sub) => {
    const matchesSearch = (sub.organization_name || '').toLowerCase().includes(search.toLowerCase());
    const matchesStatus = !statusFilter || sub.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  // Stats
  const stats = {
    total: subscriptions.length,
    active: subscriptions.filter(s => s.status === 'active').length,
    trial: subscriptions.filter(s => s.status === 'trial').length,
    pastDue: subscriptions.filter(s => s.status === 'past_due').length,
    mrr: subscriptions
      .filter(s => s.status === 'active')
      .reduce((sum, s) => sum + Number(s.amount || 0), 0),
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-12 w-64 skeleton rounded-lg" />
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map(i => <div key={i} className="h-24 skeleton rounded-xl" />)}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-100">{t.pageTitle}</h1>
          <p className="text-gray-500 mt-1">{t.pageSubtitle}</p>
        </div>
        <button onClick={() => setActiveTab('plans')} className="btn-primary flex items-center gap-2">
          <Plus className="w-5 h-5" />
          {t.newSubscription}
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="glass-card p-4">
          <p className="text-gray-500 text-sm">{t.totalSubscriptions}</p>
          <p className="text-2xl font-bold text-gray-100 mt-1">{stats.total}</p>
        </div>
        <div className="glass-card p-4">
          <p className="text-gray-500 text-sm">{t.active}</p>
          <p className="text-2xl font-bold text-emerald-400 mt-1">{stats.active}</p>
        </div>
        <div className="glass-card p-4">
          <p className="text-gray-500 text-sm">{t.inTrial}</p>
          <p className="text-2xl font-bold text-cyan-400 mt-1">{stats.trial}</p>
        </div>
        <div className="glass-card p-4">
          <p className="text-gray-500 text-sm">MRR</p>
          <p className="text-2xl font-bold text-gray-100 mt-1">${(stats.mrr || 0).toLocaleString()}</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2">
        <button
          onClick={() => setActiveTab('subscriptions')}
          className={`px-4 py-2 rounded-lg font-medium transition-colors ${
            activeTab === 'subscriptions' 
              ? 'bg-primary-500/20 text-primary-400' 
              : 'text-gray-400 hover:text-gray-200 hover:bg-dark-200/50'
          }`}
        >
          {t.subscriptionsTab}
        </button>
        <button
          onClick={() => setActiveTab('plans')}
          className={`px-4 py-2 rounded-lg font-medium transition-colors ${
            activeTab === 'plans' 
              ? 'bg-primary-500/20 text-primary-400' 
              : 'text-gray-400 hover:text-gray-200 hover:bg-dark-200/50'
          }`}
        >
          {t.plansTab}
        </button>
      </div>

      {/* Content */}
      {activeTab === 'subscriptions' && (
        <>
          {/* Filters */}
          <div className="glass-card p-4">
            <div className="flex flex-col sm:flex-row gap-4">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
                <input
                  type="text"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder={t.searchPlaceholder}
                  className="input-glass pl-11"
                />
              </div>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="input-glass w-auto"
              >
                <option value="">{t.allStatuses}</option>
                <option value="active">{t.active}</option>
                <option value="trial">Trial</option>
                <option value="past_due">{t.overduePlural}</option>
                <option value="cancelled">{t.cancelledPlural}</option>
              </select>
            </div>
          </div>

          {/* Subscriptions Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredSubscriptions.map((subscription) => (
              <SubscriptionCard
                key={subscription.id}
                subscription={subscription}
                t={t}
                isEnglish={isEnglish}
                onView={handleViewDetails}
                onManage={handleManage}
              />
            ))}
          </div>

          {filteredSubscriptions.length === 0 && (
            <div className="glass-card p-8 text-center">
              <CreditCard className="w-12 h-12 text-gray-600 mx-auto mb-4" />
              <p className="text-gray-400">{t.noSubscriptions}</p>
            </div>
          )}
        </>
      )}

      {activeTab === 'plans' && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {plans.map((plan, index) => (
            <PlanCard
              key={plan.id}
              plan={plan}
              featured={index === 1}
              t={t}
              isEnglish={isEnglish}
              onSelect={handleSelectPlan}
            />
          ))}
        </div>
      )}

      <SubscriptionDetailModal
        isOpen={detailsOpen}
        onClose={() => setDetailsOpen(false)}
        details={subscriptionDetails}
        plans={plans}
        invoices={subscriptionInvoices}
        invoicesUnavailable={invoicesUnavailable}
        t={t}
        isEnglish={isEnglish}
        onActivate={handleActivate}
        onCancel={handleCancelSubscription}
        onChangePlan={handleChangePlan}
        onOpenInvoice={handleOpenInvoice}
        onMarkInvoicePaid={handleMarkInvoicePaid}
        canMarkInvoices={canMarkInvoices}
        invoiceUpdatingId={invoiceUpdatingId}
        actionLoading={actionLoading}
      />
    </div>
  );
};

export default SubscriptionsPage;
