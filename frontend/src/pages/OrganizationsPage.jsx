import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Building2, 
  BadgeCheck,
  Plus, 
  Search, 
  Filter,
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
import { useAuth } from '../contexts/AuthContext';

// Organization Row Component
const OrganizationRow = ({ org, onView, onEdit, onDelete, t }) => {
  const statusColors = {
    active: 'badge-success',
    trial: 'badge-info',
    suspended: 'badge-danger',
    inactive: 'badge-neutral',
  };

  const statusLabels = {
    active: t.active,
    trial: 'Trial',
    suspended: t.suspended,
    inactive: t.inactive,
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
            <div className="mt-1 flex flex-wrap items-center gap-2">
              <p className="text-xs text-gray-500">{org.code}</p>
              {org.billing_exempt && (
                <span className="inline-flex items-center gap-1 rounded-full border border-emerald-400/30 bg-emerald-500/10 px-2 py-0.5 text-[11px] font-medium text-emerald-300">
                  <BadgeCheck className="h-3 w-3" />
                  {t.billingExempt}
                </span>
              )}
            </div>
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
        <div className="flex items-center gap-2 whitespace-nowrap">
          <button
            onClick={() => onView(org)}
            className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs text-gray-200 hover:bg-dark-200 transition-colors"
          >
            <Eye className="w-3.5 h-3.5" />
            {t.viewDetails}
          </button>
          <button
            onClick={() => onEdit(org)}
            className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs text-gray-200 hover:bg-dark-200 transition-colors"
          >
            <Edit className="w-3.5 h-3.5" />
            {t.edit}
          </button>
          <button
            onClick={() => onDelete(org)}
            className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs text-red-400 hover:bg-red-500/10 transition-colors"
          >
            <Trash2 className="w-3.5 h-3.5" />
            {t.delete}
          </button>
        </div>
      </td>
    </tr>
  );
};

