import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { organizationService } from '../services/api'
import { 
  Building2, 
  Plus, 
  Search, 
  Filter,
  MoreVertical,
  Eye,
  Edit,
  Power,
  Ban,
  ChevronLeft,
  ChevronRight
} from 'lucide-react'

const Organizations = () => {
  const [organizations, setOrganizations] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [menuOpen, setMenuOpen] = useState(null)

  useEffect(() => {
    loadOrganizations()
  }, [statusFilter])

  const loadOrganizations = async () => {
    try {
      setLoading(true)
      const params = {}
      if (statusFilter) params.status = statusFilter
      if (search) params.search = search
      const response = await organizationService.getAll(params)
      setOrganizations(response.data.results || response.data)
    } catch (err) {
      console.error('Error cargando organizaciones:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = (e) => {
    e.preventDefault()
    loadOrganizations()
  }

  const handleActivate = async (id) => {
    try {
      await organizationService.activate(id)
      loadOrganizations()
    } catch (err) {
      console.error('Error activando organización:', err)
    }
    setMenuOpen(null)
  }

  const handleSuspend = async (id) => {
    try {
      await organizationService.suspend(id)
      loadOrganizations()
    } catch (err) {
      console.error('Error suspendiendo organización:', err)
    }
    setMenuOpen(null)
  }

  const getStatusBadge = (status) => {
    const badges = {
      active: 'badge-success',
      trial: 'badge-warning',
      suspended: 'badge-danger',
      inactive: 'badge-gray'
    }
    return badges[status] || 'badge-gray'
  }

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">Organizaciones</h1>
          <p className="text-gray-400">Gestiona los clientes de ISO Smart</p>
        </div>
        <Link to="/organizations/new" className="glass-button flex items-center gap-2">
          <Plus size={18} />
          Nueva Organización
        </Link>
      </div>

      {/* Filters */}
      <div className="glass-card p-4">
        <div className="flex flex-col sm:flex-row gap-4">
          <form onSubmit={handleSearch} className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Buscar por nombre, código o email..."
                className="glass-input pl-10"
              />
            </div>
          </form>
          <div className="flex items-center gap-2">
            <Filter className="w-5 h-5 text-gray-500" />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="glass-input w-auto"
            >
              <option value="">Todos los estados</option>
              <option value="active">Activas</option>
              <option value="trial">En Trial</option>
              <option value="suspended">Suspendidas</option>
              <option value="inactive">Inactivas</option>
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
                  <th className="table-header">Industria</th>
                  <th className="table-header">Tamaño</th>
                  <th className="table-header">Estado</th>
                  <th className="table-header">Creación</th>
                  <th className="table-header text-right">Acciones</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-700/30">
                {organizations.map((org) => (
                  <tr key={org.id} className="hover:bg-dark-400/30 transition-colors">
                    <td className="table-cell">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-primary-600/20 rounded-lg flex items-center justify-center">
                          <Building2 className="w-5 h-5 text-primary-400" />
                        </div>
                        <div>
                          <p className="font-medium text-white">{org.name}</p>
                          <p className="text-xs text-gray-500">{org.code}</p>
                        </div>
                      </div>
                    </td>
                    <td className="table-cell">
                      <span className="capitalize">{org.industry || '-'}</span>
                    </td>
                    <td className="table-cell">
                      <span className="capitalize">{org.size || '-'}</span>
                    </td>
                    <td className="table-cell">
                      <span className={getStatusBadge(org.status)}>
                        {org.status}
                      </span>
                    </td>
                    <td className="table-cell">
                      {new Date(org.created_at).toLocaleDateString('es-ES')}
                    </td>
                    <td className="table-cell text-right">
                      <div className="relative inline-block">
                        <button
                          onClick={() => setMenuOpen(menuOpen === org.id ? null : org.id)}
                          className="p-2 hover:bg-dark-400/50 rounded-lg transition-colors"
                        >
                          <MoreVertical className="w-5 h-5 text-gray-400" />
                        </button>
                        
                        {menuOpen === org.id && (
                          <div className="absolute right-0 mt-2 w-48 glass-card p-2 z-10 animate-fadeIn">
                            <Link
                              to={`/organizations/${org.id}`}
                              className="flex items-center gap-2 px-3 py-2 text-sm text-gray-300 hover:bg-dark-400/50 rounded-lg transition-colors"
                            >
                              <Eye size={16} />
                              Ver detalles
                            </Link>
                            <Link
                              to={`/organizations/${org.id}/edit`}
                              className="flex items-center gap-2 px-3 py-2 text-sm text-gray-300 hover:bg-dark-400/50 rounded-lg transition-colors"
                            >
                              <Edit size={16} />
                              Editar
                            </Link>
                            {org.status !== 'active' ? (
                              <button
                                onClick={() => handleActivate(org.id)}
                                className="w-full flex items-center gap-2 px-3 py-2 text-sm text-emerald-400 hover:bg-emerald-500/10 rounded-lg transition-colors"
                              >
                                <Power size={16} />
                                Activar
                              </button>
                            ) : (
                              <button
                                onClick={() => handleSuspend(org.id)}
                                className="w-full flex items-center gap-2 px-3 py-2 text-sm text-red-400 hover:bg-red-500/10 rounded-lg transition-colors"
                              >
                                <Ban size={16} />
                                Suspender
                              </button>
                            )}
                          </div>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {organizations.length === 0 && (
              <div className="text-center py-12">
                <Building2 className="w-12 h-12 text-gray-600 mx-auto mb-4" />
                <p className="text-gray-400">No se encontraron organizaciones</p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Pagination placeholder */}
      <div className="flex items-center justify-between">
        <p className="text-sm text-gray-500">
          Mostrando {organizations.length} organizaciones
        </p>
        <div className="flex items-center gap-2">
          <button className="glass-button-secondary p-2" disabled>
            <ChevronLeft size={18} />
          </button>
          <button className="glass-button-secondary p-2" disabled>
            <ChevronRight size={18} />
          </button>
        </div>
      </div>
    </div>
  )
}

export default Organizations
