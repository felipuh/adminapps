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

// Subscription Card Component
const SubscriptionCard = ({ subscription }) => {
  const statusConfig = {
    active: { color: 'text-emerald-400', bg: 'bg-emerald-500/10', border: 'border-emerald-500/30', icon: CheckCircle, label: 'Activa' },
    trial: { color: 'text-cyan-400', bg: 'bg-cyan-500/10', border: 'border-cyan-500/30', icon: Clock, label: 'Trial' },
    past_due: { color: 'text-amber-400', bg: 'bg-amber-500/10', border: 'border-amber-500/30', icon: AlertTriangle, label: 'Vencida' },
    cancelled: { color: 'text-red-400', bg: 'bg-red-500/10', border: 'border-red-500/30', icon: XCircle, label: 'Cancelada' },
    expired: { color: 'text-gray-400', bg: 'bg-gray-500/10', border: 'border-gray-500/30', icon: XCircle, label: 'Expirada' },
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
            <span>Monto</span>
          </div>
          <p className="text-lg font-semibold text-gray-100">${subscription.amount}/mes</p>
        </div>
        <div className="p-3 bg-dark-400/30 rounded-lg">
          <div className="flex items-center gap-2 text-gray-500 text-sm mb-1">
            <Calendar className="w-4 h-4" />
            <span>Próximo Pago</span>
          </div>
          <p className="text-lg font-semibold text-gray-100">
            {subscription.next_payment_date 
              ? new Date(subscription.next_payment_date).toLocaleDateString('es-MX', { day: 'numeric', month: 'short' })
              : '-'
            }
          </p>
        </div>
      </div>

      <div className="flex gap-2">
        <button className="flex-1 btn-secondary py-2 text-sm">Ver Detalles</button>
        <button className="flex-1 btn-primary py-2 text-sm">Gestionar</button>
      </div>
    </div>
  );
};

// Plan Card Component
const PlanCard = ({ plan, featured }) => (
  <div className={`
    glass-card p-6 relative overflow-hidden
    ${featured ? 'border-primary-500/50 ring-2 ring-primary-500/20' : ''}
  `}>
    {featured && (
      <div className="absolute top-4 right-4 px-3 py-1 bg-primary-500 text-white text-xs font-semibold rounded-full">
        Popular
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
      Seleccionar Plan
    </button>
  </div>
);

const SubscriptionsPage = () => {
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
            name: 'Básico',
            description: 'Para pequeñas empresas',
            price: 199,
            features: ['Hasta 5 usuarios', '100 documentos', '500 MB almacenamiento', 'Módulos básicos ISO', 'Soporte por email'],
          },
          {
            id: '2',
            name: 'Premium',
            description: 'Para empresas en crecimiento',
            price: 499,
            features: ['Hasta 20 usuarios', '500 documentos', '2 GB almacenamiento', 'Todos los módulos ISO', 'Análisis IA', 'Soporte prioritario'],
          },
          {
            id: '3',
            name: 'Enterprise',
            description: 'Para grandes corporativos',
            price: 999,
            features: ['Usuarios ilimitados', 'Documentos ilimitados', '10 GB almacenamiento', 'Todos los módulos ISO', 'Análisis IA avanzado', 'API acceso', 'Soporte 24/7'],
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
          <h1 className="text-2xl font-bold text-gray-100">Suscripciones</h1>
          <p className="text-gray-500 mt-1">Gestiona planes y suscripciones</p>
        </div>
        <button className="btn-primary flex items-center gap-2">
          <Plus className="w-5 h-5" />
          Nueva Suscripción
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="glass-card p-4">
          <p className="text-gray-500 text-sm">Total Suscripciones</p>
          <p className="text-2xl font-bold text-gray-100 mt-1">{stats.total}</p>
        </div>
        <div className="glass-card p-4">
          <p className="text-gray-500 text-sm">Activas</p>
          <p className="text-2xl font-bold text-emerald-400 mt-1">{stats.active}</p>
        </div>
        <div className="glass-card p-4">
          <p className="text-gray-500 text-sm">En Trial</p>
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
          Suscripciones
        </button>
        <button
          onClick={() => setActiveTab('plans')}
          className={`px-4 py-2 rounded-lg font-medium transition-colors ${
            activeTab === 'plans' 
              ? 'bg-primary-500/20 text-primary-400' 
              : 'text-gray-400 hover:text-gray-200 hover:bg-dark-200/50'
          }`}
        >
          Planes
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
                  placeholder="Buscar por organización..."
                  className="input-glass pl-11"
                />
              </div>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="input-glass w-auto"
              >
                <option value="">Todos los estados</option>
                <option value="active">Activas</option>
                <option value="trial">Trial</option>
                <option value="past_due">Vencidas</option>
                <option value="cancelled">Canceladas</option>
              </select>
            </div>
          </div>

          {/* Subscriptions Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredSubscriptions.map((subscription) => (
              <SubscriptionCard key={subscription.id} subscription={subscription} />
            ))}
          </div>

          {filteredSubscriptions.length === 0 && (
            <div className="glass-card p-8 text-center">
              <CreditCard className="w-12 h-12 text-gray-600 mx-auto mb-4" />
              <p className="text-gray-400">No se encontraron suscripciones</p>
            </div>
          )}
        </>
      )}

      {activeTab === 'plans' && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {plans.map((plan, index) => (
            <PlanCard key={plan.id} plan={plan} featured={index === 1} />
          ))}
        </div>
      )}
    </div>
  );
};

export default SubscriptionsPage;
