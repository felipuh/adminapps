import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { organizationService, moduleService, isoStandardService } from '../services/api'
import { 
  Building2, 
  ArrowLeft,
  Mail,
  Phone,
  Globe,
  MapPin,
  Users,
  Package,
  Calendar,
  Power,
  Ban,
  Plus,
  Check,
  X
} from 'lucide-react'

const OrganizationDetail = () => {
  const { id } = useParams()
  const [organization, setOrganization] = useState(null)
  const [modules, setModules] = useState([])
  const [availableISOs, setAvailableISOs] = useState([])
  const [loading, setLoading] = useState(true)
  const [showAssignModal, setShowAssignModal] = useState(false)
  const [selectedISOs, setSelectedISOs] = useState([])

  useEffect(() => {
    loadData()
  }, [id])

  const loadData = async () => {
    try {
      setLoading(true)
      const [orgRes, modulesRes, isosRes] = await Promise.all([
        organizationService.getById(id),
        moduleService.getByOrganization(id),
        isoStandardService.getActive()
      ])
      setOrganization(orgRes.data)
      setModules(modulesRes.data.modules || [])
      setAvailableISOs(isosRes.data)
    } catch (err) {
      console.error('Error cargando datos:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleToggleModule = async (moduleId, currentStatus) => {
    const action = currentStatus === 'active' ? 'disable' : 'enable'
    try {
      await moduleService.toggle(moduleId, action)
      loadData()
    } catch (err) {
      console.error('Error cambiando estado:', err)
    }
  }

  const handleAssignModules = async () => {
    if (selectedISOs.length === 0) return
    try {
      await moduleService.bulkAssign({
        organization_id: id,
        iso_standards: selectedISOs,
        status: 'trial'
      })
      setShowAssignModal(false)
      setSelectedISOs([])
      loadData()
    } catch (err) {
      console.error('Error asignando módulos:', err)
    }
  }

  const getStatusBadge = (status) => {
    const badges = {
      active: 'badge-success',
      trial: 'badge-warning',
      suspended: 'badge-danger',
      expired: 'badge-gray'
    }
    return badges[status] || 'badge-gray'
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="spinner w-10 h-10"></div>
      </div>
    )
  }

  if (!organization) {
    return (
      <div className="glass-card p-6 text-center">
        <p className="text-red-400">Organización no encontrada</p>
        <Link to="/organizations" className="glass-button mt-4 inline-block">
          Volver
        </Link>
      </div>
    )
  }

  const assignedISOIds = modules.map(m => m.iso_standard)
  const unassignedISOs = availableISOs.filter(iso => !assignedISOIds.includes(iso.id))

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link to="/organizations" className="p-2 hover:bg-dark-400/50 rounded-lg transition-colors">
          <ArrowLeft className="w-5 h-5 text-gray-400" />
        </Link>
        <div className="flex-1">
          <h1 className="text-2xl font-bold text-white">{organization.name}</h1>
          <p className="text-gray-400">{organization.code}</p>
        </div>
        <span className={getStatusBadge(organization.status)}>
          {organization.status}
        </span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Info Principal */}
        <div className="lg:col-span-2 space-y-6">
          {/* Datos de la organización */}
          <div className="glass-card p-6">
            <h2 className="text-lg font-semibold text-white mb-4">Información General</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {organization.email && (
                <div className="flex items-center gap-3">
                  <Mail className="w-5 h-5 text-gray-500" />
                  <div>
                    <p className="text-xs text-gray-500">Email</p>
                    <p className="text-white">{organization.email}</p>
                  </div>
                </div>
              )}
              {organization.phone && (
                <div className="flex items-center gap-3">
                  <Phone className="w-5 h-5 text-gray-500" />
                  <div>
                    <p className="text-xs text-gray-500">Teléfono</p>
                    <p className="text-white">{organization.phone}</p>
                  </div>
                </div>
              )}
              {organization.website && (
                <div className="flex items-center gap-3">
                  <Globe className="w-5 h-5 text-gray-500" />
                  <div>
                    <p className="text-xs text-gray-500">Sitio Web</p>
                    <a href={organization.website} target="_blank" rel="noreferrer" className="text-primary-400 hover:underline">
                      {organization.website}
                    </a>
                  </div>
                </div>
              )}
              {organization.city && (
                <div className="flex items-center gap-3">
                  <MapPin className="w-5 h-5 text-gray-500" />
                  <div>
                    <p className="text-xs text-gray-500">Ubicación</p>
                    <p className="text-white">{organization.city}, {organization.country}</p>
                  </div>
                </div>
              )}
              <div className="flex items-center gap-3">
                <Users className="w-5 h-5 text-gray-500" />
                <div>
                  <p className="text-xs text-gray-500">Tamaño</p>
                  <p className="text-white capitalize">{organization.size || '-'}</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <Calendar className="w-5 h-5 text-gray-500" />
                <div>
                  <p className="text-xs text-gray-500">Creación</p>
                  <p className="text-white">{new Date(organization.created_at).toLocaleDateString('es-ES')}</p>
                </div>
              </div>
            </div>
          </div>

          {/* Módulos ISO */}
          <div className="glass-card p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-white">Módulos ISO Asignados</h2>
              <button 
                onClick={() => setShowAssignModal(true)}
                className="glass-button-secondary flex items-center gap-2 text-sm"
                disabled={unassignedISOs.length === 0}
              >
                <Plus size={16} />
                Asignar Módulo
              </button>
            </div>

            <div className="space-y-3">
              {modules.map((module) => (
                <div 
                  key={module.id}
                  className="flex items-center justify-between p-4 bg-dark-400/30 rounded-lg"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-primary-600/20 rounded-lg flex items-center justify-center">
                      <Package className="w-5 h-5 text-primary-400" />
                    </div>
                    <div>
                      <p className="font-medium text-white">{module.iso_code}</p>
                      <p className="text-sm text-gray-500">{module.iso_name}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className={getStatusBadge(module.status)}>
                      {module.status}
                    </span>
                    <button
                      onClick={() => handleToggleModule(module.id, module.status)}
                      className={`p-2 rounded-lg transition-colors ${
                        module.is_enabled 
                          ? 'bg-emerald-500/20 text-emerald-400 hover:bg-emerald-500/30' 
                          : 'bg-gray-500/20 text-gray-400 hover:bg-gray-500/30'
                      }`}
                      title={module.is_enabled ? 'Desactivar' : 'Activar'}
                    >
                      <Power size={18} />
                    </button>
                  </div>
                </div>
              ))}

              {modules.length === 0 && (
                <div className="text-center py-8">
                  <Package className="w-12 h-12 text-gray-600 mx-auto mb-3" />
                  <p className="text-gray-400">No hay módulos asignados</p>
                  <button 
                    onClick={() => setShowAssignModal(true)}
                    className="glass-button mt-4"
                  >
                    Asignar Primer Módulo
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Quick Stats */}
          <div className="glass-card p-6">
            <h2 className="text-lg font-semibold text-white mb-4">Resumen</h2>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-gray-400">Módulos activos</span>
                <span className="text-white font-medium">
                  {modules.filter(m => m.is_enabled).length}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-400">En trial</span>
                <span className="text-amber-400 font-medium">
                  {modules.filter(m => m.status === 'trial').length}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-400">Industria</span>
                <span className="text-white capitalize">{organization.industry || '-'}</span>
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="glass-card p-6">
            <h2 className="text-lg font-semibold text-white mb-4">Acciones</h2>
            <div className="space-y-2">
              {organization.status !== 'active' ? (
                <button className="w-full glass-button-success flex items-center justify-center gap-2">
                  <Power size={18} />
                  Activar Organización
                </button>
              ) : (
                <button className="w-full glass-button-danger flex items-center justify-center gap-2">
                  <Ban size={18} />
                  Suspender Organización
                </button>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Modal Asignar Módulo */}
      {showAssignModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
          <div className="glass-card p-6 w-full max-w-md mx-4 animate-fadeIn">
            <h2 className="text-xl font-semibold text-white mb-4">Asignar Módulos ISO</h2>
            
            <div className="space-y-2 max-h-64 overflow-y-auto mb-4">
              {unassignedISOs.map((iso) => (
                <label 
                  key={iso.id}
                  className="flex items-center gap-3 p-3 bg-dark-400/30 rounded-lg cursor-pointer hover:bg-dark-400/50 transition-colors"
                >
                  <input
                    type="checkbox"
                    checked={selectedISOs.includes(iso.id)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedISOs([...selectedISOs, iso.id])
                      } else {
                        setSelectedISOs(selectedISOs.filter(id => id !== iso.id))
                      }
                    }}
                    className="w-4 h-4 rounded border-gray-600 bg-dark-400 text-primary-500 focus:ring-primary-500"
                  />
                  <div className="flex-1">
                    <p className="text-white">{iso.code}</p>
                    <p className="text-sm text-gray-500">{iso.name}</p>
                  </div>
                </label>
              ))}
              {unassignedISOs.length === 0 && (
                <p className="text-gray-400 text-center py-4">
                  Todos los módulos ya están asignados
                </p>
              )}
            </div>

            <div className="flex gap-3">
              <button
                onClick={() => {
                  setShowAssignModal(false)
                  setSelectedISOs([])
                }}
                className="flex-1 glass-button-secondary"
              >
                Cancelar
              </button>
              <button
                onClick={handleAssignModules}
                disabled={selectedISOs.length === 0}
                className="flex-1 glass-button"
              >
                Asignar ({selectedISOs.length})
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default OrganizationDetail