// Create/Edit Organization Modal
const OrganizationModal = ({ isOpen, onClose, organization, onSave, t, isEnglish }) => {
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
    country: isEnglish ? 'Mexico' : 'Mexico',
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
        country: organization.country || (isEnglish ? 'Mexico' : 'Mexico'),
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
        country: isEnglish ? 'Mexico' : 'Mexico',
      });
    }
  }, [organization, isEnglish]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      if (organization) {
        await organizationService.update(organization.id, formData);
        toast.success(t.orgUpdated);
      } else {
        await organizationService.create(formData);
        toast.success(t.orgCreated);
      }
      onSave();
      onClose();
    } catch (error) {
      toast.error(error.response?.data?.detail || t.orgSaveError);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/65 backdrop-blur-sm p-4 md:p-6" onClick={onClose}>
      <div
        className="glass-card mx-auto w-full max-w-3xl h-full md:h-auto md:max-h-[90vh] overflow-hidden shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="border-b border-gray-700/50 px-5 py-4 md:px-6 md:py-5">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-xs uppercase tracking-[0.2em] text-primary-300">{isEnglish ? 'Organization form' : 'Formulario organizacion'}</p>
              <h2 className="mt-1 text-xl font-semibold text-gray-100">{organization ? t.editOrg : t.newOrg}</h2>
              <p className="mt-1 text-sm text-gray-500">{isEnglish ? 'Complete business and contact information.' : 'Completa la informacion comercial y de contacto.'}</p>
            </div>
            <button onClick={onClose} className="rounded-lg p-2 text-gray-400 hover:bg-dark-300 hover:text-gray-200 transition-colors">
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="flex h-[calc(100%-78px)] md:h-auto md:max-h-[calc(90vh-88px)] flex-col">
          <div className="flex-1 overflow-y-auto px-5 py-5 md:px-6 md:py-6 space-y-6">
            <div className="rounded-xl border border-gray-700/50 bg-dark-400/25 p-4 md:p-5">
              <p className="mb-4 text-xs font-semibold uppercase tracking-widest text-gray-500">{isEnglish ? 'General data' : 'Datos generales'}</p>
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <div>
                  <label className="mb-1.5 block text-sm font-medium text-gray-400">{t.orgName} *</label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="input-glass"
                    required
                  />
                </div>
                <div>
                  <label className="mb-1.5 block text-sm font-medium text-gray-400">{t.legalName}</label>
                  <input
                    type="text"
                    value={formData.legal_name}
                    onChange={(e) => setFormData({ ...formData, legal_name: e.target.value })}
                    className="input-glass"
                  />
                </div>
              </div>
            </div>

            <div className="rounded-xl border border-gray-700/50 bg-dark-400/25 p-4 md:p-5">
              <p className="mb-4 text-xs font-semibold uppercase tracking-widest text-gray-500">{isEnglish ? 'Contact' : 'Contacto'}</p>
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <div>
                  <label className="mb-1.5 block text-sm font-medium text-gray-400">{t.email} *</label>
                  <input
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    className="input-glass"
                    required
                  />
                </div>
                <div>
                  <label className="mb-1.5 block text-sm font-medium text-gray-400">{t.phone}</label>
                  <input
                    type="tel"
                    value={formData.phone}
                    onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                    className="input-glass"
                  />
                </div>
                <div className="md:col-span-2">
                  <label className="mb-1.5 block text-sm font-medium text-gray-400">{t.website}</label>
                  <input
                    type="url"
                    value={formData.website}
                    onChange={(e) => setFormData({ ...formData, website: e.target.value })}
                    className="input-glass"
                    placeholder="https://"
                  />
                </div>
              </div>
            </div>

            <div className="rounded-xl border border-gray-700/50 bg-dark-400/25 p-4 md:p-5">
              <p className="mb-4 text-xs font-semibold uppercase tracking-widest text-gray-500">{isEnglish ? 'Business profile' : 'Perfil comercial'}</p>
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <div>
                  <label className="mb-1.5 block text-sm font-medium text-gray-400">{t.industry}</label>
                  <select
                    value={formData.industry}
                    onChange={(e) => setFormData({ ...formData, industry: e.target.value })}
                    className="input-glass"
                  >
                    <option value="manufacturing">{isEnglish ? 'Manufacturing' : 'Manufactura'}</option>
                    <option value="technology">{isEnglish ? 'Technology' : 'Tecnologia'}</option>
                    <option value="healthcare">{isEnglish ? 'Healthcare' : 'Salud'}</option>
                    <option value="finance">{isEnglish ? 'Finance' : 'Finanzas'}</option>
                    <option value="education">{isEnglish ? 'Education' : 'Educacion'}</option>
                    <option value="construction">{isEnglish ? 'Construction' : 'Construccion'}</option>
                    <option value="retail">{isEnglish ? 'Retail' : 'Comercio'}</option>
                    <option value="services">{isEnglish ? 'Services' : 'Servicios'}</option>
                    <option value="government">{isEnglish ? 'Government' : 'Gobierno'}</option>
                    <option value="other">{isEnglish ? 'Other' : 'Otro'}</option>
                  </select>
                </div>
                <div>
                  <label className="mb-1.5 block text-sm font-medium text-gray-400">{t.size}</label>
                  <select
                    value={formData.size}
                    onChange={(e) => setFormData({ ...formData, size: e.target.value })}
                    className="input-glass"
                  >
                    <option value="micro">{isEnglish ? 'Micro' : 'Micro'} (1-10)</option>
                    <option value="small">{isEnglish ? 'Small' : 'Pequena'} (11-50)</option>
                    <option value="medium">{isEnglish ? 'Medium' : 'Mediana'} (51-250)</option>
                    <option value="large">{isEnglish ? 'Large' : 'Grande'} (251-1000)</option>
                    <option value="enterprise">{isEnglish ? 'Enterprise' : 'Corporativo'} (1000+)</option>
                  </select>
                </div>
                <div>
                  <label className="mb-1.5 block text-sm font-medium text-gray-400">{t.city}</label>
                  <input
                    type="text"
                    value={formData.city}
                    onChange={(e) => setFormData({ ...formData, city: e.target.value })}
                    className="input-glass"
                  />
                </div>
                <div>
                  <label className="mb-1.5 block text-sm font-medium text-gray-400">{t.country}</label>
                  <input
                    type="text"
                    value={formData.country}
                    onChange={(e) => setFormData({ ...formData, country: e.target.value })}
                    className="input-glass"
                  />
                </div>
              </div>
            </div>
          </div>

          <div className="border-t border-gray-700/50 bg-dark-400/20 px-5 py-4 md:px-6">
            <div className="flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
              <button type="button" onClick={onClose} className="btn-secondary w-full sm:w-auto">
                {t.cancel}
              </button>
              <button type="submit" disabled={loading} className="btn-primary w-full sm:w-auto">
                {loading ? t.saving : (organization ? t.update : t.create)}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
};

