import { useState, useEffect } from 'react';
import { 
  Building2, 
  Users, 
  TrendingUp, 
  Activity,
  AlertTriangle,
  CheckCircle,
  Clock,
  PackageCheck,
  PackageX,
} from 'lucide-react';
import { dashboardService, organizationService } from '../services/api';
import { useAuth } from '../contexts/AuthContext';

// Stats Card Component
const StatCard = ({ title, value, subtitle, icon: Icon, color }) => {
  const colorClasses = {
    blue: 'from-primary-500 to-primary-600 shadow-primary-500/25',
    green: 'from-emerald-500 to-emerald-600 shadow-emerald-500/25',
    purple: 'from-primary-600 to-primary-700 shadow-primary-500/25',
    orange: 'from-orange-500 to-orange-600 shadow-orange-500/25',
    red: 'from-red-500 to-red-600 shadow-red-500/25',
  };

  return (
    <div className="glass-card p-6 relative overflow-hidden">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-gray-400 text-sm font-medium">{title}</p>
          <p className="text-3xl font-bold text-gray-100 mt-2">{value}</p>
          {subtitle && <p className="mt-2 text-sm text-gray-500">{subtitle}</p>}
        </div>
        <div className={`p-3 rounded-xl bg-gradient-to-br ${colorClasses[color]} shadow-lg`}>
          <Icon className="w-6 h-6 text-white" />
        </div>
      </div>
    </div>
  );
};

// Recent Activity Item
const ActivityItem = ({ activity }) => {
  const typeConfig = {
    organization_created: { icon: Building2, color: 'text-primary-400', bg: 'bg-primary-500/10' },
    user_created: { icon: Users, color: 'text-emerald-400', bg: 'bg-emerald-500/10' },
    subscription_updated: { icon: TrendingUp, color: 'text-primary-300', bg: 'bg-primary-500/10' },
    alert: { icon: AlertTriangle, color: 'text-amber-400', bg: 'bg-amber-500/10' },
  };

  const config = typeConfig[activity.type] || typeConfig.alert;
  const Icon = config.icon;

  return (
    <div className="flex items-start gap-4 p-4 rounded-lg hover:bg-dark-200/30 transition-colors">
      <div className={`p-2 rounded-lg ${config.bg}`}>
        <Icon className={`w-5 h-5 ${config.color}`} />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm text-gray-200">{activity.message || activity.description || activity.action}</p>
        <p className="text-xs text-gray-500 mt-1">{activity.time || (activity.created_at ? new Date(activity.created_at).toLocaleString('es-MX') : '')}</p>
      </div>
    </div>
  );
};

// Organization Status Card
const OrganizationStatusCard = ({ org, usersLabel }) => {
  const statusColors = {
    active: 'badge-success',
    trial: 'badge-info',
    suspended: 'badge-danger',
    inactive: 'badge-neutral',
  };

  return (
    <div className="flex items-center justify-between p-4 rounded-lg hover:bg-dark-200/30 transition-colors">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-primary-500/20 to-primary-600/20 flex items-center justify-center">
          <Building2 className="w-5 h-5 text-primary-400" />
        </div>
        <div>
          <p className="text-sm font-medium text-gray-200">{org.name}</p>
          <p className="text-xs text-gray-500">{org.users_count} {usersLabel}</p>
        </div>
      </div>
      <span className={statusColors[org.status]}>{org.status}</span>
    </div>
  );
};

