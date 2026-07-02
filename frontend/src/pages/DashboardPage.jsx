import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Activity,
  AlertTriangle,
  Building2,
  CheckCircle,
  Clock,
  PackageCheck,
  PackageX,
  Users,
} from 'lucide-react';
import { dashboardService, organizationService } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import {
  Card,
  EmptyState,
  ErrorState,
  LoadingState,
  MetricCard,
  PageHeader,
  SectionHeader,
  StatusBadge,
} from '../components/ui/EnterpriseUI';

const formatDateTime = (value, locale = 'es-MX') => {
  if (!value) return '';
  return new Date(value).toLocaleString(locale, {
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  });
};

const ActivityItem = ({ activity, locale }) => {
  const typeConfig = {
    organization_created: { icon: Building2, tone: 'bg-blue-50 text-blue-700 border-blue-100' },
    user_created: { icon: Users, tone: 'bg-emerald-50 text-emerald-700 border-emerald-100' },
    subscription_updated: { icon: PackageCheck, tone: 'bg-indigo-50 text-indigo-700 border-indigo-100' },
    alert: { icon: AlertTriangle, tone: 'bg-amber-50 text-amber-700 border-amber-100' },
  };
  const config = typeConfig[activity.type] || typeConfig.alert;
  const Icon = config.icon;

  return (
    <div className="flex items-start gap-3 rounded-lg px-3 py-3 hover:bg-slate-50">
      <div className={`flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-lg border ${config.tone}`}>
        <Icon className="h-4 w-4" />
      </div>
      <div className="min-w-0 flex-1">
        <p className="text-sm font-medium text-slate-900">{activity.message || activity.description || activity.action}</p>
        <p className="mt-1 text-xs text-slate-500">{activity.time || formatDateTime(activity.created_at, locale)}</p>
      </div>
    </div>
  );
};

const ProductScenario = ({ label, value, tone = 'slate' }) => {
  const tones = {
    blue: 'border-blue-100 bg-blue-50 text-blue-800',
    emerald: 'border-emerald-100 bg-emerald-50 text-emerald-800',
    amber: 'border-amber-100 bg-amber-50 text-amber-800',
    slate: 'border-slate-200 bg-slate-50 text-slate-800',
  };

  return (
    <div className={`rounded-xl border p-4 ${tones[tone] || tones.slate}`}>
      <p className="text-sm opacity-80">{label}</p>
      <p className="mt-2 text-2xl font-semibold">{value ?? '-'}</p>
    </div>
  );
};

