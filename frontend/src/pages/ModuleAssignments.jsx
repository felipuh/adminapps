import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { moduleService } from '../services/api'
import { 
  Package, 
  Search, 
  Filter,
  Power,
  Building2,
  Shield,
  Clock,
  AlertTriangle
} from 'lucide-react'

const ModuleAssignments = () => {
  const [modules, setModules] = useState([])
  const [loading, setLoading] = useState(true)
  const [statusFilter, setStatusFilter] = useState('')
  const [search, setSearch] = useState('')

  useEffect(() => {
    loadModules()
  }, [statusFilter])

  const loadModules = async () => {
    try {
      setLoading(true)
      const params = {}
      if (statusFilter) params.status = statusFilter
      const response = await moduleService.getAll(params)
      setModules(response.data.results || response.data)
    } catch (err) {
      console.error('Error cargando módulos:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleToggle = async (id, currentEnabled) => {
    const action = currentEnabled ? 'disable' : 'enable'
    try {
      await moduleService.toggle(id, action)
      loadModules()
    } catch (err) {
      console.error('Error cambiando estado:', err)
    }
  }

  const getStatusBadge = (status, isEnabled) => {
    if (!isEnabled) return 'badge-gray'
    const badges = {
      active: 'badge-success',
      trial: 'badge-warning',
      suspended: 'badge-danger',
      expired: 'badge-gray'
    }
    return badges[status] || 'badge-gray'
  }

  const filteredModules = modules.filter(m => {
    if (!search) return true
    const searchLower = search.toLowerCase()
    return (
      m.organization_name?.toLowerCase().includes(searchLower) ||
      m.iso_code?.toLowerCase().includes(searchLower)
    )
  })

  // Stats
  const stats = {
    total: modules.length,
    active: modules.filter(m => m.is_enabled && m.status === 'active').length,
    trial: modules.filter(m => m.status === 'trial').length,
    expiring: modules.filter(m => {
      if (!m.expires_at) return false
      const daysLeft = Math.ceil((new Date(m.expires_at) - new Date()) / (1000 * 60 * 60 * 24))
      return daysLeft <= 7 && daysLeft > 0
    }).length
  }

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white">Módulos Asignados</h1>
        <p className="text-gray-400">Control de módulos ISO por organización</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="stat-card">
          <div className="flex items-center gap-3">
            <Package className="w-8 h-8 text-primary-500" />
            <div>
              <p className="stat-value text-2xl">{stats.total}</p>
              <p className="stat-label">Total</p>
            </div>
          </div>
        </div>
        <div className="stat-card">
          <div className="flex items-center gap-3">
            <Power className="w-8 h-8 text-emerald-500" />
            <div>
              <p className="stat-value text-2xl">{stats.active}</p>
              <p className="stat-label">Activos</p>
            </div>
          </div>
        </div>
        <div className="stat-card">
          <div className="flex items-center gap-3">
            <Clock className="w-8 h-8 text-amber-500" />
            <div>
              <p className="stat-value text-2xl">{stats.trial}</p>
              <p className="stat-label">En Trial</p>
            </div>
          </div>
        </div>
        <div className="stat-card">
          <div className="flex items-center gap-3">
            <AlertTriangle className="w-8 h-8 text-red-500" />
            <div>
              <p className="stat-value text-2xl">{stats.expiring}</p>
              <p className="stat-label">Por Expirar</p>
            </div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="glass-card p-4">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Buscar por organización o ISO..."
              className="glass-input pl-10"
            />
          </div>
          <div className="flex items-center gap-2">
            <Filter className="w-5 h-5 text-gray-500" />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="glass-input w-auto"
            >
              <option value="">Todos los estados</option>
              <option value="active">Activos</option>
              <option value="trial">En Trial</option>
              <option value="suspended">Suspendidos</option>
              <option value="expired">Expirados</option>
            </select>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="glass-card overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="spinner w-10 h-10"></div>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-dark-400/50">
                <tr>
                  <th className="table-header">Organización</th>
                  <th className="table-header">Módulo ISO</th>
                  <th className="table-header">Estado</th>
                  <th className="table-header">Activado</th>
                  <th className="table-header">Expira</th>
                  <th className="table-header text-center">Habilitado</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-700/30">
                {filteredModules.map((module) => {
                  const daysLeft = module.expires_at 
                    ? Math.ceil((new Date(module.expires_at) - new Date()) / (1000 * 60 * 60 * 24))
                    : null

                  return (
                    <tr key={module.id} className="hover:bg-dark-400/30 transition-colors">
                      <td className="table-cell">
                        <Link 
                          to={`/organizations/${module.organization}`}
                          className="flex items-center gap-3 hover:text-primary-400 transition-colors"
                        >
                          <div className="w-10 h-10 bg-primary-600/20 rounded-lg flex items-center justify-center">
                            <Building2 className="w-5 h-5 text-primary-400" />
                          </div>
                          <div>
                            <p className="font-medium text-white">{module.organization_name}</p>
                            <p className="text-xs text-gray-500">{module.organization_code}</p>
                          </div>
                        </Link>
                      </td>
                      <td className="table-cell">
                        <div className="flex items-center gap-2">
                          <Shield className="w-5 h-5 text-primary-400" />
                          <div>
                            <p className="text-white">{module.iso_code}</p>
                            <p className="text-xs text-gray-500">{module.iso_name}</p>
                          </div>
                        </div>
                      </td>
                      <td className="table-cell">
                        <span className={getStatusBadge(module.status, module.is_enabled)}>
                          {module.is_enabled ? module.status : 'deshabilitado'}
                        </span>
                      </td>
                      <td className="table-cell">
                        {new Date(module.activated_at).toLocaleDateString('es-ES')}
                      </td>
                      <td className="table-cell">
                        {module.expires_at ? (
                          <div>
                            <p className={daysLeft <= 7 ? 'text-red-400' : 'text-gray-300'}>
                              {new Date(module.expires_at).toLocaleDateString('es-ES')}
                            </p>
                            {daysLeft !== null && daysLeft <= 7 && (
                              <p className="text-xs text-red-400">
                                {daysLeft <= 0 ? 'Expirado' : `${daysLeft} días restantes`}
                              </p>
                            )}
                          </div>
                        ) : (
                          <span className="text-gray-500">-</span>
                        )}
                      </td>
                      <td className="table-cell text-center">
                        <button
                          onClick={() => handleToggle(module.id, module.is_enabled)}
                          className={`p-2 rounded-lg transition-colors ${
                            module.is_enabled 
                              ? 'bg-emerald-500/20 text-emerald-400 hover:bg-emerald-500/30' 
                              : 'bg-gray-500/20 text-gray-400 hover:bg-gray-500/30'
                          }`}
                          title={module.is_enabled ? 'Desactivar' : 'Activar'}
                        >
                          <Power size={18} />
                        </button>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>

            {filteredModules.length === 0 && (
              <div className="text-center py-12">
                <Package className="w-12 h-12 text-gray-600 mx-auto mb-4" />
                <p className="text-gray-400">No se encontraron módulos asignados</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default ModuleAssignments