const OrganizationsPage = () => {
  const { user } = useAuth();
  const isEnglish = user?.language === 'en';
  const t = {
    active: isEnglish ? 'Active' : 'Activa',
    suspended: isEnglish ? 'Suspended' : 'Suspendida',
    inactive: isEnglish ? 'Inactive' : 'Inactiva',
    viewDetails: isEnglish ? 'View details' : 'Ver detalles',
    edit: isEnglish ? 'Edit' : 'Editar',
    delete: isEnglish ? 'Delete' : 'Eliminar',
    orgUpdated: isEnglish ? 'Organization updated successfully' : 'Organizacion actualizada correctamente',
    orgCreated: isEnglish ? 'Organization created successfully' : 'Organizacion creada correctamente',
    orgSaveError: isEnglish ? 'Error saving organization' : 'Error al guardar la organizacion',
    editOrg: isEnglish ? 'Edit Organization' : 'Editar Organizacion',
    newOrg: isEnglish ? 'New Organization' : 'Nueva Organizacion',
    orgName: isEnglish ? 'Organization Name' : 'Nombre de la Organizacion',
    legalName: isEnglish ? 'Legal Name' : 'Razon Social',
    email: 'Email',
    phone: isEnglish ? 'Phone' : 'Telefono',
    website: isEnglish ? 'Website' : 'Sitio Web',
    industry: isEnglish ? 'Industry' : 'Industria',
    size: isEnglish ? 'Size' : 'Tamano',
    city: isEnglish ? 'City' : 'Ciudad',
    country: isEnglish ? 'Country' : 'Pais',
    cancel: isEnglish ? 'Cancel' : 'Cancelar',
    saving: isEnglish ? 'Saving...' : 'Guardando...',
    update: isEnglish ? 'Update' : 'Actualizar',
    create: isEnglish ? 'Create' : 'Crear',
    confirmDelete: isEnglish ? 'Are you sure you want to delete' : 'Estas seguro de eliminar',
    orgDeleted: isEnglish ? 'Organization deleted' : 'Organizacion eliminada',
    orgDeleteError: isEnglish ? 'Error deleting organization' : 'Error al eliminar la organizacion',
    pageTitle: isEnglish ? 'Organizations' : 'Organizaciones',
    pageSubtitle: isEnglish ? 'Manage customer organizations' : 'Gestiona las organizaciones cliente',
    newOrganization: isEnglish ? 'New Organization' : 'Nueva Organizacion',
    searchPlaceholder: isEnglish ? 'Search organizations...' : 'Buscar organizaciones...',
    allStatuses: isEnglish ? 'All statuses' : 'Todos los estados',
    activePlural: isEnglish ? 'Active' : 'Activas',
    suspendedPlural: isEnglish ? 'Suspended' : 'Suspendidas',
    inactivePlural: isEnglish ? 'Inactive' : 'Inactivas',
    loadingOrganizations: isEnglish ? 'Loading organizations...' : 'Cargando organizaciones...',
    noOrganizations: isEnglish ? 'No organizations found' : 'No se encontraron organizaciones',
    organization: isEnglish ? 'Organization' : 'Organizacion',
    users: isEnglish ? 'Users' : 'Usuarios',
    status: isEnglish ? 'Status' : 'Estado',
    billingExempt: isEnglish ? 'Billing exempt' : 'Exenta de cobro',
  };
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
    if (window.confirm(`${t.confirmDelete} "${org.name}"?`)) {
      try {
        await organizationService.delete(org.id);
        toast.success(t.orgDeleted);
        fetchOrganizations();
      } catch (error) {
        toast.error(t.orgDeleteError);
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
          <h1 className="text-2xl font-bold text-gray-100">{t.pageTitle}</h1>
          <p className="text-gray-500 mt-1">{t.pageSubtitle}</p>
        </div>
        <button onClick={handleCreate} className="btn-primary flex items-center gap-2">
          <Plus className="w-5 h-5" />
          {t.newOrganization}
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
              placeholder={t.searchPlaceholder}
              className="input-glass pl-11"
            />
          </div>
          <div className="flex gap-3">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="input-glass w-auto"
            >
              <option value="">{t.allStatuses}</option>
              <option value="active">{t.activePlural}</option>
              <option value="trial">Trial</option>
              <option value="suspended">{t.suspendedPlural}</option>
              <option value="inactive">{t.inactivePlural}</option>
            </select>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="glass-card overflow-hidden">
        {loading ? (
          <div className="p-8 text-center">
            <div className="w-8 h-8 border-2 border-primary-500 border-t-transparent rounded-full animate-spin mx-auto" />
            <p className="text-gray-500 mt-4">{t.loadingOrganizations}</p>
          </div>
        ) : organizations.length === 0 ? (
          <div className="p-8 text-center">
            <Building2 className="w-12 h-12 text-gray-600 mx-auto mb-4" />
            <p className="text-gray-400">{t.noOrganizations}</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="table-glass">
              <thead>
                <tr>
                  <th>{t.organization}</th>
                  <th>Email</th>
                  <th>{t.industry}</th>
                  <th>{t.users}</th>
                  <th>{t.status}</th>
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
                    t={t}
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
        t={t}
        isEnglish={isEnglish}
      />
    </div>
  );
};

export default OrganizationsPage;
