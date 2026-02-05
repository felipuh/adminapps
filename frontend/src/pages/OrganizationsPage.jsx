import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Building2, 
  Plus, 
  Search, 
  Filter,
  MoreVertical,
  Eye,
  Edit,
  Trash2,
  Users,
  Mail,
  Globe,
  X
} from 'lucide-react';
import { organizationService } from '../services/api';
import toast from 'react-hot-toast';

// Organization Row Component
const OrganizationRow = ({ org, onView, onEdit, onDelete }) => {
  const [menuOpen, setMenuOpen] = useState(false);

  const statusColors = {
    active: 'badge-success',
    trial: 'badge-info',
    suspended: 'badge-danger',
    inactive: 'badge-neutral',
  };

  const statusLabels = {
    active: 'Activa',
    trial: 'Trial',
    suspended: 'Suspendida',
    inactive: 'Inactiva',
  };

  return (
    <tr className="border-b border-gray-700/30 hover:bg-dark-300/30 transition-colors">
      <td className="px-4 py-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-primary-500/20 to-primary-600/20 flex items-center justify-center flex-shrink-0">
            <Building2 className="w-5 h-5 text-primary-400" />
          </div>
          <div>
            <p className="font-medium text-gray-200">{org.name}</p>
            <p className="text-xs text-gray-500">{org.code}</p>
          </div>
        </div>
      </td>
      <td className="px-4 py-4 text-sm text-gray-400">{org.email}</td>
      <td className="px-4 py-4 text-sm text-gray-400 capitalize">{org.industry}</td>
      <td className="px-4 py-4">
        <div className="flex items-center gap-2 text-sm text-gray-400">
          <Users className="w-4 h-4" />
          <span>{org.users_count || 0} / {org.max_users}</span>
        </div>
      </td>
      <td className="px-4 py-4">
        <span className={statusColors[org.status]}>
          {statusLabels[org.status]}
        </span>
      </td>
      <td className="px-4 py-4">
        <div className="relative">
          <button
            onClick={() => setMenuOpen(!menuOpen)}
            className="p-2 rounded-lg hover:bg-dark-200 text-gray-400 hover:text-gray-200 transition-colors"
          >
            <MoreVertical className="w-4 h-4" />
          </button>
          
          {menuOpen && (
            <>
              <div className="fixed inset-0 z-10" onClick={() => setMenuOpen(false)} />
              <div className="absolute right-0 mt-2 w-48 bg-dark-200 border border-gray-700/50 rounded-xl shadow-xl z-20 overflow-hidden">
                <button
                  onClick={() => { onView(org); setMenuOpen(false); }}
                  className="w-full flex items-center gap-3 px-4 py-3 text-sm text-gray-300 hover:bg-dark-300 transition-colors"
                >
                  <Eye className="w-4 h-4" />
                  Ver detalles
                </button>
                <button
                  onClick={() => { onEdit(org); setMenuOpen(false); }}
                  className="w-full flex items-center gap-3 px-4 py-3 text-sm text-gray-300 hover:bg-dark-300 transition-colors"
                >
                  <Edit className="w-4 h-4" />
                  Editar
                </button>
                <button
                  onClick={() => { onDelete(org); setMenuOpen(false); }}
                  className="w-full flex items-center gap-3 px-4 py-3 text-sm text-red-400 hover:bg-red-500/10 transition-colors"
                >
                  <Trash2 className="w-4 h-4" />
                  Eliminar
                </button>
              </div>
            </>
          )}
        </div>
      </td>
    </tr>
  );
};

