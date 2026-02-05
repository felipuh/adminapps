import React, { useState, useEffect } from 'react';
import { 
  Building2, 
  Users, 
  TrendingUp, 
  Activity,
  AlertTriangle,
  CheckCircle,
  Clock,
  ArrowUpRight,
  ArrowDownRight
} from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';
import { dashboardService, organizationService } from '../services/api';

// Stats Card Component
const StatCard = ({ title, value, change, changeType, icon: Icon, color }) => {
  const colorClasses = {
    blue: 'from-blue-500 to-blue-600 shadow-blue-500/25',
    green: 'from-emerald-500 to-emerald-600 shadow-emerald-500/25',
    purple: 'from-purple-500 to-purple-600 shadow-purple-500/25',
    orange: 'from-orange-500 to-orange-600 shadow-orange-500/25',
  };

  return (
    <div className="glass-card p-6 relative overflow-hidden">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-gray-400 text-sm font-medium">{title}</p>
          <p className="text-3xl font-bold text-gray-100 mt-2">{value}</p>
          {change && (
            <div className={`flex items-center gap-1 mt-2 text-sm ${
              changeType === 'increase' ? 'text-emerald-400' : 'text-red-400'
            }`}>
              {changeType === 'increase' ? (
                <ArrowUpRight className="w-4 h-4" />
              ) : (
                <ArrowDownRight className="w-4 h-4" />
              )}
              <span>{change}% vs mes anterior</span>
            </div>
          )}
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
    organization_created: { icon: Building2, color: 'text-blue-400', bg: 'bg-blue-500/10' },
    user_created: { icon: Users, color: 'text-emerald-400', bg: 'bg-emerald-500/10' },
    subscription_updated: { icon: TrendingUp, color: 'text-purple-400', bg: 'bg-purple-500/10' },
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
        <p className="text-sm text-gray-200">{activity.message}</p>
        <p className="text-xs text-gray-500 mt-1">{activity.time}</p>
      </div>
    </div>
  );
};

// Organization Status Card
const OrganizationStatusCard = ({ org }) => {
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
          <p className="text-xs text-gray-500">{org.users_count} usuarios</p>
        </div>
      </div>
      <span className={statusColors[org.status]}>{org.status}</span>
    </div>
  );
};

