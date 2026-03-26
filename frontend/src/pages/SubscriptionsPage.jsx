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
  XCircle
} from 'lucide-react';
import { subscriptionService } from '../services/api';
import { useAuth } from '../contexts/AuthContext';

// Subscription Card Component
const SubscriptionCard = ({ subscription, t, isEnglish }) => {
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
            <h3 className="font-semibold text-gray-100">{subscription.organization_name}</h3>
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
          <p className="text-lg font-semibold text-gray-100">${subscription.amount}/{isEnglish ? 'month' : 'mes'}</p>
        </div>
        <div className="p-3 bg-dark-400/30 rounded-lg">
          <div className="flex items-center gap-2 text-gray-500 text-sm mb-1">
            <Calendar className="w-4 h-4" />
            <span>{t.nextPayment}</span>
          </div>
          <p className="text-lg font-semibold text-gray-100">
            {subscription.next_payment_date 
              ? new Date(subscription.next_payment_date).toLocaleDateString(isEnglish ? 'en-US' : 'es-MX', { day: 'numeric', month: 'short' })
              : '-'
            }
          </p>
        </div>
      </div>

      <div className="flex gap-2">
        <button className="flex-1 btn-secondary py-2 text-sm">{t.viewDetails}</button>
        <button className="flex-1 btn-primary py-2 text-sm">{t.manage}</button>
      </div>
    </div>
  );
};

// Plan Card Component
const PlanCard = ({ plan, featured, t }) => (
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
      <span className="text-gray-500">/mes</span>
    </div>
    
    <ul className="mt-6 space-y-3">
      {plan.features.map((feature, index) => (
        <li key={index} className="flex items-center gap-2 text-sm text-gray-300">
          <CheckCircle className="w-4 h-4 text-emerald-400 flex-shrink-0" />
          {feature}
        </li>
      ))}
    </ul>
    
    <button className={`w-full mt-6 py-2.5 ${featured ? 'btn-primary' : 'btn-secondary'}`}>
      {t.selectPlan}
    </button>
  </div>
);

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
  };
  const [subscriptions, setSubscriptions] = useState([]);
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('subscriptions');
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [subsData, plansData] = await Promise.all([
          subscriptionService.getAll(),
          subscriptionService.getPlans(),
        ]);
        setSubscriptions(subsData.results || subsData);
        setPlans(plansData);
      } catch (error) {
        // Mock data
        setSubscriptions([
          { id: '1', organization_name: 'Tech Corp', plan_name: 'Premium', status: 'active', amount: 499, next_payment_date: '2026-02-15' },
          { id: '2', organization_name: 'Acme Inc', plan_name: 'Básico', status: 'active', amount: 199, next_payment_date: '2026-02-20' },
          { id: '3', organization_name: 'StartupXYZ', plan_name: 'Trial', status: 'trial', amount: 0, next_payment_date: '2026-02-10' },
          { id: '4', organization_name: 'Global Services', plan_name: 'Enterprise', status: 'active', amount: 999, next_payment_date: '2026-03-01' },
          { id: '5', organization_name: 'Local Shop', plan_name: 'Básico', status: 'past_due', amount: 199, next_payment_date: '2026-01-25' },
          { id: '6', organization_name: 'Old Company', plan_name: 'Básico', status: 'cancelled', amount: 199, next_payment_date: null },
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

    fetchData();
  }, []);

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
      .reduce((sum, s) => sum + s.amount, 0),
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
        <button className="btn-primary flex items-center gap-2">
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
              <SubscriptionCard key={subscription.id} subscription={subscription} t={t} isEnglish={isEnglish} />
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
            <PlanCard key={plan.id} plan={plan} featured={index === 1} t={t} />
          ))}
        </div>
      )}
    </div>
  );
};

export default SubscriptionsPage;