// Create/Edit Organization Modal
const OrganizationModal = ({ isOpen, onClose, organization, onSave }) => {
  const [formData, setFormData] = useState({
    name: '',
    legal_name: '',
    email: '',
    phone: '',
    website: '',
    industry: 'services',
    size: 'small',
    address: '',
    city: '',
    country: 'México',
  });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (organization) {
      setFormData({
        name: organization.name || '',
        legal_name: organization.legal_name || '',
        email: organization.email || '',
        phone: organization.phone || '',
        website: organization.website || '',
        industry: organization.industry || 'services',
        size: organization.size || 'small',
        address: organization.address || '',
        city: organization.city || '',
        country: organization.country || 'México',
      });
    } else {
      setFormData({
        name: '',
        legal_name: '',
        email: '',
        phone: '',
        website: '',
        industry: 'services',
        size: 'small',
        address: '',
        city: '',
        country: 'México',
      });
    }
  }, [organization]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      if (organization) {
        await organizationService.update(organization.id, formData);
        toast.success('Organización actualizada correctamente');
      } else {
        await organizationService.create(formData);
        toast.success('Organización creada correctamente');
      }
      onSave();
      onClose();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al guardar la organización');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content max-w-2xl" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold text-gray-100">
            {organization ? 'Editar Organización' : 'Nueva Organización'}
          </h2>
          <button onClick={onClose} className="p-2 rounded-lg hover:bg-dark-300 text-gray-400">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">
                Nombre de la Organización *
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="input-glass"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">
                Razón Social
              </label>
              <input
                type="text"
                value={formData.legal_name}
                onChange={(e) => setFormData({ ...formData, legal_name: e.target.value })}
                className="input-glass"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">
                Email *
              </label>
              <input
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                className="input-glass"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">
                Teléfono
              </label>
              <input
                type="tel"
                value={formData.phone}
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                className="input-glass"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">
              Sitio Web
            </label>
            <input
              type="url"
              value={formData.website}
              onChange={(e) => setFormData({ ...formData, website: e.target.value })}
              className="input-glass"
              placeholder="https://"
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">
                Industria
              </label>
              <select
                value={formData.industry}
                onChange={(e) => setFormData({ ...formData, industry: e.target.value })}
                className="input-glass"
              >
                <option value="manufacturing">Manufactura</option>
                <option value="technology">Tecnología</option>
                <option value="healthcare">Salud</option>
                <option value="finance">Finanzas</option>
                <option value="education">Educación</option>
                <option value="construction">Construcción</option>
                <option value="retail">Comercio</option>
                <option value="services">Servicios</option>
                <option value="government">Gobierno</option>
                <option value="other">Otro</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">
                Tamaño
              </label>
              <select
                value={formData.size}
                onChange={(e) => setFormData({ ...formData, size: e.target.value })}
                className="input-glass"
              >
                <option value="micro">Micro (1-10)</option>
                <option value="small">Pequeña (11-50)</option>
                <option value="medium">Mediana (51-250)</option>
                <option value="large">Grande (251-1000)</option>
                <option value="enterprise">Corporativo (1000+)</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">
                Ciudad
              </label>
              <input
                type="text"
                value={formData.city}
                onChange={(e) => setFormData({ ...formData, city: e.target.value })}
                className="input-glass"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">
                País
              </label>
              <input
                type="text"
                value={formData.country}
                onChange={(e) => setFormData({ ...formData, country: e.target.value })}
                className="input-glass"
              />
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-4">
            <button type="button" onClick={onClose} className="btn-secondary">
              Cancelar
            </button>
            <button type="submit" disabled={loading} className="btn-primary">
              {loading ? 'Guardando...' : (organization ? 'Actualizar' : 'Crear')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

const OrganizationsPage = () => {
  const navigate = useNavigate();
  const [organizations, setOrganizations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedOrg, setSelectedOrg] = useState(null);

  const fetchOrganizations = async () => {
    try {
      const params = {};
      if (search) params.search = search;
      if (statusFilter) params.status = statusFilter;
      
      const data = await organizationService.getAll(params);
      setOrganizations(data.results || data);
    } catch (error) {
      // Use mock data on error
      setOrganizations([
        { id: '1', code: 'ORG00001', name: 'Tech Corp', email: 'contact@techcorp.com', industry: 'technology', status: 'active', users_count: 15, max_users: 20 },
        { id: '2', code: 'ORG00002', name: 'Acme Inc', email: 'info@acme.com', industry: 'manufacturing', status: 'active', users_count: 8, max_users: 10 },
        { id: '3', code: 'ORG00003', name: 'StartupXYZ', email: 'hello@startupxyz.io', industry: 'technology', status: 'trial', users_count: 3, max_users: 5 },
        { id: '4', code: 'ORG00004', name: 'Global Services', email: 'contact@global.com', industry: 'services', status: 'active', users_count: 12, max_users: 15 },
        { id: '5', code: 'ORG00005', name: 'Local Shop', email: 'shop@local.mx', industry: 'retail', status: 'suspended', users_count: 2, max_users: 5 },
      ]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOrganizations();
  }, [search, statusFilter]);

  const handleView = (org) => {
    navigate(`/organizations/${org.id}`);
  };

  const handleEdit = (org) => {
    setSelectedOrg(org);
    setModalOpen(true);
  };

  const handleDelete = async (org) => {
    if (window.confirm(`¿Estás seguro de eliminar "${org.name}"?`)) {
      try {
        await organizationService.delete(org.id);
        toast.success('Organización eliminada');
        fetchOrganizations();
      } catch (error) {
        toast.error('Error al eliminar la organización');
      }
    }
  };

  const handleCreate = () => {
    setSelectedOrg(null);
    setModalOpen(true);
  };

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-100">Organizaciones</h1>
          <p className="text-gray-500 mt-1">Gestiona las organizaciones cliente</p>
        </div>
        <button onClick={handleCreate} className="btn-primary flex items-center gap-2">
          <Plus className="w-5 h-5" />
          Nueva Organización
        </button>
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
              placeholder="Buscar organizaciones..."
              className="input-glass pl-11"
            />
          </div>
          <div className="flex gap-3">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="input-glass w-auto"
            >
              <option value="">Todos los estados</option>
              <option value="active">Activas</option>
              <option value="trial">Trial</option>
              <option value="suspended">Suspendidas</option>
              <option value="inactive">Inactivas</option>
            </select>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="glass-card overflow-hidden">
        {loading ? (
          <div className="p-8 text-center">
            <div className="w-8 h-8 border-2 border-primary-500 border-t-transparent rounded-full animate-spin mx-auto" />
            <p className="text-gray-500 mt-4">Cargando organizaciones...</p>
          </div>
        ) : organizations.length === 0 ? (
          <div className="p-8 text-center">
            <Building2 className="w-12 h-12 text-gray-600 mx-auto mb-4" />
            <p className="text-gray-400">No se encontraron organizaciones</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="table-glass">
              <thead>
                <tr>
                  <th>Organización</th>
                  <th>Email</th>
                  <th>Industria</th>
                  <th>Usuarios</th>
                  <th>Estado</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {organizations.map((org) => (
                  <OrganizationRow
                    key={org.id}
                    org={org}
                    onView={handleView}
                    onEdit={handleEdit}
                    onDelete={handleDelete}
                  />
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Modal */}
      <OrganizationModal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        organization={selectedOrg}
        onSave={fetchOrganizations}
      />
    </div>
  );
};

export default OrganizationsPage;
