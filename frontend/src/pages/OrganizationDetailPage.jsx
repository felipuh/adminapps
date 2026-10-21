import { useState, useEffect, useCallback, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  Building2, 
  ArrowLeft,
  BadgeCheck,
  Users,
  Mail,
  Phone,
  Globe,
  MapPin,
  Calendar,
  CreditCard,
  FileText,
  Shield,
  ToggleLeft,
  ToggleRight,
  Edit,
  Trash2,
  PackageCheck,
  PackagePlus,
  PauseCircle,
  PlayCircle,
  RotateCcw,
  Ban,
  ClipboardCheck,
  RefreshCw,
  AlertTriangle,
  Layers,
  History,
  UserPlus,
  Save,
  Download
} from 'lucide-react';
import { entitlementService, organizationService, productSystemService, subscriptionService, userService } from '../services/api';
import toast from 'react-hot-toast';
import { showConfirm } from '../services/dialogs';

// Tab Component
const Tab = ({ active, onClick, children }) => (
  <button
    onClick={onClick}
    className={`
      rounded-lg px-4 py-2 text-sm font-semibold transition-colors
      ${active 
        ? 'bg-blue-50 text-primary-700 shadow-sm ring-1 ring-blue-100' 
        : 'text-slate-600 hover:bg-slate-100 hover:text-slate-950'
      }
    `}
  >
    {children}
  </button>
);

// Info Row Component
const InfoRow = ({ icon: Icon, label, value }) => (
  <div className="flex items-start gap-3 py-3">
    <Icon className="w-5 h-5 text-slate-400 mt-0.5 flex-shrink-0" />
    <div>
      <p className="text-xs font-medium text-slate-500">{label}</p>
      <p className="text-sm font-medium text-slate-900">{value || '-'}</p>
    </div>
  </div>
);

// Module Toggle Component
const ModuleToggle = ({ name, enabled, onChange }) => (
  <div className="flex items-center justify-between py-3 border-b border-slate-200 last:border-0">
    <span className="text-sm font-medium text-slate-700">{name}</span>
    <button
      onClick={() => onChange(!enabled)}
      className={`transition-colors ${enabled ? 'text-emerald-600' : 'text-slate-400'}`}
    >
      {enabled ? <ToggleRight className="w-8 h-8" /> : <ToggleLeft className="w-8 h-8" />}
    </button>
  </div>
);

const accessBadgeClasses = {
  active: 'badge-success',
  trial: 'badge-info',
  suspended: 'badge-warning',
  disabled: 'badge-neutral',
  expired: 'badge-danger',
  cancelled: 'badge-danger',
  not_configured: 'badge-neutral',
};

const AccessBadge = ({ status, children }) => (
  <span className={accessBadgeClasses[status] || 'badge-neutral'}>
    {children || status || 'sin configurar'}
  </span>
);

const formatDate = (value) => {
  if (!value) return '-';
  return new Date(value).toLocaleDateString('es-MX', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  });
};

