import { useState, useEffect } from 'react'
import { activityService } from '../services/api'
import { 
  Activity, 
  Search, 
  Filter,
  Power,
  PowerOff,
  Clock,
  RefreshCw,
  Calendar
} from 'lucide-react'

const ActivityLogs = () => {
  const [logs, setLogs] = useState([])
  const [loading, setLoading] = useState(true)
  const [actionFilter, setActionFilter] = useState('')

  useEffect(() => {
    loadLogs()
  }, [actionFilter])

  const loadLogs = async () => {
    try {
      setLoading(true)
      const params = {}
      if (actionFilter) params.action = actionFilter
      const response = await activityService.getLogs(params)
      setLogs(response.data.results || response.data)
    } catch (err) {
      console.error('Error cargando logs:', err)
    } finally {
      setLoading(false)
    }
  }

  const getActionIcon = (action) => {
    const icons = {
      enabled: <Power className="w-4 h-4 text-emerald-400" />,
      disabled: <PowerOff className="w-4 h-4 text-red-400" />,
      trial_started: <Clock className="w-4 h-4 text-amber-400" />,
      trial_ended: <Clock className="w-4 h-4 text-gray-400" />,
      expired: <Calendar className="w-4 h-4 text-red-400" />,
      renewed: <RefreshCw className="w-4 h-4 text-emerald-400" />
    }
    return icons[action] || <Activity className="w-4 h-4 text-gray-400" />
  }

  const getActionLabel = (action) => {
    const labels = {
      enabled: 'Habilitado',
      disabled: 'Deshabilitado',
      trial_started: 'Prueba Iniciada',
      trial_ended: 'Prueba Terminada',
      expired: 'Expirado',
      renewed: 'Renovado'
    }
    return labels[action] || action
  }

  const getActionBadge = (action) => {
    const badges = {
      enabled: 'badge-success',
      disabled: 'badge-danger',
      trial_started: 'badge-warning',
      trial_ended: 'badge-gray',
      expired: 'badge-danger',
      renewed: 'badge-success'
    }
    return badges[action] || 'badge-gray'
  }

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">Registro de Actividad</h1>
          <p className="text-gray-400">Historial de cambios en módulos ISO</p>
        </div>
        <button 
          onClick={loadLogs}
          className="glass-button-secondary flex items-center gap-2"
        >
          <RefreshCw size={18} />
          Actualizar
        </button>
      </div>

      {/* Filters */}
      <div className="glass-card p-4">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex items-center gap-2">
            <Filter className="w-5 h-5 text-gray-500" />
            <select
              value={actionFilter}
              onChange={(e) => setActionFilter(e.target.value)}
              className="glass-input w-auto"
            >
              <option value="">Todas las acciones</option>
              <option value="enabled">Habilitado</option>
              <option value="disabled">Deshabilitado</option>
              <option value="trial_started">Prueba Iniciada</option>
              <option value="trial_ended">Prueba Terminada</option>
              <option value="expired">Expirado</option>
              <option value="renewed">Renovado</option>
            </select>
          </div>
        </div>
      </div>

      {/* Activity List */}
      <div className="glass-card">
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="spinner w-10 h-10"></div>
          </div>
        ) : (
          <div className="divide-y divide-gray-700/30">
            {logs.map((log) => (
              <div key={log.id} className="p-4 hover:bg-dark-400/30 transition-colors">
                <div className="flex items-start gap-4">
                  <div className="w-10 h-10 bg-dark-400/50 rounded-full flex items-center justify-center flex-shrink-0">
                    {getActionIcon(log.action)}
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className={getActionBadge(log.action)}>
                        {getActionLabel(log.action)}
                      </span>
                      <span className="text-white font-medium">
                        {log.iso_code}
                      </span>
                      <span className="text-gray-500">para</span>
                      <span className="text-primary-400">
                        {log.organization_name}
                      </span>
                    </div>
                    
                    {log.notes && (
                      <p className="text-sm text-gray-400 mt-1">{log.notes}</p>
                    )}
                    
                    <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                      <span>Por: {log.performed_by_name || 'Sistema'}</span>
                      <span>•</span>
                      <span>{new Date(log.created_at).toLocaleString('es-ES')}</span>
                    </div>
                  </div>
                </div>
              </div>
            ))}

            {logs.length === 0 && (
              <div className="text-center py-12">
                <Activity className="w-12 h-12 text-gray-600 mx-auto mb-4" />
                <p className="text-gray-400">No hay registros de actividad</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default ActivityLogs
