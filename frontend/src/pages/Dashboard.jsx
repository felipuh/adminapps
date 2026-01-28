import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { dashboardService } from '../services/api'
import { 
  Building2, 
  Users, 
  Package, 
  AlertTriangle,
  TrendingUp,
  Clock,
  ArrowRight,
  RefreshCw,
  Shield,
  Activity
} from 'lucide-react'

const Dashboard = () => {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    loadDashboard()
  }, [])

  const loadDashboard = async () => {
    try {
      setLoading(true)
      const response = await dashboardService.getDashboard()
      setData(response.data)
    } catch (err) {
      setError('Error al cargar el dashboard')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="spinner w-10 h-10"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="glass-card p-6 text-center">
        <p className="text-red-400">{error}</p>
        <button onClick={loadDashboard} className="glass-button mt-4">
          Reintentar
        </button>
      </div>
    )
  }

  const orgStats = data?.organizations || {}
  const isoStats = data?.iso_modules || {}

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Dashboard</h1>
          <p className="text-gray-400">Resumen del sistema</p>
        </div>
        <button 
          onClick={loadDashboard}
          className="glass-button-secondary flex items-center gap-2"
        >
          <RefreshCw size={18} />
          Actualizar
        </button>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="stat-card">
          <div className="flex items-center justify-between">
            <Building2 className="w-8 h-8 text-primary-500" />
            <span className="badge-success">+{orgStats.new_this_month || 0} este mes</span>
          </div>
          <div className="mt-4">
            <p className="stat-value">{orgStats.total || 0}</p>
            <p className="stat-label">Organizaciones</p>
          </div>
        </div>

        <div className="stat-card">
          <div className="flex items-center justify-between">
            <Shield className="w-8 h-8 text-emerald-500" />
            <span className="badge-info">{isoStats.standards_available || 0} disponibles</span>
          </div>
          <div className="mt-4">
            <p className="stat-value">{isoStats.active_assignments || 0}</p>
            <p className="stat-label">Módulos Activos</p>
          </div>
        </div>

        <div className="stat-card">
          <div className="flex items-center justify-between">
            <Clock className="w-8 h-8 text-amber-500" />
          </div>
          <div className="mt-4">
            <p className="stat-value">{isoStats.trial_assignments || 0}</p>
            <p className="stat-label">En Periodo de Prueba</p>
          </div>
        </div>

        <div className="stat-card">
          <div className="flex items-center justify-between">
            <AlertTriangle className="w-8 h-8 text-red-500" />
          </div>
          <div className="mt-4">
            <p className="stat-value">{isoStats.expiring_soon || 0}</p>
            <p className="stat-label">Trials por Expirar</p>
          </div>
        </div>
      </div>

      {/* Organizations Status */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 glass-card p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-semibold text-white">Estado de Organizaciones</h2>
            <Link to="/organizations" className="text-primary-400 hover:text-primary-300 flex items-center gap-1 text-sm">
              Ver todas <ArrowRight size={16} />
            </Link>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center p-4 bg-dark-400/30 rounded-lg">
              <p className="text-2xl font-bold text-emerald-400">{orgStats.active || 0}</p>
              <p className="text-sm text-gray-400">Activas</p>
            </div>
            <div className="text-center p-4 bg-dark-400/30 rounded-lg">
              <p className="text-2xl font-bold text-amber-400">{orgStats.trial || 0}</p>
              <p className="text-sm text-gray-400">En Trial</p>
            </div>
            <div className="text-center p-4 bg-dark-400/30 rounded-lg">
              <p className="text-2xl font-bold text-red-400">{orgStats.suspended || 0}</p>
              <p className="text-sm text-gray-400">Suspendidas</p>
            </div>
            <div className="text-center p-4 bg-dark-400/30 rounded-lg">
              <p className="text-2xl font-bold text-gray-400">{orgStats.total || 0}</p>
              <p className="text-sm text-gray-400">Total</p>
            </div>
          </div>

          {/* Recent organizations */}
          <div className="mt-6">
            <h3 className="text-sm font-medium text-gray-400 mb-3">Organizaciones Recientes</h3>
            <div className="space-y-2">
              {data?.recent_organizations?.map((org) => (
                <Link 
                  key={org.id} 
                  to={`/organizations/${org.id}`}
                  className="flex items-center justify-between p-3 bg-dark-400/30 rounded-lg hover:bg-dark-400/50 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-primary-600/20 rounded-lg flex items-center justify-center">
                      <Building2 className="w-5 h-5 text-primary-400" />
                    </div>
                    <div>
                      <p className="text-white font-medium">{org.name}</p>
                      <p className="text-xs text-gray-500">{org.code}</p>
                    </div>
                  </div>
                  <span className={`badge-${org.status === 'active' ? 'success' : org.status === 'trial' ? 'warning' : 'danger'}`}>
                    {org.status}
                  </span>
                </Link>
              ))}
              {(!data?.recent_organizations || data.recent_organizations.length === 0) && (
                <p className="text-gray-500 text-center py-4">No hay organizaciones recientes</p>
              )}
            </div>
          </div>
        </div>

        {/* Alerts & Popular Modules */}
        <div className="space-y-6">
          {/* Alerts */}
          <div className="glass-card p-6">
            <h2 className="text-lg font-semibold text-white mb-4">Alertas</h2>
            <div className="space-y-3">
              {data?.alerts?.map((alert, index) => (
                <div 
                  key={index}
                  className={`p-3 rounded-lg border ${
                    alert.type === 'warning' 
                      ? 'bg-amber-500/10 border-amber-500/30' 
                      : 'bg-blue-500/10 border-blue-500/30'
                  }`}
                >
                  <p className={`text-sm ${alert.type === 'warning' ? 'text-amber-400' : 'text-blue-400'}`}>
                    {alert.message}
                  </p>
                  {alert.date && (
                    <p className="text-xs text-gray-500 mt-1">
                      {new Date(alert.date).toLocaleDateString('es-ES')}
                    </p>
                  )}
                </div>
              ))}
              {(!data?.alerts || data.alerts.length === 0) && (
                <p className="text-gray-500 text-center py-4">Sin alertas pendientes</p>
              )}
            </div>
          </div>

          {/* Popular Modules */}
          <div className="glass-card p-6">
            <h2 className="text-lg font-semibold text-white mb-4">Módulos Populares</h2>
            <div className="space-y-3">
              {data?.popular_modules?.map((module, index) => (
                <div key={index} className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 bg-primary-600/20 rounded-lg flex items-center justify-center">
                      <Package className="w-4 h-4 text-primary-400" />
                    </div>
                    <span className="text-gray-300">{module.iso_standard__code}</span>
                  </div>
                  <span className="text-white font-medium">{module.count}</span>
                </div>
              ))}
              {(!data?.popular_modules || data.popular_modules.length === 0) && (
                <p className="text-gray-500 text-center py-4">Sin datos disponibles</p>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="glass-card p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-semibold text-white">Actividad Reciente</h2>
          <Link to="/activity" className="text-primary-400 hover:text-primary-300 flex items-center gap-1 text-sm">
            Ver todo <ArrowRight size={16} />
          </Link>
        </div>

        <div className="space-y-4">
          {data?.recent_activity?.map((activity) => (
            <div key={activity.id} className="flex items-start gap-4 p-3 bg-dark-400/30 rounded-lg">
              <div className="w-10 h-10 bg-dark-300 rounded-full flex items-center justify-center flex-shrink-0">
                <Activity className="w-5 h-5 text-gray-400" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-white">
                  <span className="font-medium">{activity.user}</span>
                  <span className="text-gray-400"> - {activity.action}</span>
                </p>
                {activity.organization && (
                  <p className="text-sm text-gray-500">{activity.organization}</p>
                )}
              </div>
              <span className="text-xs text-gray-500 whitespace-nowrap">
                {new Date(activity.created_at).toLocaleString('es-ES')}
              </span>
            </div>
          ))}
          {(!data?.recent_activity || data.recent_activity.length === 0) && (
            <p className="text-gray-500 text-center py-4">No hay actividad reciente</p>
          )}
        </div>
      </div>
    </div>
  )
}

export default Dashboard