const DashboardPage = () => {
  const [stats, setStats] = useState({
    totalOrganizations: 0,
    activeOrganizations: 0,
    totalUsers: 0,
    monthlyRevenue: 0,
  });
  const [recentOrgs, setRecentOrgs] = useState([]);
  const [loading, setLoading] = useState(true);

  // Mock data for chart
  const chartData = [
    { name: 'Ene', organizations: 4, users: 24 },
    { name: 'Feb', organizations: 6, users: 35 },
    { name: 'Mar', organizations: 8, users: 47 },
    { name: 'Abr', organizations: 10, users: 62 },
    { name: 'May', organizations: 12, users: 78 },
    { name: 'Jun', organizations: 15, users: 95 },
  ];

  // Mock recent activity
  const recentActivity = [
    { id: 1, type: 'organization_created', message: 'Nueva organización "Tech Corp" registrada', time: 'Hace 5 minutos' },
    { id: 2, type: 'user_created', message: 'Usuario juan@techcorp.com añadido', time: 'Hace 15 minutos' },
    { id: 3, type: 'subscription_updated', message: 'Suscripción de "Acme Inc" actualizada a Premium', time: 'Hace 1 hora' },
    { id: 4, type: 'alert', message: 'Trial de "StartupXYZ" expira en 3 días', time: 'Hace 2 horas' },
    { id: 5, type: 'organization_created', message: 'Nueva organización "Global Services" registrada', time: 'Hace 3 horas' },
  ];

  useEffect(() => {
    const fetchData = async () => {
      try {
        // Try to fetch real data
        const [dashboardData, orgsData] = await Promise.all([
          dashboardService.getStats().catch(() => null),
          organizationService.getAll({ limit: 5 }).catch(() => null),
        ]);

        if (dashboardData) {
          setStats(dashboardData);
        } else {
          // Use mock data
          setStats({
            totalOrganizations: 24,
            activeOrganizations: 18,
            totalUsers: 156,
            monthlyRevenue: 12450,
          });
        }

        if (orgsData?.results) {
          setRecentOrgs(orgsData.results);
        } else {
          // Mock organizations
          setRecentOrgs([
            { id: 1, name: 'Tech Corp', status: 'active', users_count: 15 },
            { id: 2, name: 'Acme Inc', status: 'active', users_count: 8 },
            { id: 3, name: 'StartupXYZ', status: 'trial', users_count: 3 },
            { id: 4, name: 'Global Services', status: 'active', users_count: 12 },
            { id: 5, name: 'Local Shop', status: 'suspended', users_count: 2 },
          ]);
        }
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
        <h1 className="text-2xl font-bold text-gray-100">Dashboard</h1>
        <p className="text-gray-500 mt-1">Resumen general del sistema</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Organizaciones"
          value={stats.totalOrganizations}
          change={12}
          changeType="increase"
          icon={Building2}
          color="blue"
        />
        <StatCard
          title="Organizaciones Activas"
          value={stats.activeOrganizations}
          change={8}
          changeType="increase"
          icon={CheckCircle}
          color="green"
        />
        <StatCard
          title="Usuarios Totales"
          value={stats.totalUsers}
          change={15}
          changeType="increase"
          icon={Users}
          color="purple"
        />
        <StatCard
          title="Ingresos Mensuales"
          value={`$${stats.monthlyRevenue.toLocaleString()}`}
          change={5}
          changeType="increase"
          icon={TrendingUp}
          color="orange"
        />
      </div>

      {/* Charts and Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Growth Chart */}
        <div className="lg:col-span-2 glass-card p-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-lg font-semibold text-gray-100">Crecimiento</h2>
              <p className="text-sm text-gray-500">Organizaciones y usuarios por mes</p>
            </div>
            <select className="bg-dark-400 border border-gray-700/50 rounded-lg px-3 py-2 text-sm text-gray-300 focus:outline-none focus:border-primary-500/50">
              <option>Últimos 6 meses</option>
              <option>Último año</option>
              <option>Todo el tiempo</option>
            </select>
          </div>
          
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient id="colorOrgs" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="colorUsers" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.3} />
                <XAxis dataKey="name" stroke="#6b7280" fontSize={12} />
                <YAxis stroke="#6b7280" fontSize={12} />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#1e293b', 
                    border: '1px solid rgba(71, 85, 105, 0.5)',
                    borderRadius: '8px',
                    color: '#f1f5f9'
                  }} 
                />
                <Area 
                  type="monotone" 
                  dataKey="organizations" 
                  stroke="#3b82f6" 
                  fillOpacity={1} 
                  fill="url(#colorOrgs)" 
                  name="Organizaciones"
                />
                <Area 
                  type="monotone" 
                  dataKey="users" 
                  stroke="#10b981" 
                  fillOpacity={1} 
                  fill="url(#colorUsers)" 
                  name="Usuarios"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Recent Activity */}
        <div className="glass-card p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-100">Actividad Reciente</h2>
            <Activity className="w-5 h-5 text-gray-500" />
          </div>
          <div className="space-y-1 -mx-4">
            {recentActivity.slice(0, 5).map((activity) => (
              <ActivityItem key={activity.id} activity={activity} />
            ))}
          </div>
        </div>
      </div>

      {/* Organizations Overview */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Organizations */}
        <div className="glass-card p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-100">Organizaciones Recientes</h2>
            <a href="/organizations" className="text-sm text-primary-400 hover:text-primary-300 transition-colors">
              Ver todas →
            </a>
          </div>
          <div className="space-y-1 -mx-4">
            {recentOrgs.map((org) => (
              <OrganizationStatusCard key={org.id} org={org} />
            ))}
          </div>
        </div>

        {/* Quick Actions / Alerts */}
        <div className="glass-card p-6">
          <h2 className="text-lg font-semibold text-gray-100 mb-4">Alertas y Pendientes</h2>
          
          <div className="space-y-4">
            <div className="flex items-start gap-4 p-4 bg-amber-500/10 border border-amber-500/30 rounded-lg">
              <AlertTriangle className="w-5 h-5 text-amber-400 flex-shrink-0" />
              <div>
                <p className="text-sm font-medium text-amber-400">3 trials por expirar</p>
                <p className="text-xs text-gray-400 mt-1">Organizaciones con trial que expira en menos de 7 días</p>
              </div>
            </div>

            <div className="flex items-start gap-4 p-4 bg-red-500/10 border border-red-500/30 rounded-lg">
              <Clock className="w-5 h-5 text-red-400 flex-shrink-0" />
              <div>
                <p className="text-sm font-medium text-red-400">2 suscripciones vencidas</p>
                <p className="text-xs text-gray-400 mt-1">Requieren atención inmediata</p>
              </div>
            </div>

            <div className="flex items-start gap-4 p-4 bg-blue-500/10 border border-blue-500/30 rounded-lg">
              <Users className="w-5 h-5 text-blue-400 flex-shrink-0" />
              <div>
                <p className="text-sm font-medium text-blue-400">5 invitaciones pendientes</p>
                <p className="text-xs text-gray-400 mt-1">Usuarios que aún no han aceptado</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;