const ProductAccessCard = ({
  product,
  entitlement,
  plans,
  validation,
  loading,
  onActivate,
  onTrial,
  onSuspend,
  onRevoke,
  onPlanChange,
  onValidate,
}) => {
  const configured = Boolean(entitlement);
  const statusValue = configured
    ? (entitlement.enabled ? entitlement.status : 'disabled')
    : 'not_configured';
  const accessAllowed = Boolean(entitlement?.access_allowed);
  const denialReason = entitlement?.access_denial_reason || validation?.reason;
  const selectedPlan = entitlement?.plan || entitlement?.effective_plan || product.default_plan || '';
  const billingStatus = entitlement?.billing_status || validation?.product?.billing_status || 'not_configured';
  const planLabel = entitlement?.effective_plan_name
    || entitlement?.effective_plan_code
    || entitlement?.plan_name
    || entitlement?.plan_code
    || (configured ? 'Sin plan efectivo' : '-');

  return (
    <div className="relative overflow-hidden rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl border border-blue-100 bg-blue-50 text-blue-700">
              <PackageCheck className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-slate-950">{product.name}</h3>
              <p className="text-xs font-semibold uppercase tracking-[0.08em] text-slate-500">{product.code}</p>
            </div>
            <AccessBadge status={statusValue}>
              {statusValue === 'not_configured' ? 'Sin configurar' : statusValue}
            </AccessBadge>
            {accessAllowed ? (
              <span className="badge-success">Acceso permitido</span>
            ) : (
              <span className="badge-danger">Acceso bloqueado</span>
            )}
          </div>
          <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">
            {product.description || 'Producto SaaS administrado desde AdminApps como control plane central.'}
          </p>
        </div>

        <button
          type="button"
          onClick={() => onValidate(product)}
          disabled={loading}
          className="btn-secondary inline-flex items-center justify-center gap-2 px-4 py-2 text-sm disabled:opacity-60"
        >
          <ClipboardCheck className="h-4 w-4" />
          Validar acceso
        </button>
      </div>

      <div className="mt-5 grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-4">
        <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
          <p className="text-xs font-medium text-slate-500">Plan</p>
          <p className="mt-1 text-sm font-semibold text-slate-900">{planLabel}</p>
        </div>
        <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
          <p className="text-xs font-medium text-slate-500">Billing</p>
          <p className="mt-1 text-sm font-semibold text-slate-900">{product.billing_enabled ? billingStatus : 'No requerido'}</p>
        </div>
        <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
          <p className="text-xs font-medium text-slate-500">Trial hasta / vigencia</p>
          <p className="mt-1 text-sm font-semibold text-slate-900">{formatDate(entitlement?.ends_at)}</p>
        </div>
        <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
          <p className="text-xs font-medium text-slate-500">Actualizado</p>
          <p className="mt-1 text-sm font-semibold text-slate-900">{formatDate(entitlement?.updated_at)}</p>
        </div>
      </div>

      {Array.isArray(entitlement?.scopes) && entitlement.scopes.length > 0 && (
        <div className="mt-4 flex flex-wrap gap-2">
          {entitlement.scopes.map((scope) => (
            <span key={scope} className="badge-neutral">{scope}</span>
          ))}
        </div>
      )}

      {(denialReason && denialReason !== 'ok') && (
        <div className="mt-4 flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800">
          <AlertTriangle className="mt-0.5 h-4 w-4 flex-shrink-0" />
          <span>Razón de bloqueo: {denialReason}</span>
        </div>
      )}

      {validation && (
        <div className="mt-4 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-600">
          Última validación: {validation.allowed ? 'permitida' : 'bloqueada'} · {validation.reason || 'sin razón'}
        </div>
      )}

      <div className="mt-5 flex flex-col gap-3 border-t border-slate-200 pt-4 xl:flex-row xl:items-center xl:justify-between">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
          <select
            value={selectedPlan || ''}
            onChange={(event) => configured && onPlanChange(entitlement, event.target.value)}
            disabled={!configured || loading}
            className="input-glass max-w-xs py-2 text-sm disabled:cursor-not-allowed disabled:opacity-60"
          >
            <option value="">Sin plan específico</option>
            {plans.map((plan) => (
              <option key={plan.id} value={plan.id}>
                {plan.name} · {plan.billing_cycle}
              </option>
            ))}
          </select>
          <span className="text-xs text-slate-500">El plan específico puede complementar la suscripción del cliente.</span>
        </div>

        <div className="flex flex-wrap gap-2">
          {!configured && (
            <>
              <button type="button" onClick={() => onActivate(product)} disabled={loading} className="btn-primary inline-flex items-center gap-2 px-4 py-2 text-sm">
                <PackagePlus className="h-4 w-4" />
                Activar
              </button>
              <button type="button" onClick={() => onTrial(product)} disabled={loading} className="btn-secondary inline-flex items-center gap-2 px-4 py-2 text-sm">
                <PlayCircle className="h-4 w-4" />
                Trial
              </button>
            </>
          )}
          {configured && (
            <>
              <button type="button" onClick={() => onActivate(product, entitlement)} disabled={loading} className="btn-secondary inline-flex items-center gap-2 px-4 py-2 text-sm">
                <RotateCcw className="h-4 w-4" />
                Activar
              </button>
              <button type="button" onClick={() => onTrial(product, entitlement)} disabled={loading} className="btn-secondary inline-flex items-center gap-2 px-4 py-2 text-sm">
                <PlayCircle className="h-4 w-4" />
                Trial
              </button>
              <button type="button" onClick={() => onSuspend(entitlement)} disabled={loading} className="btn-secondary inline-flex items-center gap-2 px-4 py-2 text-sm text-amber-200">
                <PauseCircle className="h-4 w-4" />
                Suspender
              </button>
              <button type="button" onClick={() => onRevoke(entitlement)} disabled={loading} className="btn-danger inline-flex items-center gap-2 px-4 py-2 text-sm">
                <Ban className="h-4 w-4" />
                Revocar
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

const OrganizationUserModal = ({ organization, onClose, onCreated }) => {
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({
    email: '',
    first_name: '',
    last_name: '',
    password: '',
    password_confirm: '',
    role: 'user',
    job_title: '',
    department: '',
  });

  const updateForm = (field, value) => {
    setForm((current) => ({ ...current, [field]: value }));
  };

  const submit = async (event) => {
    event.preventDefault();
    setSaving(true);
    try {
      await userService.create({
        ...form,
        organization: organization.id,
      });
      toast.success('Usuario creado');
      onCreated();
    } catch (error) {
      const data = error.response?.data || {};
      const message = data.detail || data.email?.[0] || data.password?.[0] || data.role || data.organization || 'No se pudo crear el usuario';
      toast.error(message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm">
      <form onSubmit={submit} className="glass-card w-full max-w-2xl p-6">
        <div className="mb-5 flex items-start justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-[0.2em] text-primary-300">Alta controlada</p>
            <h2 className="mt-1 text-xl font-semibold text-gray-100">Crear usuario en {organization.name}</h2>
            <p className="mt-2 text-sm text-gray-500">El backend fuerza scoping por organización y bloquea escalamiento de roles.</p>
          </div>
          <button type="button" onClick={onClose} className="rounded-lg p-2 text-gray-500 hover:bg-dark-300 hover:text-gray-200">
            <Ban className="h-5 w-5" />
          </button>
        </div>

        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <div>
            <label className="mb-1.5 block text-sm text-gray-400">Email</label>
            <input className="input-glass w-full" type="email" value={form.email} onChange={(e) => updateForm('email', e.target.value)} required />
          </div>
          <div>
            <label className="mb-1.5 block text-sm text-gray-400">Rol</label>
            <select className="input-glass w-full" value={form.role} onChange={(e) => updateForm('role', e.target.value)}>
              <option value="user">Usuario</option>
              <option value="org_admin">Administrador de organización</option>
            </select>
          </div>
          <div>
            <label className="mb-1.5 block text-sm text-gray-400">Nombre</label>
            <input className="input-glass w-full" value={form.first_name} onChange={(e) => updateForm('first_name', e.target.value)} required />
          </div>
          <div>
            <label className="mb-1.5 block text-sm text-gray-400">Apellido</label>
            <input className="input-glass w-full" value={form.last_name} onChange={(e) => updateForm('last_name', e.target.value)} required />
          </div>
          <div>
            <label className="mb-1.5 block text-sm text-gray-400">Contraseña temporal</label>
            <input className="input-glass w-full" type="password" value={form.password} onChange={(e) => updateForm('password', e.target.value)} required />
          </div>
          <div>
            <label className="mb-1.5 block text-sm text-gray-400">Confirmar contraseña</label>
            <input className="input-glass w-full" type="password" value={form.password_confirm} onChange={(e) => updateForm('password_confirm', e.target.value)} required />
          </div>
          <div>
            <label className="mb-1.5 block text-sm text-gray-400">Puesto</label>
            <input className="input-glass w-full" value={form.job_title} onChange={(e) => updateForm('job_title', e.target.value)} />
          </div>
          <div>
            <label className="mb-1.5 block text-sm text-gray-400">Departamento</label>
            <input className="input-glass w-full" value={form.department} onChange={(e) => updateForm('department', e.target.value)} />
          </div>
        </div>

        <div className="mt-6 flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
          <button type="button" onClick={onClose} className="btn-secondary px-4 py-2">Cancelar</button>
          <button type="submit" disabled={saving} className="btn-primary inline-flex items-center justify-center gap-2 px-4 py-2 disabled:opacity-60">
            <Save className="h-4 w-4" />
            {saving ? 'Creando...' : 'Crear usuario'}
          </button>
        </div>
      </form>
    </div>
  );
};

const OrganizationDetailPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [organization, setOrganization] = useState(null);
  const [settings, setSettings] = useState(null);
  const [products, setProducts] = useState([]);
  const [entitlements, setEntitlements] = useState([]);
  const [plans, setPlans] = useState([]);
  const [productAccessLoading, setProductAccessLoading] = useState(false);
  const [productAccessError, setProductAccessError] = useState('');
  const [actionLoading, setActionLoading] = useState(false);
  const [validations, setValidations] = useState({});
  const [auditLogs, setAuditLogs] = useState([]);
  const [auditLoading, setAuditLoading] = useState(false);
  const [auditActionFilter, setAuditActionFilter] = useState('');
  const [auditProductFilter, setAuditProductFilter] = useState('');
  const [organizationUsers, setOrganizationUsers] = useState([]);
  const [usersLoading, setUsersLoading] = useState(false);
  const [showUserModal, setShowUserModal] = useState(false);
  const [userActionLoading, setUserActionLoading] = useState(null);
  const [subscriptionDetail, setSubscriptionDetail] = useState(null);
  const [subscriptionInvoices, setSubscriptionInvoices] = useState([]);
  const [subscriptionLoading, setSubscriptionLoading] = useState(false);
  const [subscriptionActionLoading, setSubscriptionActionLoading] = useState(false);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('products');

  // Validate ID - 'new' is not a valid organization ID
  useEffect(() => {
    if (id === 'new') {
      navigate('/organizations', { replace: true });
      return;
    }

    const fetchProductAccess = async () => {
      setProductAccessLoading(true);
      setProductAccessError('');
      try {
        const [productsData, entitlementsData, plansData] = await Promise.all([
          productSystemService.active(),
          entitlementService.byOrganization(id),
          subscriptionService.getPlans().catch(() => []),
        ]);
        setProducts(productsData.results || productsData || []);
        setEntitlements(entitlementsData.products || []);
        setPlans(plansData.results || plansData || []);
      } catch (error) {
        setProductAccessError(error.response?.data?.detail || 'No se pudieron cargar productos y accesos.');
      } finally {
        setProductAccessLoading(false);
      }
    };

    const fetchOrganizationUsers = async () => {
      setUsersLoading(true);
      try {
        const usersData = await organizationService.getUsers(id);
        setOrganizationUsers(usersData.results || usersData || []);
      } catch (error) {
        toast.error(error.response?.data?.detail || 'No se pudieron cargar usuarios');
      } finally {
        setUsersLoading(false);
      }
    };

    const fetchSubscriptionDetail = async (subscriptionId) => {
      if (!subscriptionId) {
        setSubscriptionDetail(null);
        setSubscriptionInvoices([]);
        return;
      }
      setSubscriptionLoading(true);
      try {
        const [subscriptionData, invoicesData] = await Promise.all([
          subscriptionService.getById(subscriptionId),
          subscriptionService.getInvoices(subscriptionId).catch(() => []),
        ]);
        setSubscriptionDetail(subscriptionData);
        setSubscriptionInvoices(invoicesData.results || invoicesData || []);
      } catch (error) {
        toast.error(error.response?.data?.detail || 'No se pudo cargar la suscripción');
      } finally {
        setSubscriptionLoading(false);
      }
    };

    const fetchData = async () => {
      try {
        const [orgData, settingsData] = await Promise.all([
          organizationService.getById(id),
          organizationService.getSettings(id).catch(() => null),
        ]);
        setOrganization(orgData);
        setSettings(settingsData);
        await Promise.all([
          fetchProductAccess(),
          fetchOrganizationUsers(),
          fetchSubscriptionDetail(orgData.subscription),
        ]);
      } catch (error) {
        toast.error(error.response?.data?.detail || 'No se pudo cargar la organización');
        setOrganization(null);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [id, navigate]);

  const refreshOrganizationUsers = async () => {
    setUsersLoading(true);
    try {
      const usersData = await organizationService.getUsers(id);
      setOrganizationUsers(usersData.results || usersData || []);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'No se pudieron refrescar usuarios');
    } finally {
      setUsersLoading(false);
    }
  };

  const handleUserCreated = async () => {
    setShowUserModal(false);
    await refreshOrganizationUsers();
  };

  const handleToggleUserStatus = async (user) => {
    const nextActive = !user.is_active;
    const confirmed = await showConfirm({
      title: nextActive ? 'Activar usuario' : 'Desactivar usuario',
      text: `${nextActive ? 'Se reactivará' : 'Se bloqueará'} el acceso de ${user.email}.`,
      confirmButtonText: nextActive ? 'Activar' : 'Desactivar',
      cancelButtonText: 'Cancelar',
      icon: nextActive ? 'question' : 'warning',
    });
    if (!confirmed) return;
    setUserActionLoading(user.id);
    try {
      await userService.update(user.id, { is_active: nextActive });
      toast.success(nextActive ? 'Usuario activado' : 'Usuario desactivado');
      await refreshOrganizationUsers();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'No se pudo actualizar el usuario');
    } finally {
      setUserActionLoading(null);
    }
  };

  const refreshSubscriptionDetail = async () => {
    if (!organization?.subscription) return;
    setSubscriptionLoading(true);
    try {
      const [subscriptionData, invoicesData] = await Promise.all([
        subscriptionService.getById(organization.subscription),
        subscriptionService.getInvoices(organization.subscription).catch(() => []),
      ]);
      setSubscriptionDetail(subscriptionData);
      setSubscriptionInvoices(invoicesData.results || invoicesData || []);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'No se pudo refrescar la suscripción');
    } finally {
      setSubscriptionLoading(false);
    }
  };

  const handleSubscriptionActivate = async () => {
    if (!subscriptionDetail) return;
    const confirmed = await showConfirm({
      title: 'Activar suscripción',
      text: `Se activará la suscripción de ${organization.name}.`,
      confirmButtonText: 'Activar',
      cancelButtonText: 'Cancelar',
    });
    if (!confirmed) return;
    setSubscriptionActionLoading(true);
    try {
      await subscriptionService.activate(subscriptionDetail.id);
      toast.success('Suscripción activada');
      await refreshSubscriptionDetail();
      await refreshProductAccess();
    } catch (error) {
      toast.error(error.response?.data?.error || error.response?.data?.detail || 'No se pudo activar la suscripción');
    } finally {
      setSubscriptionActionLoading(false);
    }
  };

  const handleSubscriptionCancel = async () => {
    if (!subscriptionDetail) return;
    const confirmed = await showConfirm({
      title: 'Cancelar suscripción',
      text: `Se cancelará la suscripción de ${organization.name}. Los productos con billing pueden quedar bloqueados.`,
      confirmButtonText: 'Cancelar suscripción',
      cancelButtonText: 'Mantener activa',
      icon: 'warning',
    });
    if (!confirmed) return;
    setSubscriptionActionLoading(true);
    try {
      await subscriptionService.cancel(subscriptionDetail.id);
      toast.success('Suscripción cancelada');
      await refreshSubscriptionDetail();
      await refreshProductAccess();
    } catch (error) {
      toast.error(error.response?.data?.error || error.response?.data?.detail || 'No se pudo cancelar la suscripción');
    } finally {
      setSubscriptionActionLoading(false);
    }
  };

  const handleSubscriptionPlanChange = async (planId) => {
    if (!subscriptionDetail || !planId || planId === subscriptionDetail.plan?.id) return;
    const confirmed = await showConfirm({
      title: 'Cambiar plan de suscripción',
      text: `Se actualizará el plan comercial de ${organization.name}.`,
      confirmButtonText: 'Cambiar plan',
      cancelButtonText: 'Cancelar',
    });
    if (!confirmed) return;
    setSubscriptionActionLoading(true);
    try {
      await subscriptionService.changePlan(subscriptionDetail.id, planId);
      toast.success('Plan de suscripción actualizado');
      await refreshSubscriptionDetail();
      await refreshProductAccess();
    } catch (error) {
      toast.error(error.response?.data?.error || error.response?.data?.detail || 'No se pudo cambiar el plan');
    } finally {
      setSubscriptionActionLoading(false);
    }
  };

  const refreshProductAccess = async () => {
    try {
      const entitlementsData = await entitlementService.byOrganization(id);
      setEntitlements(entitlementsData.products || []);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'No se pudo refrescar productos y accesos');
    }
  };

  const getEntitlementForProduct = (product) => (
    entitlements.find((item) => item.product === product.id || item.product_code === product.code)
  );

  const createEntitlement = async (product, status = 'active') => {
    const payload = {
      organization: id,
      product: product.id,
      enabled: true,
      status,
    };
    if (organization?.subscription) {
      payload.subscription = organization.subscription;
    }
    if (product.default_plan) {
      payload.plan = product.default_plan;
    }
    return entitlementService.create(payload);
  };

  const handleActivateProduct = async (product, entitlement = null) => {
    if (product.billing_enabled && !organization?.subscription && !entitlement?.subscription) {
      toast.error('Este producto requiere una suscripción efectiva para activarse. Usa Trial o vincula una suscripción.');
      return;
    }
    const confirmed = await showConfirm({
      title: 'Activar producto',
      text: `Se habilitará ${product.name} para ${organization.name}.`,
      confirmButtonText: 'Activar',
      cancelButtonText: 'Cancelar',
    });
    if (!confirmed) return;
    setActionLoading(true);
    try {
      if (entitlement) {
        await entitlementService.toggle(entitlement.id, 'enable');
      } else {
        await createEntitlement(product, 'active');
      }
      toast.success(`${product.name} activado`);
      await refreshProductAccess();
    } catch (error) {
      toast.error(error.response?.data?.detail || error.response?.data?.non_field_errors?.[0] || 'No se pudo activar el producto');
    } finally {
      setActionLoading(false);
    }
  };

  const handleTrialProduct = async (product, entitlement = null) => {
    const confirmed = await showConfirm({
      title: 'Iniciar trial',
      text: `Se habilitará ${product.name} en trial para ${organization.name}.`,
      confirmButtonText: 'Iniciar trial',
      cancelButtonText: 'Cancelar',
    });
    if (!confirmed) return;
    setActionLoading(true);
    try {
      if (entitlement) {
        await entitlementService.toggle(entitlement.id, { action: 'trial', trial_days: 14 });
      } else {
        const endsAt = new Date();
        endsAt.setDate(endsAt.getDate() + 14);
        await entitlementService.create({
          organization: id,
          product: product.id,
          enabled: true,
          status: 'trial',
          ends_at: endsAt.toISOString(),
          ...(organization?.subscription ? { subscription: organization.subscription } : {}),
          ...(product.default_plan ? { plan: product.default_plan } : {}),
        });
      }
      toast.success(`${product.name} en trial`);
      await refreshProductAccess();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'No se pudo iniciar el trial');
    } finally {
      setActionLoading(false);
    }
  };

  const handleSuspendEntitlement = async (entitlement) => {
    const confirmed = await showConfirm({
      title: 'Suspender producto',
      text: `El acceso a ${entitlement.product_name} quedará bloqueado hasta reactivación.`,
      confirmButtonText: 'Suspender',
      cancelButtonText: 'Cancelar',
    });
    if (!confirmed) return;
    setActionLoading(true);
    try {
      await entitlementService.toggle(entitlement.id, { action: 'disable', reason: 'Suspensión desde AdminApps' });
      toast.success(`${entitlement.product_name} suspendido`);
      await refreshProductAccess();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'No se pudo suspender el producto');
    } finally {
      setActionLoading(false);
    }
  };

  const handleRevokeEntitlement = async (entitlement) => {
    const confirmed = await showConfirm({
      title: 'Revocar producto',
      text: `Se revocará ${entitlement.product_name}. Esta acción bloquea el acceso comercial del cliente.`,
      confirmButtonText: 'Revocar',
      cancelButtonText: 'Cancelar',
      icon: 'warning',
    });
    if (!confirmed) return;
    setActionLoading(true);
    try {
      await entitlementService.update(entitlement.id, {
        enabled: false,
        status: 'cancelled',
      });
      toast.success(`${entitlement.product_name} revocado`);
      await refreshProductAccess();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'No se pudo revocar el producto');
    } finally {
      setActionLoading(false);
    }
  };

  const handlePlanChange = async (entitlement, planId) => {
    const confirmed = await showConfirm({
      title: 'Cambiar plan',
      text: `Se actualizará el plan asociado a ${entitlement.product_name}.`,
      confirmButtonText: 'Actualizar plan',
      cancelButtonText: 'Cancelar',
    });
    if (!confirmed) return;
    setActionLoading(true);
    try {
      await entitlementService.update(entitlement.id, { plan: planId || null });
      toast.success('Plan actualizado');
      await refreshProductAccess();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'No se pudo cambiar el plan');
    } finally {
      setActionLoading(false);
    }
  };

  const handleValidateProduct = async (product) => {
    setActionLoading(true);
    try {
      const data = await entitlementService.validate(id, product.code);
      setValidations((current) => ({ ...current, [product.code]: data }));
      toast.success(data.allowed ? 'Acceso permitido' : 'Acceso bloqueado');
    } catch (error) {
      const payload = error.response?.data || { allowed: false, reason: 'validation_error' };
      setValidations((current) => ({ ...current, [product.code]: payload }));
      toast.error(payload.reason || 'Acceso bloqueado');
    } finally {
      setActionLoading(false);
    }
  };

  const fetchEntitlementAuditLogs = useCallback(async () => {
    if (entitlements.length === 0) {
      setAuditLogs([]);
      return;
    }
    setAuditLoading(true);
    try {
      const logsByEntitlement = await Promise.all(
        entitlements.map((entitlement) => entitlementService.auditLogs(entitlement.id).catch(() => []))
      );
      const mergedLogs = logsByEntitlement
        .flat()
        .sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
      setAuditLogs(mergedLogs);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'No se pudo cargar auditoría de productos');
    } finally {
      setAuditLoading(false);
    }
  }, [entitlements]);

  useEffect(() => {
    if (activeTab === 'audit') {
      fetchEntitlementAuditLogs();
    }
  }, [activeTab, fetchEntitlementAuditLogs]);

  const auditActionOptions = useMemo(() => (
    [...new Set(auditLogs.map((log) => log.action).filter(Boolean))].sort()
  ), [auditLogs]);

  const auditProductOptions = useMemo(() => (
    [...new Set(auditLogs.map((log) => log.product_code).filter(Boolean))].sort()
  ), [auditLogs]);

  const filteredAuditLogs = useMemo(() => (
    auditLogs.filter((log) => (
      (!auditActionFilter || log.action === auditActionFilter)
      && (!auditProductFilter || log.product_code === auditProductFilter)
    ))
  ), [auditLogs, auditActionFilter, auditProductFilter]);

  const exportAuditCsv = () => {
    const rows = [
      ['created_at', 'action', 'product_code', 'product_name', 'actor', 'previous_status', 'previous_enabled', 'new_status', 'new_enabled'],
      ...filteredAuditLogs.map((log) => [
        log.created_at || '',
        log.action || '',
        log.product_code || '',
        log.product_name || '',
        log.actor_name || 'Sistema',
        log.previous_state?.status || '',
        log.previous_state?.enabled ?? '',
        log.new_state?.status || '',
        log.new_state?.enabled ?? '',
      ]),
    ];
    const csv = rows.map((row) => (
      row.map((value) => `"${String(value).replaceAll('"', '""')}"`).join(',')
    )).join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${organization.code || 'organization'}-product-audit.csv`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const handleModuleToggle = async (module, value) => {
    try {
      await organizationService.updateSettings(id, { [module]: value });
      setSettings({ ...settings, [module]: value });
      toast.success('Configuración actualizada');
    } catch {
      toast.error('Error al actualizar configuración');
    }
  };

  const statusColors = {
    active: 'badge-success',
    trial: 'badge-info',
    suspended: 'badge-danger',
    inactive: 'badge-neutral',
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-12 w-64 skeleton rounded-lg" />
        <div className="glass-card p-8 h-96 skeleton" />
      </div>
    );
  }

  if (!organization) {
    return (
      <div className="glass-card p-8 text-center">
        <Building2 className="w-12 h-12 text-gray-600 mx-auto mb-4" />
        <p className="text-gray-400">Organización no encontrada</p>
        <button onClick={() => navigate('/organizations')} className="btn-primary mt-4">
          Volver a Organizaciones
        </button>
      </div>
    );
  }

  return (
    <div className="enterprise-page">
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/organizations')}
            className="rounded-lg border border-slate-200 bg-white p-2 text-slate-500 shadow-sm hover:bg-slate-50 hover:text-slate-900"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div className="flex items-center gap-4">
            <div className="flex h-14 w-14 items-center justify-center rounded-xl border border-blue-100 bg-blue-50 text-blue-700">
              <Building2 className="w-7 h-7" />
            </div>
            <div>
              <div className="flex flex-wrap items-center gap-3">
                <h1 className="text-2xl font-semibold text-slate-950">{organization.name}</h1>
                <span className={statusColors[organization.status]}>{organization.status}</span>
                {organization.billing_exempt && (
                  <span className="badge-success">
                    <BadgeCheck className="h-3.5 w-3.5" />
                    Exenta de cobro
                  </span>
                )}
              </div>
              <p className="mt-1 text-sm text-slate-500">{organization.code}</p>
            </div>
          </div>
        </div>
        <div className="flex gap-3">
          <button className="btn-secondary flex items-center gap-2">
            <Edit className="w-4 h-4" />
            Editar
          </button>
          <button className="btn-danger flex items-center gap-2">
            <Trash2 className="w-4 h-4" />
            Eliminar
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 overflow-x-auto rounded-xl border border-slate-200 bg-white p-2 shadow-sm">
        <Tab active={activeTab === 'overview'} onClick={() => setActiveTab('overview')}>
          Resumen
        </Tab>
        <Tab active={activeTab === 'products'} onClick={() => setActiveTab('products')}>
          Productos y accesos
        </Tab>
        <Tab active={activeTab === 'users'} onClick={() => setActiveTab('users')}>
          Usuarios
        </Tab>
        <Tab active={activeTab === 'subscription'} onClick={() => setActiveTab('subscription')}>
          Suscripción
        </Tab>
        <Tab active={activeTab === 'billing'} onClick={() => setActiveTab('billing')}>
          Billing
        </Tab>
        <Tab active={activeTab === 'settings'} onClick={() => setActiveTab('settings')}>
          Configuración
        </Tab>
        <Tab active={activeTab === 'audit'} onClick={() => setActiveTab('audit')}>
          Auditoría
        </Tab>
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Contact Info */}
          <div className="glass-card p-6">
            <h2 className="text-lg font-semibold text-gray-100 mb-4">Información de Contacto</h2>
            <div className="divide-y divide-gray-700/30">
              <InfoRow icon={Mail} label="Email" value={organization.email} />
              <InfoRow icon={Phone} label="Teléfono" value={organization.phone} />
              <InfoRow icon={Globe} label="Sitio Web" value={organization.website} />
              <InfoRow icon={MapPin} label="Dirección" value={`${organization.address}, ${organization.city}, ${organization.country}`} />
            </div>
          </div>

          {/* Business Info */}
          <div className="glass-card p-6">
            <h2 className="text-lg font-semibold text-gray-100 mb-4">Información del Negocio</h2>
            <div className="divide-y divide-gray-700/30">
              <InfoRow icon={FileText} label="Razón Social" value={organization.legal_name} />
              <InfoRow icon={Building2} label="Industria" value={organization.industry} />
              <InfoRow icon={Shield} label="Facturación" value={organization.billing_exempt ? 'Exenta por organización dueña' : 'Facturación estándar'} />
              <InfoRow icon={Users} label="Empleados" value={organization.employees_count?.toString()} />
              <InfoRow icon={Calendar} label="Fecha de Registro" value={organization.created_at ? new Date(organization.created_at).toLocaleDateString('es-MX') : '-'} />
            </div>
          </div>

          {/* Limits & Usage */}
          <div className="glass-card p-6">
            <h2 className="text-lg font-semibold text-gray-100 mb-4">Límites y Uso</h2>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-400">Usuarios</span>
                  <span className="text-gray-200">{organization.users_count} / {organization.max_users}</span>
                </div>
                <div className="w-full bg-dark-400 rounded-full h-2">
                  <div
                    className="bg-primary-500 h-2 rounded-full transition-all"
                    style={{ width: `${(organization.users_count / organization.max_users) * 100}%` }}
                  />
                </div>
              </div>
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-400">Documentos</span>
                  <span className="text-gray-200">Límite: {organization.max_documents}</span>
                </div>
                <p className="text-xs text-gray-500">Uso real no expuesto por este endpoint.</p>
              </div>
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-400">Almacenamiento</span>
                  <span className="text-gray-200">Límite: {organization.max_storage_mb} MB</span>
                </div>
                <p className="text-xs text-gray-500">Uso real no expuesto por este endpoint.</p>
              </div>
            </div>
            
            {/* ISO Standards */}
            <div className="mt-6 pt-4 border-t border-gray-700/30">
              <p className="text-sm text-gray-400 mb-2">Estándares ISO</p>
              <div className="flex flex-wrap gap-2">
                {organization.iso_standards?.map((standard) => (
                  <span key={standard} className="badge-info">{standard}</span>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'products' && (
        <div className="space-y-5">
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
              <div>
                <p className="enterprise-kicker">Control plane comercial</p>
                <h2 className="mt-1 text-xl font-semibold text-slate-950">Productos SaaS y accesos contratados</h2>
                <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">
                  Esta sección administra productos reales vendibles. Los módulos ISO legacy y feature flags viven en configuración y no otorgan acceso comercial por sí solos.
                </p>
              </div>
              <button
                type="button"
                onClick={refreshProductAccess}
                disabled={productAccessLoading}
                className="btn-secondary inline-flex items-center justify-center gap-2 px-4 py-2 text-sm disabled:opacity-60"
              >
                <RefreshCw className={`h-4 w-4 ${productAccessLoading ? 'animate-spin' : ''}`} />
                Refrescar
              </button>
            </div>

            <div className="mt-5 grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
              <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
                <p className="text-xs font-medium text-slate-500">Productos disponibles</p>
                <p className="mt-1 text-2xl font-semibold text-slate-950">{products.length}</p>
              </div>
              <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
                <p className="text-xs font-medium text-slate-500">Configurados</p>
                <p className="mt-1 text-2xl font-semibold text-slate-950">{entitlements.length}</p>
              </div>
              <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-4">
                <p className="text-xs font-medium text-emerald-700">Acceso permitido</p>
                <p className="mt-1 text-2xl font-semibold text-emerald-950">{entitlements.filter((item) => item.access_allowed).length}</p>
              </div>
              <div className="rounded-lg border border-red-200 bg-red-50 p-4">
                <p className="text-xs font-medium text-red-700">Bloqueados</p>
                <p className="mt-1 text-2xl font-semibold text-red-950">{entitlements.filter((item) => !item.access_allowed).length}</p>
              </div>
            </div>
          </div>

          {productAccessError && (
            <div className="flex items-start gap-3 rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-red-200">
              <AlertTriangle className="mt-0.5 h-5 w-5 flex-shrink-0" />
              <div>
                <p className="font-medium">No se pudo cargar la administración de productos</p>
                <p className="mt-1 text-sm text-red-200/80">{productAccessError}</p>
              </div>
            </div>
          )}

          {productAccessLoading ? (
            <div className="grid grid-cols-1 gap-4">
              {[0, 1].map((item) => (
                <div key={item} className="h-56 rounded-xl border border-gray-700/50 bg-dark-300/60 skeleton" />
              ))}
            </div>
          ) : products.length === 0 ? (
            <div className="rounded-xl border border-gray-700/60 bg-dark-300/70 p-10 text-center">
              <Layers className="mx-auto h-12 w-12 text-gray-600" />
              <h3 className="mt-4 text-lg font-semibold text-gray-100">No hay productos SaaS activos</h3>
              <p className="mt-2 text-sm text-gray-500">Registra o activa productos en el catálogo para asignarlos a clientes.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {products.map((product) => (
                <ProductAccessCard
                  key={product.id}
                  product={product}
                  entitlement={getEntitlementForProduct(product)}
                  plans={plans}
                  validation={validations[product.code]}
                  loading={actionLoading}
                  onActivate={handleActivateProduct}
                  onTrial={handleTrialProduct}
                  onSuspend={handleSuspendEntitlement}
                  onRevoke={handleRevokeEntitlement}
                  onPlanChange={handlePlanChange}
                  onValidate={handleValidateProduct}
                />
              ))}
            </div>
          )}
        </div>
      )}

      {activeTab === 'users' && (
        <div className="glass-card p-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-lg font-semibold text-gray-100">Usuarios de la organización</h2>
              <p className="mt-1 text-sm text-gray-500">Identidades vinculadas a este cliente/tenant.</p>
            </div>
            <button onClick={() => setShowUserModal(true)} className="btn-primary flex items-center gap-2">
              <UserPlus className="w-4 h-4" />
              Agregar Usuario
            </button>
          </div>

          {usersLoading ? (
            <div className="space-y-3">
              {[0, 1, 2].map((item) => (
                <div key={item} className="h-16 rounded-lg border border-gray-700/50 bg-dark-400/40 skeleton" />
              ))}
            </div>
          ) : organizationUsers.length === 0 ? (
            <div className="rounded-xl border border-gray-700/60 bg-dark-400/30 p-10 text-center">
              <Users className="w-12 h-12 mx-auto mb-4 text-gray-600" />
              <h3 className="text-lg font-semibold text-gray-100">Sin usuarios registrados</h3>
              <p className="mt-2 text-sm text-gray-500">Crea el primer usuario de esta organización para habilitar operación del cliente.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="table-glass">
                <thead>
                  <tr>
                    <th>Usuario</th>
                    <th>Rol</th>
                    <th>Estado</th>
                    <th>Último acceso</th>
                    <th>Acciones</th>
                  </tr>
                </thead>
                <tbody>
                  {organizationUsers.map((user) => (
                    <tr key={user.id}>
                      <td>
                        <div className="font-medium text-gray-100">
                          {[user.first_name, user.last_name].filter(Boolean).join(' ') || user.email}
                        </div>
                        <div className="text-xs text-gray-500">{user.email}</div>
                      </td>
                      <td>
                        <span className={user.role === 'org_admin' ? 'badge-info' : 'badge-neutral'}>
                          {user.role}
                        </span>
                      </td>
                      <td>
                        <span className={user.is_active ? 'badge-success' : 'badge-danger'}>
                          {user.is_active ? 'Activo' : 'Inactivo'}
                        </span>
                      </td>
                      <td className="text-sm text-gray-400">{formatDate(user.last_login_at)}</td>
                      <td>
                        <button
                          type="button"
                          onClick={() => handleToggleUserStatus(user)}
                          disabled={userActionLoading === user.id}
                          className={`inline-flex items-center gap-2 rounded-lg px-3 py-2 text-sm transition-colors disabled:opacity-60 ${
                            user.is_active
                              ? 'border border-amber-400/25 bg-amber-500/10 text-amber-200 hover:bg-amber-500/20'
                              : 'border border-emerald-400/25 bg-emerald-500/10 text-emerald-200 hover:bg-emerald-500/20'
                          }`}
                        >
                          {user.is_active ? <PauseCircle className="h-4 w-4" /> : <PlayCircle className="h-4 w-4" />}
                          {user.is_active ? 'Desactivar' : 'Activar'}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {activeTab === 'settings' && settings && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="glass-card p-6">
            <div className="mb-4">
              <p className="text-xs uppercase tracking-[0.2em] text-gray-500">Configuración interna legacy</p>
              <h2 className="mt-1 text-lg font-semibold text-gray-100">Módulos ISO Smart</h2>
              <p className="mt-2 text-sm text-gray-500">
                Estos toggles configuran módulos operativos legacy. No reemplazan los productos SaaS contratados en Productos y accesos.
              </p>
            </div>
            <div className="divide-y divide-gray-700/30">
              <ModuleToggle
                name="SCA - Análisis de Contexto"
                enabled={settings.module_sca_enabled}
                onChange={(v) => handleModuleToggle('module_sca_enabled', v)}
              />
              <ModuleToggle
                name="SIE - Inteligencia de Stakeholders"
                enabled={settings.module_sie_enabled}
                onChange={(v) => handleModuleToggle('module_sie_enabled', v)}
              />
              <ModuleToggle
                name="ASB - Construcción de Alcance"
                enabled={settings.module_asb_enabled}
                onChange={(v) => handleModuleToggle('module_asb_enabled', v)}
              />
              <ModuleToggle
                name="SPM - Mapeo de Procesos"
                enabled={settings.module_spm_enabled}
                onChange={(v) => handleModuleToggle('module_spm_enabled', v)}
              />
              <ModuleToggle
                name="Gestión Documental"
                enabled={settings.module_documents_enabled}
                onChange={(v) => handleModuleToggle('module_documents_enabled', v)}
              />
              <ModuleToggle
                name="Gestión de Riesgos"
                enabled={settings.module_risks_enabled}
                onChange={(v) => handleModuleToggle('module_risks_enabled', v)}
              />
              <ModuleToggle
                name="Objetivos de Calidad"
                enabled={settings.module_objectives_enabled}
                onChange={(v) => handleModuleToggle('module_objectives_enabled', v)}
              />
            </div>
          </div>
          
          <div className="glass-card p-6">
            <h2 className="text-lg font-semibold text-gray-100 mb-4">Configuración de IA</h2>
            <div className="space-y-4">
              <ModuleToggle
                name="Análisis Automático"
                enabled={settings.ai_auto_analysis}
                onChange={(v) => handleModuleToggle('ai_auto_analysis', v)}
              />
              <p className="text-sm text-gray-500">
                Cuando está habilitado, el sistema ejecutará análisis automáticos periódicos 
                para detectar oportunidades de mejora y riesgos potenciales.
              </p>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'audit' && (
        <div className="rounded-xl border border-gray-700/60 bg-dark-300/70 p-6">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <p className="text-xs uppercase tracking-[0.2em] text-gray-500">Evidencia operativa</p>
              <h2 className="mt-1 text-lg font-semibold text-gray-100">Auditoría de productos</h2>
              <p className="mt-2 text-sm text-gray-500">Cambios sensibles sobre entitlements de productos SaaS para esta organización.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                onClick={exportAuditCsv}
                disabled={filteredAuditLogs.length === 0}
                className="btn-secondary inline-flex items-center justify-center gap-2 px-4 py-2 text-sm disabled:opacity-60"
              >
                <Download className="h-4 w-4" />
                Exportar CSV
              </button>
              <button
                type="button"
                onClick={fetchEntitlementAuditLogs}
                disabled={auditLoading}
                className="btn-secondary inline-flex items-center justify-center gap-2 px-4 py-2 text-sm disabled:opacity-60"
              >
                <RefreshCw className={`h-4 w-4 ${auditLoading ? 'animate-spin' : ''}`} />
                Refrescar
              </button>
            </div>
          </div>

          {auditLogs.length > 0 && (
            <div className="mt-5 grid grid-cols-1 gap-3 md:grid-cols-[1fr_1fr_auto] md:items-end">
              <div>
                <label className="mb-1.5 block text-xs uppercase tracking-widest text-gray-500">Acción</label>
                <select
                  className="input-glass py-2 text-sm"
                  value={auditActionFilter}
                  onChange={(event) => setAuditActionFilter(event.target.value)}
                >
                  <option value="">Todas</option>
                  {auditActionOptions.map((action) => (
                    <option key={action} value={action}>{action}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="mb-1.5 block text-xs uppercase tracking-widest text-gray-500">Producto</label>
                <select
                  className="input-glass py-2 text-sm"
                  value={auditProductFilter}
                  onChange={(event) => setAuditProductFilter(event.target.value)}
                >
                  <option value="">Todos</option>
                  {auditProductOptions.map((productCode) => (
                    <option key={productCode} value={productCode}>{productCode}</option>
                  ))}
                </select>
              </div>
              <button
                type="button"
                onClick={() => {
                  setAuditActionFilter('');
                  setAuditProductFilter('');
                }}
                className="btn-secondary px-4 py-2 text-sm"
              >
                Limpiar filtros
              </button>
            </div>
          )}

          {auditLoading ? (
            <div className="mt-6 space-y-3">
              {[0, 1, 2].map((item) => (
                <div key={item} className="h-20 rounded-lg border border-gray-700/50 bg-dark-400/40 skeleton" />
              ))}
            </div>
          ) : auditLogs.length === 0 ? (
            <div className="mt-6 rounded-xl border border-gray-700/50 bg-dark-400/30 p-8 text-center">
              <History className="mx-auto h-10 w-10 text-gray-600" />
              <h3 className="mt-3 text-base font-semibold text-gray-100">Sin eventos de auditoría</h3>
              <p className="mt-1 text-sm text-gray-500">Cuando se activen, suspendan, revoquen o actualicen productos, aparecerán aquí.</p>
            </div>
          ) : filteredAuditLogs.length === 0 ? (
            <div className="mt-6 rounded-xl border border-gray-700/50 bg-dark-400/30 p-8 text-center">
              <History className="mx-auto h-10 w-10 text-gray-600" />
              <h3 className="mt-3 text-base font-semibold text-gray-100">Sin resultados para estos filtros</h3>
              <p className="mt-1 text-sm text-gray-500">Ajusta la acción o producto para ver otros eventos.</p>
            </div>
          ) : (
            <div className="mt-6 space-y-3">
              {filteredAuditLogs.map((log) => (
                <div key={log.id} className="rounded-lg border border-gray-700/50 bg-dark-400/30 p-4">
                  <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                    <div>
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="badge-info">{log.action}</span>
                        <span className="text-sm font-medium text-gray-100">{log.product_name || log.product_code}</span>
                        <span className="text-xs text-gray-500">{log.product_code}</span>
                      </div>
                      <p className="mt-2 text-sm text-gray-400">
                        Actor: {log.actor_name || 'Sistema'} · {new Date(log.created_at).toLocaleString('es-MX')}
                      </p>
                    </div>
                    <div className="grid min-w-0 grid-cols-1 gap-2 text-xs sm:grid-cols-2 md:w-[420px]">
                      <div className="rounded-md border border-gray-700/45 bg-slate-950/20 p-2">
                        <p className="text-gray-500">Antes</p>
                        <p className="mt-1 truncate text-gray-300">{log.previous_state?.status || '-'} · {log.previous_state?.enabled ? 'enabled' : 'disabled'}</p>
                      </div>
                      <div className="rounded-md border border-gray-700/45 bg-slate-950/20 p-2">
                        <p className="text-gray-500">Después</p>
                        <p className="mt-1 truncate text-gray-300">{log.new_state?.status || '-'} · {log.new_state?.enabled ? 'enabled' : 'disabled'}</p>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {activeTab === 'subscription' && (
        <div className="space-y-5">
          <div className="glass-card p-6">
            <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
              <div>
                <p className="text-xs uppercase tracking-[0.2em] text-primary-300">Contrato comercial</p>
                <h2 className="mt-1 text-lg font-semibold text-gray-100">Suscripción / Plan</h2>
                <p className="mt-2 text-sm text-gray-500">Estado financiero que alimenta la validación de productos con billing.</p>
              </div>
              <button
                type="button"
                onClick={refreshSubscriptionDetail}
                disabled={subscriptionLoading || !organization.subscription}
                className="btn-secondary inline-flex items-center gap-2 disabled:opacity-60"
              >
                <RefreshCw className={`h-4 w-4 ${subscriptionLoading ? 'animate-spin' : ''}`} />
                Refrescar
              </button>
            </div>

            {subscriptionLoading ? (
              <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
                {[0, 1, 2].map((item) => (
                  <div key={item} className="h-28 rounded-xl border border-gray-700/50 bg-dark-400/40 skeleton" />
                ))}
              </div>
            ) : !subscriptionDetail ? (
              <div className="rounded-xl border border-amber-400/25 bg-amber-500/10 p-6 text-amber-100">
                <div className="flex items-start gap-3">
                  <AlertTriangle className="mt-0.5 h-5 w-5 flex-shrink-0" />
                  <div>
                    <h3 className="font-semibold">Sin suscripción vinculada</h3>
                    <p className="mt-1 text-sm text-amber-100/80">
                      Esta organización puede usar trials, pero los productos con billing no podrán activarse como activos hasta tener una suscripción efectiva.
                    </p>
                  </div>
                </div>
              </div>
            ) : (
              <>
                <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
                  <div className="rounded-xl border border-gray-700/50 bg-dark-400/30 p-4">
                    <p className="text-xs text-gray-500">Plan</p>
                    <p className="mt-1 text-xl font-semibold text-gray-100">{subscriptionDetail.plan?.name || subscriptionDetail.plan_name || '-'}</p>
                    <p className="mt-1 text-xs text-gray-500">{subscriptionDetail.plan?.code || ''}</p>
                  </div>
                  <div className="rounded-xl border border-gray-700/50 bg-dark-400/30 p-4">
                    <p className="text-xs text-gray-500">Estado</p>
                    <p className="mt-2"><AccessBadge status={subscriptionDetail.status}>{subscriptionDetail.status}</AccessBadge></p>
                  </div>
                  <div className="rounded-xl border border-gray-700/50 bg-dark-400/30 p-4">
                    <p className="text-xs text-gray-500">Monto</p>
                    <p className="mt-1 text-xl font-semibold text-gray-100">
                      {subscriptionDetail.amount} {subscriptionDetail.plan?.currency || ''}
                    </p>
                    <p className="mt-1 text-xs text-gray-500">{subscriptionDetail.plan?.billing_cycle || ''}</p>
                  </div>
                  <div className="rounded-xl border border-gray-700/50 bg-dark-400/30 p-4">
                    <p className="text-xs text-gray-500">Próximo cobro</p>
                    <p className="mt-1 text-xl font-semibold text-gray-100">{formatDate(subscriptionDetail.next_billing_date)}</p>
                  </div>
                </div>

                <div className="mt-5 grid grid-cols-1 gap-4 lg:grid-cols-3">
                  <div className="rounded-xl border border-gray-700/50 bg-dark-400/30 p-4">
                    <p className="text-xs text-gray-500">Periodo actual</p>
                    <p className="mt-2 text-sm text-gray-200">
                      {formatDate(subscriptionDetail.current_period_start)} - {formatDate(subscriptionDetail.current_period_end)}
                    </p>
                  </div>
                  <div className="rounded-xl border border-gray-700/50 bg-dark-400/30 p-4">
                    <p className="text-xs text-gray-500">Uso</p>
                    <p className="mt-2 text-sm text-gray-200">
                      {subscriptionDetail.current_users} usuarios · {subscriptionDetail.current_documents} docs · {subscriptionDetail.current_storage_mb} MB
                    </p>
                  </div>
                  <div className="rounded-xl border border-gray-700/50 bg-dark-400/30 p-4">
                    <p className="text-xs text-gray-500">Trial</p>
                    <p className="mt-2 text-sm text-gray-200">
                      {subscriptionDetail.is_trial ? `${subscriptionDetail.trial_days_remaining} días restantes` : 'No está en trial'}
                    </p>
                  </div>
                </div>

                <div className="mt-5 flex flex-col gap-3 border-t border-gray-700/50 pt-5 lg:flex-row lg:items-center lg:justify-between">
                  <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
                    <select
                      className="input-glass min-w-[260px] py-2 text-sm"
                      value={subscriptionDetail.plan?.id || subscriptionDetail.plan || ''}
                      disabled={subscriptionActionLoading}
                      onChange={(event) => handleSubscriptionPlanChange(event.target.value)}
                    >
                      <option value="">Seleccionar plan...</option>
                      {plans.map((plan) => (
                        <option key={plan.id} value={plan.id}>
                          {plan.name} · {plan.price} {plan.currency}
                        </option>
                      ))}
                    </select>
                    <span className="text-xs text-gray-500">Cambiar plan actualiza el contrato financiero, no los entitlements individuales.</span>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {subscriptionDetail.status !== 'active' && (
                      <button type="button" onClick={handleSubscriptionActivate} disabled={subscriptionActionLoading} className="btn-primary inline-flex items-center gap-2 px-4 py-2 text-sm disabled:opacity-60">
                        <PlayCircle className="h-4 w-4" />
                        Activar
                      </button>
                    )}
                    {subscriptionDetail.status !== 'cancelled' && (
                      <button type="button" onClick={handleSubscriptionCancel} disabled={subscriptionActionLoading} className="btn-danger inline-flex items-center gap-2 px-4 py-2 text-sm disabled:opacity-60">
                        <Ban className="h-4 w-4" />
                        Cancelar
                      </button>
                    )}
                  </div>
                </div>
              </>
            )}
          </div>

          {subscriptionDetail && (
            <div className="glass-card p-6">
              <div className="mb-4 flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-semibold text-gray-100">Facturas de la suscripción</h3>
                  <p className="mt-1 text-sm text-gray-500">Historial financiero vinculado al contrato.</p>
                </div>
                <CreditCard className="h-5 w-5 text-primary-300" />
              </div>
              {subscriptionInvoices.length === 0 ? (
                <div className="rounded-xl border border-gray-700/50 bg-dark-400/30 p-8 text-center text-sm text-gray-500">
                  No hay facturas asociadas a esta suscripción.
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="table-glass">
                    <thead>
                      <tr>
                        <th>Factura</th>
                        <th>Estado</th>
                        <th>Total</th>
                        <th>Emitida</th>
                        <th>Vence</th>
                      </tr>
                    </thead>
                    <tbody>
                      {subscriptionInvoices.map((invoice) => (
                        <tr key={invoice.id}>
                          <td className="font-medium text-gray-100">{invoice.number}</td>
                          <td><AccessBadge status={invoice.status}>{invoice.status}</AccessBadge></td>
                          <td>{invoice.total} {invoice.currency}</td>
                          <td className="text-sm text-gray-400">{formatDate(invoice.issued_at)}</td>
                          <td className="text-sm text-gray-400">{formatDate(invoice.due_date)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {organization.billing_exempt && (
            <div className="rounded-xl border border-emerald-400/25 bg-emerald-500/10 p-4 text-sm text-emerald-200">
              Smart3AI está marcada como organización dueña y no participa en ciclos de cobro ni en facturación manual.
            </div>
          )}
        </div>
      )}

      {activeTab === 'billing' && (
        <div className="space-y-5">
          <div className="glass-card p-6">
            <div className="mb-5 flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
              <div>
                <p className="enterprise-kicker">Estado financiero</p>
                <h2 className="mt-1 text-lg font-semibold text-slate-950">Billing y cobros</h2>
                <p className="mt-2 max-w-3xl text-sm text-slate-600">
                  Vista operativa del estado financiero asociado al acceso comercial. Los productos con billing dependen de una suscripción efectiva.
                </p>
              </div>
              <button
                type="button"
                onClick={refreshSubscriptionDetail}
                disabled={subscriptionLoading || !organization.subscription}
                className="btn-secondary disabled:opacity-60"
              >
                <RefreshCw className={`h-4 w-4 ${subscriptionLoading ? 'animate-spin' : ''}`} />
                Refrescar billing
              </button>
            </div>

            <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
              <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                <p className="text-xs font-medium text-slate-500">Billing enabled</p>
                <p className="mt-2 text-lg font-semibold text-slate-950">
                  {products.some((product) => product.billing_enabled) ? 'Requerido por producto' : 'No requerido'}
                </p>
              </div>
              <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                <p className="text-xs font-medium text-slate-500">Suscripción</p>
                <p className="mt-2">
                  <AccessBadge status={subscriptionDetail?.status || 'not_configured'}>
                    {subscriptionDetail?.status || 'Sin suscripción'}
                  </AccessBadge>
                </p>
              </div>
              <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                <p className="text-xs font-medium text-slate-500">Monto</p>
                <p className="mt-2 text-lg font-semibold text-slate-950">
                  {subscriptionDetail ? `${subscriptionDetail.amount || 0} ${subscriptionDetail.plan?.currency || ''}` : '-'}
                </p>
              </div>
              <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                <p className="text-xs font-medium text-slate-500">Facturas</p>
                <p className="mt-2 text-lg font-semibold text-slate-950">{subscriptionInvoices.length}</p>
              </div>
            </div>

            {organization.billing_exempt && (
              <div className="mt-5 rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-800">
                Esta organización está exenta de cobro. El billing no debe bloquear accesos comerciales para el owner account.
              </div>
            )}

            {!subscriptionDetail && !organization.billing_exempt && (
              <div className="mt-5 rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
                No hay suscripción vinculada. Los productos que requieren billing no podrán operar como activos hasta asociar un contrato financiero.
              </div>
            )}
          </div>

          <div className="glass-card p-6">
            <div className="mb-4 flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-slate-950">Cobros y facturas</h3>
                <p className="mt-1 text-sm text-slate-500">Historial disponible desde el servicio de suscripciones.</p>
              </div>
              <CreditCard className="h-5 w-5 text-primary-600" />
            </div>
            {subscriptionLoading ? (
              <div className="space-y-3">
                {[0, 1, 2].map((item) => (
                  <div key={item} className="h-14 rounded-lg skeleton" />
                ))}
              </div>
            ) : subscriptionInvoices.length === 0 ? (
              <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50 p-8 text-center">
                <CreditCard className="mx-auto h-10 w-10 text-slate-400" />
                <h3 className="mt-3 text-base font-semibold text-slate-950">Sin facturas disponibles</h3>
                <p className="mt-1 text-sm text-slate-500">Cuando existan cobros o facturas vinculadas a la suscripción aparecerán aquí.</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="table-glass">
                  <thead>
                    <tr>
                      <th>Factura</th>
                      <th>Estado</th>
                      <th>Total</th>
                      <th>Emitida</th>
                      <th>Vence</th>
                    </tr>
                  </thead>
                  <tbody>
                    {subscriptionInvoices.map((invoice) => (
                      <tr key={invoice.id}>
                        <td className="font-medium text-slate-950">{invoice.number || `INV-${String(invoice.id).slice(0, 8)}`}</td>
                        <td><AccessBadge status={invoice.status}>{invoice.status}</AccessBadge></td>
                        <td>{invoice.total} {invoice.currency}</td>
                        <td className="text-sm text-slate-500">{formatDate(invoice.issued_at)}</td>
                        <td className="text-sm text-slate-500">{formatDate(invoice.due_date)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {showUserModal && (
        <OrganizationUserModal
          organization={organization}
          onClose={() => setShowUserModal(false)}
          onCreated={handleUserCreated}
        />
      )}
    </div>
  );
};

export default OrganizationDetailPage;