const DashboardPage = () => {
  const { user } = useAuth();
  const isEnglish = user?.language === 'en';
  const locale = isEnglish ? 'en-US' : 'es-MX';
  const t = {
    title: isEnglish ? 'Dashboard' : 'Dashboard',
    subtitle: isEnglish
      ? 'Operational overview for customers, subscriptions and SaaS access.'
      : 'Vista operativa de clientes, suscripciones y accesos SaaS.',
    totalOrganizations: isEnglish ? 'Organizations' : 'Organizaciones',
    activeOrganizations: isEnglish ? 'Active organizations' : 'Organizaciones activas',
    activeEntitlements: isEnglish ? 'Active entitlements' : 'Entitlements activos',
    suspendedEntitlements: isEnglish ? 'Suspended' : 'Suspendidos',
    productsTitle: isEnglish ? 'SaaS product coverage' : 'Cobertura de productos SaaS',
    productsSubtitle: isEnglish
      ? 'Commercial access is counted from product entitlements, not legacy modules.'
      : 'El acceso comercial se cuenta desde entitlements de producto, no desde módulos legacy.',
    isoSmartCustomers: isEnglish ? 'ISO Smart' : 'ISO Smart',
    medsupplierCustomers: isEnglish ? 'MedSupplier' : 'MedSupplier',
    bothProducts: isEnglish ? 'Both products' : 'Ambos productos',
    isoOnly: isEnglish ? 'ISO only' : 'Solo ISO',
    medsupplierOnly: isEnglish ? 'MedSupplier only' : 'Solo MedSupplier',
    noActiveProduct: isEnglish ? 'No active product' : 'Sin producto activo',
    readinessTitle: isEnglish ? 'Control-plane readiness' : 'Readiness del control plane',
    readinessReady: isEnglish ? 'Ready' : 'Listo',
    readinessAttention: isEnglish ? 'Needs review' : 'Requiere revisión',
    requiredProducts: isEnglish ? 'Required products' : 'Productos requeridos',
    billingGate: isEnglish ? 'Billing gate' : 'Control billing',
    review: isEnglish ? 'Review' : 'Revisar',
    legacyWatchlist: isEnglish ? 'Legacy watchlist' : 'Watchlist legacy',
    recentActivity: isEnglish ? 'Recent activity' : 'Actividad reciente',
    recentOrganizations: isEnglish ? 'Recent organizations' : 'Organizaciones recientes',
    viewAll: isEnglish ? 'View all' : 'Ver todas',
    alertsTitle: isEnglish ? 'Operational alerts' : 'Alertas operativas',
    noActivity: isEnglish ? 'No recent activity available' : 'No hay actividad reciente disponible',
    noAlerts: isEnglish ? 'No current alerts' : 'No hay alertas actuales',
    users: isEnglish ? 'users' : 'usuarios',
  };

  const [stats, setStats] = useState({
    totalOrganizations: 0,
    activeOrganizations: 0,
    totalUsers: 0,
    monthlyRevenue: 0,
    products: {},
  });
  const [recentOrgs, setRecentOrgs] = useState([]);
  const [recentActivity, setRecentActivity] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [productReadiness, setProductReadiness] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      setLoadError(false);
      try {
        const [dashboardData, orgsData, readinessData] = await Promise.all([
          dashboardService.getStats().catch(() => null),
          organizationService.getAll({ limit: 5 }).catch(() => null),
          dashboardService.getProductReadiness().catch(() => null),
        ]);

        if (dashboardData) {
          setStats({
            totalOrganizations: dashboardData.organizations?.total || 0,
            activeOrganizations: dashboardData.organizations?.active || 0,
            totalUsers: dashboardData.team?.total_admins || 0,
            monthlyRevenue: dashboardData.monthly_revenue || 0,
            products: dashboardData.products || {},
          });
          setRecentActivity(dashboardData.recent_activity || []);
          setAlerts(dashboardData.alerts || []);
        } else {
          setLoadError(true);
        }

        if (orgsData?.results) {
          setRecentOrgs(orgsData.results);
        } else if (dashboardData?.recent_organizations) {
          setRecentOrgs(dashboardData.recent_organizations);
        } else {
          setRecentOrgs([]);
        }

        setProductReadiness(readinessData);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="enterprise-page">
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
          {[1, 2, 3, 4].map((i) => <div key={i} className="h-32 rounded-xl skeleton" />)}
        </div>
        <LoadingState label={isEnglish ? 'Loading dashboard...' : 'Cargando dashboard...'} />
      </div>
    );
  }

  return (
    <div className="enterprise-page">
      <PageHeader
        eyebrow={isEnglish ? 'AdminApps control plane' : 'Control plane AdminApps'}
        title={t.title}
        description={t.subtitle}
      />

      {loadError && (
        <ErrorState
          title={isEnglish ? 'Dashboard data is partially unavailable' : 'La data del dashboard está parcialmente disponible'}
          description={isEnglish ? 'Some widgets may show zero values until the API responds.' : 'Algunas secciones pueden mostrar valores en cero hasta que la API responda.'}
        />
      )}

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          label={t.totalOrganizations}
          value={stats.totalOrganizations}
          helper={`${stats.products.systems_active || 0} productos activos`}
          icon={Building2}
          tone="blue"
        />
        <MetricCard
          label={t.activeOrganizations}
          value={stats.activeOrganizations}
          helper={`${stats.products.customers_with_both || 0} con ambos productos`}
          icon={CheckCircle}
          tone="emerald"
        />
        <MetricCard
          label={t.activeEntitlements}
          value={stats.products.entitlements_active || 0}
          helper={`${stats.products.entitlements_trial || 0} trials activos`}
          icon={PackageCheck}
          tone="blue"
        />
        <MetricCard
          label={t.suspendedEntitlements}
          value={stats.products.entitlements_suspended || 0}
          helper="Requieren revisión operativa"
          icon={PackageX}
          tone="red"
        />
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
        <Card className="p-6 xl:col-span-2">
          <SectionHeader
            title={t.productsTitle}
            description={t.productsSubtitle}
            action={<PackageCheck className="h-5 w-5 text-primary-600" />}
          />

          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            <ProductScenario label={t.isoSmartCustomers} value={stats.products.iso_smart_customers || 0} tone="blue" />
            <ProductScenario label={t.medsupplierCustomers} value={stats.products.medsupplier_customers || 0} tone="blue" />
            <ProductScenario label={t.bothProducts} value={stats.products.customers_with_both || 0} tone="emerald" />
          </div>

          <div className="mt-5 rounded-xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-600">
            Los productos SaaS se cuentan desde <span className="font-semibold text-slate-900">OrganizationProductEntitlement</span>. Los módulos legacy se muestran como configuración secundaria.
          </div>

          <div className="mt-5 grid gap-4 lg:grid-cols-[1.35fr_0.65fr]">
            <div className={`rounded-xl border p-5 ${
              productReadiness?.status === 'ready'
                ? 'border-emerald-200 bg-emerald-50'
                : productReadiness
                  ? 'border-amber-200 bg-amber-50'
                  : 'border-slate-200 bg-slate-50'
            }`}>
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.08em] text-slate-500">{t.readinessTitle}</p>
                  <p className="mt-1 text-lg font-semibold text-slate-950">
                    {productReadiness
                      ? (productReadiness.status === 'ready' ? t.readinessReady : t.readinessAttention)
                      : (isEnglish ? 'Unavailable' : 'No disponible')}
                  </p>
                </div>
                {productReadiness?.status === 'ready'
                  ? <CheckCircle className="h-6 w-6 text-emerald-700" />
                  : <AlertTriangle className="h-6 w-6 text-amber-700" />}
              </div>

              <div className="mt-4 grid grid-cols-1 gap-3 text-sm sm:grid-cols-2">
                <div className="rounded-lg border border-white/70 bg-white/70 p-3">
                  <p className="text-slate-500">{t.requiredProducts}</p>
                  <p className="mt-1 font-semibold text-slate-950">
                    {productReadiness?.checks?.required_products_exist && productReadiness?.checks?.required_products_available ? 'OK' : t.review}
                  </p>
                </div>
                <div className="rounded-lg border border-white/70 bg-white/70 p-3">
                  <p className="text-slate-500">{t.billingGate}</p>
                  <p className="mt-1 font-semibold text-slate-950">
                    {productReadiness?.checks?.billing_active_requires_entitlement ? 'OK' : t.review}
                  </p>
                </div>
              </div>

              <div className="mt-4 grid grid-cols-2 gap-3 text-sm lg:grid-cols-4">
                <ProductScenario label={t.isoOnly} value={productReadiness?.commercial_scenarios?.iso_smart_only} />
                <ProductScenario label={t.medsupplierOnly} value={productReadiness?.commercial_scenarios?.medsupplier_only} />
                <ProductScenario label={t.bothProducts} value={productReadiness?.commercial_scenarios?.both_products} tone="emerald" />
                <ProductScenario label={t.noActiveProduct} value={productReadiness?.commercial_scenarios?.no_active_product} tone="amber" />
              </div>
            </div>

            <div className="rounded-xl border border-slate-200 bg-white p-5">
              <p className="text-xs font-semibold uppercase tracking-[0.08em] text-slate-500">{t.legacyWatchlist}</p>
              <p className="mt-2 text-3xl font-semibold text-slate-950">
                {productReadiness?.legacy_bypass_watchlist?.plan_product_mentions_without_entitlement ?? '-'}
              </p>
              <p className="mt-2 text-sm text-slate-500">
                {(productReadiness?.legacy_bypass_watchlist?.plan_product_mentions_without_entitlement || 0) === 0
                  ? 'Sin riesgos legacy detectados'
                  : 'Planes legacy mencionan productos sin entitlement.'}
              </p>
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <SectionHeader title={t.recentActivity} action={<Activity className="h-5 w-5 text-slate-400" />} />
          <div className="-mx-3 space-y-1">
            {recentActivity.length > 0 ? recentActivity.slice(0, 6).map((activity) => (
              <ActivityItem key={activity.id || activity.message} activity={activity} locale={locale} />
            )) : (
              <EmptyState title={t.noActivity} description="Cuando existan cambios operativos aparecerán aquí." />
            )}
          </div>
        </Card>
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <Card className="p-6">
          <SectionHeader
            title={t.recentOrganizations}
            action={<Link to="/organizations" className="text-sm font-semibold text-primary-700 hover:text-primary-900">{t.viewAll}</Link>}
          />
          <div className="-mx-3 space-y-1">
            {recentOrgs.length > 0 ? recentOrgs.map((org) => (
              <div key={org.id} className="flex items-center justify-between gap-4 rounded-lg px-3 py-3 hover:bg-slate-50">
                <div className="flex min-w-0 items-center gap-3">
                  <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg border border-blue-100 bg-blue-50 text-blue-700">
                    <Building2 className="h-5 w-5" />
                  </div>
                  <div className="min-w-0">
                    <p className="truncate text-sm font-semibold text-slate-950">{org.name}</p>
                    <p className="text-xs text-slate-500">{org.users_count || 0} {t.users}</p>
                  </div>
                </div>
                <StatusBadge status={org.status}>{org.status}</StatusBadge>
              </div>
            )) : (
              <EmptyState title={t.noActivity} description="Aún no hay organizaciones recientes para mostrar." />
            )}
          </div>
        </Card>

        <Card className="p-6">
          <SectionHeader title={t.alertsTitle} action={<Clock className="h-5 w-5 text-slate-400" />} />
          <div className="space-y-3">
            {alerts.length > 0 ? alerts.slice(0, 5).map((alert, index) => (
              <div key={`${alert.message}-${index}`} className="flex items-start gap-3 rounded-xl border border-amber-200 bg-amber-50 p-4">
                <AlertTriangle className="mt-0.5 h-5 w-5 flex-shrink-0 text-amber-700" />
                <div>
                  <p className="text-sm font-semibold text-amber-950">{alert.message}</p>
                  {alert.date && <p className="mt-1 text-xs text-amber-800">{formatDateTime(alert.date, locale)}</p>}
                </div>
              </div>
            )) : (
              <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-6 text-center">
                <CheckCircle className="mx-auto h-8 w-8 text-emerald-700" />
                <p className="mt-3 text-sm font-semibold text-emerald-950">{t.noAlerts}</p>
                <p className="mt-1 text-sm text-emerald-700">La operación no reporta bloqueos relevantes.</p>
              </div>
            )}
          </div>
        </Card>
      </div>
    </div>
  );
};

export default DashboardPage;
