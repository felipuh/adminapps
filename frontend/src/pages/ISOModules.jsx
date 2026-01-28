import { useState, useEffect } from 'react'
import { isoStandardService } from '../services/api'
import { 
  Shield, 
  Plus, 
  Edit,
  Package,
  DollarSign,
  Check,
  Clock
} from 'lucide-react'

const ISOModules = () => {
  const [standards, setStandards] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadStandards()
  }, [])

  const loadStandards = async () => {
    try {
      setLoading(true)
      const response = await isoStandardService.getAll()
      setStandards(response.data.results || response.data)
    } catch (err) {
      console.error('Error cargando estándares:', err)
    } finally {
      setLoading(false)
    }
  }

  const getStatusBadge = (status) => {
    const styles = {
      active: { class: 'badge-success', label: 'Activo' },
      beta: { class: 'badge-info', label: 'Beta' },
      development: { class: 'badge-warning', label: 'En Desarrollo' },
      deprecated: { class: 'badge-gray', label: 'Descontinuado' }
    }
    return styles[status] || styles.development
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="spinner w-10 h-10"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">Estándares ISO</h1>
          <p className="text-gray-400">Catálogo de módulos disponibles</p>
        </div>
        <button className="glass-button flex items-center gap-2">
          <Plus size={18} />
          Nuevo Estándar
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="stat-card">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-emerald-500/20 rounded-lg flex items-center justify-center">
              <Check className="w-5 h-5 text-emerald-400" />
            </div>
            <div>
              <p className="stat-value text-2xl">{standards.filter(s => s.status === 'active').length}</p>
              <p className="stat-label">Activos</p>
            </div>
          </div>
        </div>
        <div className="stat-card">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-amber-500/20 rounded-lg flex items-center justify-center">
              <Clock className="w-5 h-5 text-amber-400" />
            </div>
            <div>
              <p className="stat-value text-2xl">{standards.filter(s => s.status === 'development').length}</p>
              <p className="stat-label">En Desarrollo</p>
            </div>
          </div>
        </div>
        <div className="stat-card">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-primary-500/20 rounded-lg flex items-center justify-center">
              <Package className="w-5 h-5 text-primary-400" />
            </div>
            <div>
              <p className="stat-value text-2xl">{standards.length}</p>
              <p className="stat-label">Total</p>
            </div>
          </div>
        </div>
      </div>

      {/* Grid de estándares */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {standards.map((standard) => {
          const statusInfo = getStatusBadge(standard.status)
          return (
            <div key={standard.id} className="glass-card-hover p-6">
              <div className="flex items-start justify-between mb-4">
                <div 
                  className="w-12 h-12 rounded-xl flex items-center justify-center"
                  style={{ backgroundColor: `${standard.color}20` }}
                >
                  <Shield className="w-6 h-6" style={{ color: standard.color }} />
                </div>
                <span className={statusInfo.class}>{statusInfo.label}</span>
              </div>

              <h3 className="text-lg font-semibold text-white mb-1">{standard.code}</h3>
              <p className="text-gray-400 mb-2">{standard.name}</p>
              <p className="text-sm text-gray-500 mb-4 line-clamp-2">{standard.description}</p>

              <div className="border-t border-gray-700/30 pt-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-gray-500">Versión</span>
                  <span className="text-white">{standard.version}</span>
                </div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-gray-500">Precio Mensual</span>
                  <span className="text-white flex items-center gap-1">
                    <DollarSign size={14} />
                    {parseFloat(standard.monthly_price).toFixed(2)} MXN
                  </span>
                </div>
                {standard.is_base && (
                  <div className="mt-3">
                    <span className="badge-info">Módulo Base</span>
                  </div>
                )}
              </div>

              <div className="mt-4 flex gap-2">
                <button className="flex-1 glass-button-secondary text-sm py-2">
                  <Edit size={16} className="inline mr-1" />
                  Editar
                </button>
              </div>
            </div>
          )
        })}

        {standards.length === 0 && (
          <div className="col-span-full text-center py-12 glass-card">
            <Shield className="w-12 h-12 text-gray-600 mx-auto mb-4" />
            <p className="text-gray-400">No hay estándares ISO configurados</p>
            <button className="glass-button mt-4">
              Crear Primer Estándar
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

export default ISOModules