const DashboardPage = () => {
  const { user } = useAuth();
  const isEnglish = user?.language === 'en';
  const t = {
    users: isEnglish ? 'users' : 'usuarios',
    title: isEnglish ? 'Dashboard' : 'Dashboard',
    subtitle: isEnglish ? 'System overview' : 'Resumen general del sistema',
    totalOrganizations: isEnglish ? 'Organizations' : 'Organizaciones',
    activeOrganizations: isEnglish ? 'Active Organizations' : 'Organizaciones Activas',
    totalUsers: isEnglish ? 'Total Users' : 'Usuarios Totales',
    monthlyRevenue: isEnglish ? 'Monthly Revenue' : 'Ingresos Mensuales',
    productsTitle: isEnglish ? 'SaaS Product Control' : 'Control de productos SaaS',
    productsSubtitle: isEnglish ? 'Real commercial entitlements by customer' : 'Entitlements comerciales reales por cliente',
    activeEntitlements: isEnglish ? 'Active entitlements' : 'Entitlements activos',
    trialEntitlements: isEnglish ? 'Trials' : 'Trials',
    suspendedEntitlements: isEnglish ? 'Suspended' : 'Suspendidos',
    bothProducts: isEnglish ? 'Both products' : 'Ambos productos',
    isoOnly: isEnglish ? 'ISO only' : 'Solo ISO',
    medsupplierOnly: isEnglish ? 'MedSupplier only' : 'Solo MedSupplier',
    noActiveProduct: isEnglish ? 'No active product' : 'Sin producto activo',
    isoSmartCustomers: isEnglish ? 'ISO Smart customers' : 'Clientes con ISO Smart',
    medsupplierCustomers: isEnglish ? 'MedSupplier customers' : 'Clientes con MedSupplier',
    readinessReady: isEnglish ? 'Ready' : 'Listo',
    readinessAttention: isEnglish ? 'Attention required' : 'Requiere atención',
    readinessUnavailable: isEnglish ? 'Readiness unavailable' : 'Readiness no disponible',
    readinessSubtitle: isEnglish ? 'Control-plane readiness' : 'Readiness del control plane',
    legacyWatchlist: isEnglish ? 'Legacy watchlist' : 'Watchlist legacy',
    requiredProducts: isEnglish ? 'Required products' : 'Productos requeridos',
    billingGate: isEnglish ? 'Billing gate' : 'Control billing',
    review: isEnglish ? 'Review' : 'Revisar',
    legacyIssues: isEnglish ? 'Legacy plans mention products without entitlement.' : 'Planes legacy mencionan productos sin entitlement.',
    noLegacyIssues: isEnglish ? 'No legacy bypass risks detected' : 'Sin riesgos legacy detectados',
    missingEntitlements: isEnglish ? 'Missing entitlements' : 'Entitlements faltantes',
    recentActivity: isEnglish ? 'Recent Activity' : 'Actividad Reciente',
    recentOrganizations: isEnglish ? 'Recent Organizations' : 'Organizaciones Recientes',
    viewAll: isEnglish ? 'View all ->' : 'Ver todas ->',
    alertsTitle: isEnglish ? 'Alerts and Pending' : 'Alertas y Pendientes',
    noActivity: isEnglish ? 'No recent activity available' : 'No hay actividad reciente disponible',
    noAlerts: isEnglish ? 'No current alerts' : 'No hay alertas actuales',
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

  useEffect(() => {
    const fetchData = async () => {
      try {
        // Try to fetch real data
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
          setStats({
            totalOrganizations: 0,
            activeOrganizations: 0,
            totalUsers: 0,
            monthlyRevenue: 0,
            products: {},
          });
        }

        if (orgsData?.results) {
          setRecentOrgs(orgsData.results);
        } else if (dashboardData?.recent_organizations) {
          setRecentOrgs(dashboardData.recent_organizations);
        } else {
          setRecentOrgs([]);
        }

        setProductReadiness(readinessData);
      } catch (error) {
        console.error('Error fetching dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="glass-card p-6 h-32 skeleton" />
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 glass-card p-6 h-80 skeleton" />
          <div className="glass-card p-6 h-80 skeleton" />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Page header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-100">{t.title}</h1>
        <p className="text-gray-500 mt-1">{t.subtitle}</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title={t.totalOrganizations}
          value={stats.totalOrganizations}
          subtitle={`${stats.products.systems_active || 0} productos activos`}
          icon={Building2}
          color="blue"
        />
        <StatCard
          title={t.activeOrganizations}
          value={stats.activeOrganizations}
          subtitle={`${stats.products.customers_with_both || 0} con ambos productos`}
          icon={CheckCircle}
          color="green"
        />
        <StatCard
          title={t.activeEntitlements}
          value={stats.products.entitlements_active || 0}
          subtitle={`${stats.products.entitlements_trial || 0} trials activos`}
          icon={PackageCheck}
          color="purple"
        />
        <StatCard
          title={t.suspendedEntitlements}
          value={stats.products.entitlements_suspended || 0}
          subtitle="Requieren revisión operativa"
          icon={PackageX}
          color="red"
        />
      </div>

      {/* Charts and Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Product Control Summary */}
        <div className="lg:col-span-2 glass-card p-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-lg font-semibold text-gray-100">{t.productsTitle}</h2>
              <p className="text-sm text-gray-500">{t.productsSubtitle}</p>
            </div>
            <PackageCheck className="h-5 w-5 text-primary-300" />
          </div>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            <div className="rounded-xl border border-gray-700/50 bg-dark-400/30 p-5">
              <p className="text-sm text-gray-500">{t.isoSmartCustomers}</p>
              <p className="mt-2 text-3xl font-bold text-gray-100">{stats.products.iso_smart_customers || 0}</p>
            </div>
            <div className="rounded-xl border border-gray-700/50 bg-dark-400/30 p-5">
              <p className="text-sm text-gray-500">{t.medsupplierCustomers}</p>
              <p className="mt-2 text-3xl font-bold text-gray-100">{stats.products.medsupplier_customers || 0}</p>
            </div>
            <div className="rounded-xl border border-gray-700/50 bg-dark-400/30 p-5">
              <p className="text-sm text-gray-500">{t.bothProducts}</p>
              <p className="mt-2 text-3xl font-bold text-emerald-300">{stats.products.customers_with_both || 0}</p>
            </div>
          </div>
          <div className="mt-4 rounded-xl border border-gray-700/50 bg-slate-950/20 p-4 text-sm text-gray-400">
            Los productos SaaS se cuentan desde <span className="text-gray-200">OrganizationProductEntitlement</span>. Los módulos legacy no se consideran acceso comercial.
          </div>
          <div className="mt-4 grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">
            <div className={`rounded-xl border p-4 ${
              productReadiness?.status === 'ready'
                ? 'border-emerald-500/25 bg-emerald-500/10'
                : productReadiness
                  ? 'border-amber-500/25 bg-amber-500/10'
                  : 'border-gray-700/50 bg-dark-400/30'
            }`}>
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="text-xs uppercase tracking-[0.2em] text-gray-500">{t.readinessSubtitle}</p>
                  <p className="mt-1 text-lg font-semibold text-gray-100">
                    {productReadiness
                      ? (productReadiness.status === 'ready' ? t.readinessReady : t.readinessAttention)
                      : t.readinessUnavailable}
                  </p>
                </div>
                {productReadiness?.status === 'ready' ? (
                  <CheckCircle className="h-6 w-6 text-emerald-300" />
                ) : (
                  <AlertTriangle className="h-6 w-6 text-amber-300" />
                )}
              </div>
              <div className="mt-4 grid grid-cols-1 gap-2 text-sm text-gray-300 sm:grid-cols-2">
                <div className="rounded-lg border border-gray-700/40 bg-slate-950/20 p-3">
                  <p className="text-gray-500">{t.requiredProducts}</p>
                  <p className="mt-1 font-medium">
                    {productReadiness?.checks?.required_products_exist && productReadiness?.checks?.required_products_available ? 'OK' : t.review}
                  </p>
                </div>
                <div className="rounded-lg border border-gray-700/40 bg-slate-950/20 p-3">
                  <p className="text-gray-500">{t.billingGate}</p>
                  <p className="mt-1 font-medium">
                    {productReadiness?.checks?.billing_active_requires_entitlement ? 'OK' : t.review}
                  </p>
                </div>
              </div>
              <div className="mt-4 grid grid-cols-2 gap-2 text-sm text-gray-300 lg:grid-cols-4">
                <div className="rounded-lg border border-gray-700/40 bg-slate-950/20 p-3">
                  <p className="text-gray-500">{t.isoOnly}</p>
                  <p className="mt-1 font-semibold text-gray-100">{productReadiness?.commercial_scenarios?.iso_smart_only ?? '-'}</p>
                </div>
                <div className="rounded-lg border border-gray-700/40 bg-slate-950/20 p-3">
                  <p className="text-gray-500">{t.medsupplierOnly}</p>
                  <p className="mt-1 font-semibold text-gray-100">{productReadiness?.commercial_scenarios?.medsupplier_only ?? '-'}</p>
                </div>
                <div className="rounded-lg border border-gray-700/40 bg-slate-950/20 p-3">
                  <p className="text-gray-500">{t.bothProducts}</p>
                  <p className="mt-1 font-semibold text-emerald-200">{productReadiness?.commercial_scenarios?.both_products ?? '-'}</p>
                </div>
                <div className="rounded-lg border border-gray-700/40 bg-slate-950/20 p-3">
                  <p className="text-gray-500">{t.noActiveProduct}</p>
                  <p className="mt-1 font-semibold text-amber-200">{productReadiness?.commercial_scenarios?.no_active_product ?? '-'}</p>
                </div>
              </div>
            </div>
            <div className="rounded-xl border border-gray-700/50 bg-dark-400/30 p-4">
              <p className="text-xs uppercase tracking-[0.2em] text-gray-500">{t.legacyWatchlist}</p>
              <p className="mt-2 text-3xl font-bold text-gray-100">
                {productReadiness?.legacy_bypass_watchlist?.plan_product_mentions_without_entitlement ?? '-'}
              </p>
              <p className="mt-2 text-sm text-gray-500">
                {(productReadiness?.legacy_bypass_watchlist?.plan_product_mentions_without_entitlement || 0) === 0
                  ? t.noLegacyIssues
                  : t.legacyIssues}
              </p>
              {(productReadiness?.legacy_bypass_watchlist?.items || []).length > 0 && (
                <div className="mt-4 space-y-2">
                  {productReadiness.legacy_bypass_watchlist.items.slice(0, 3).map((item) => (
                    <div key={`${item.organization_id}-${item.plan_code}`} className="rounded-lg border border-amber-500/20 bg-amber-500/10 p-3">
                      <p className="text-sm font-medium text-amber-100">{item.organization_code}</p>
                      <p className="mt-1 text-xs text-amber-200/80">{item.plan_code}</p>
                      <p className="mt-1 text-xs text-gray-400">
                        {t.missingEntitlements}: {item.missing_entitlements?.join(', ')}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Recent Activity */}
        <div className="glass-card p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-100">{t.recentActivity}</h2>
            <Activity className="w-5 h-5 text-gray-500" />
          </div>
          <div className="space-y-1 -mx-4">
            {recentActivity.length > 0 ? recentActivity.slice(0, 5).map((activity) => (
              <ActivityItem key={activity.id} activity={activity} />
            )) : (
              <p className="px-4 py-8 text-center text-sm text-gray-500">{t.noActivity}</p>
            )}
          </div>
        </div>
      </div>

      {/* Organizations Overview */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Organizations */}
        <div className="glass-card p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-100">{t.recentOrganizations}</h2>
            <a href="/organizations" className="text-sm text-primary-400 hover:text-primary-300 transition-colors">
              {t.viewAll}
            </a>
          </div>
          <div className="space-y-1 -mx-4">
            {recentOrgs.length > 0 ? recentOrgs.map((org) => (
              <OrganizationStatusCard key={org.id} org={org} usersLabel={t.users} />
            )) : (
              <p className="px-4 py-8 text-center text-sm text-gray-500">{t.noActivity}</p>
            )}
          </div>
        </div>

        {/* Quick Actions / Alerts */}
        <div className="glass-card p-6">
          <h2 className="text-lg font-semibold text-gray-100 mb-4">{t.alertsTitle}</h2>
          
          <div className="space-y-4">
            {alerts.length > 0 ? alerts.slice(0, 5).map((alert, index) => (
              <div key={`${alert.message}-${index}`} className="flex items-start gap-4 p-4 bg-amber-500/10 border border-amber-500/30 rounded-lg">
                <Clock className="w-5 h-5 text-amber-400 flex-shrink-0" />
                <div>
                  <p className="text-sm font-medium text-amber-300">{alert.message}</p>
                  {alert.date && <p className="text-xs text-gray-400 mt-1">{new Date(alert.date).toLocaleString('es-MX')}</p>}
                </div>
              </div>
            )) : (
              <div className="rounded-lg border border-emerald-500/25 bg-emerald-500/10 p-6 text-center">
                <CheckCircle className="mx-auto h-8 w-8 text-emerald-300" />
                <p className="mt-3 text-sm font-medium text-emerald-200">{t.noAlerts}</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;
