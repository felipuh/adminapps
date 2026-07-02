import { useCallback, useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Building2, 
  BadgeCheck,
  Plus, 
  Eye,
  Edit,
  Trash2,
  Users,
  X
} from 'lucide-react';
import { organizationService } from '../services/api';
import toast from 'react-hot-toast';
import { useAuth } from '../contexts/AuthContext';
import { showConfirm } from '../services/dialogs';
import { DataTable, EmptyState, ErrorState, LoadingState, PageHeader, SearchInput, StatusBadge } from '../components/ui/EnterpriseUI';

const getProductSignals = (org, t) => {
  const rawProducts = org.products || org.active_products || org.entitlements || org.product_codes || [];
  const list = Array.isArray(rawProducts) ? rawProducts : [];
  const codes = list.map((item) => String(item.code || item.product_code || item.name || item).toLowerCase());
  const hasIso = Boolean(org.has_iso_smart || codes.some((code) => code.includes('iso')));
  const hasMed = Boolean(org.has_medsupplier || codes.some((code) => code.includes('med')));

  if (hasIso && hasMed) return [{ label: t.bothProducts, className: 'badge-success' }];
  if (hasIso) return [{ label: 'ISO Smart', className: 'badge-info' }];
  if (hasMed) return [{ label: 'MedSupplier', className: 'badge-info' }];
  if (list.length > 0) {
    return list.slice(0, 2).map((item) => ({
      label: item.name || item.product_name || item.code || item.product_code || String(item),
      className: 'badge-info',
    }));
  }
  return [{ label: t.noProduct, className: 'badge-neutral' }];
};

const formatDate = (value) => {
  if (!value) return '-';
  return new Date(value).toLocaleDateString('es-MX', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  });
};

// Organization Row Component
const OrganizationRow = ({ org, onView, onEdit, onDelete, t }) => {
  const statusLabels = {
    active: t.active,
    trial: 'Trial',
    suspended: t.suspended,
    inactive: t.inactive,
  };
  const productSignals = getProductSignals(org, t);
  const planLabel = org.subscription_plan_name || org.plan_name || org.subscription?.plan_name || org.subscription?.plan?.name || org.plan || '-';
  const updatedAt = org.updated_at || org.modified_at || org.created_at;

  return (
    <tr>
      <td className="px-4 py-4">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg border border-blue-100 bg-blue-50 text-blue-700">
            <Building2 className="w-5 h-5" />
          </div>
          <div className="min-w-0">
            <p className="font-semibold text-slate-950">{org.name}</p>
            <div className="mt-1 flex flex-wrap items-center gap-2">
              <p className="text-xs text-slate-500">{org.code || org.email}</p>
              {org.billing_exempt && (
                <span className="badge-success">
                  <BadgeCheck className="h-3 w-3" />
                  {t.billingExempt}
                </span>
              )}
            </div>
          </div>
        </div>
      </td>
      <td className="px-4 py-4">
        <StatusBadge status={org.status}>{statusLabels[org.status] || org.status}</StatusBadge>
      </td>
      <td className="px-4 py-4">
        <div className="flex flex-wrap gap-1.5">
          {productSignals.map((product) => (
            <span key={product.label} className={product.className}>{product.label}</span>
          ))}
        </div>
      </td>
      <td className="px-4 py-4">
        <div className="flex items-center gap-2 text-sm text-slate-600">
          <Users className="w-4 h-4" />
          <span>{org.users_count || 0} / {org.max_users}</span>
        </div>
      </td>
      <td className="px-4 py-4 text-sm text-slate-600">{planLabel}</td>
      <td className="px-4 py-4 text-sm text-slate-500">{formatDate(updatedAt)}</td>
      <td className="px-4 py-4">
        <div className="flex items-center gap-2 whitespace-nowrap">
          <button
            onClick={() => onView(org)}
            className="inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs font-semibold text-primary-700 hover:bg-blue-50"
          >
            <Eye className="w-3.5 h-3.5" />
            {t.viewDetails}
          </button>
          <button
            onClick={() => onEdit(org)}
            className="inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs font-semibold text-slate-600 hover:bg-slate-100"
          >
            <Edit className="w-3.5 h-3.5" />
            {t.edit}
          </button>
          <button
            onClick={() => onDelete(org)}
            className="inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs font-semibold text-red-700 hover:bg-red-50"
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
    organizationsLoadError: isEnglish ? 'Could not load organizations' : 'No se pudieron cargar las organizaciones',
    organizationsLoadErrorHelp: isEnglish ? 'Check the API connection and try again.' : 'Revisa la conexion con la API e intenta de nuevo.',
    retry: isEnglish ? 'Retry' : 'Reintentar',
    noOrganizations: isEnglish ? 'No organizations found' : 'No se encontraron organizaciones',
    organization: isEnglish ? 'Organization' : 'Organizacion',
    users: isEnglish ? 'Users' : 'Usuarios',
    status: isEnglish ? 'Status' : 'Estado',
    billingExempt: isEnglish ? 'Billing exempt' : 'Exenta de cobro',
    activeProducts: isEnglish ? 'Active products' : 'Productos activos',
    subscriptionPlan: isEnglish ? 'Subscription / plan' : 'Suscripcion / plan',
    updatedAt: isEnglish ? 'Updated' : 'Actualizacion',
    bothProducts: isEnglish ? 'Both products' : 'Ambos productos',
    noProduct: isEnglish ? 'No product' : 'Sin producto',
  };
  const navigate = useNavigate();
  const [organizations, setOrganizations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(null);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedOrg, setSelectedOrg] = useState(null);

  const fetchOrganizations = useCallback(async () => {
    setLoading(true);
    setLoadError(null);
    try {
      const params = {};
      if (search) params.search = search;
      if (statusFilter) params.status = statusFilter;
      
      const data = await organizationService.getAll(params);
      setOrganizations(data.results || data);
    } catch (error) {
      setOrganizations([]);
      setLoadError(error);
    } finally {
      setLoading(false);
    }
  }, [search, statusFilter]);

  useEffect(() => {
    fetchOrganizations();
  }, [fetchOrganizations]);

  const handleView = (org) => {
    navigate(`/organizations/${org.id}`);
  };

  const handleEdit = (org) => {
    setSelectedOrg(org);
    setModalOpen(true);
  };

  const handleDelete = async (org) => {
    const isEnglish = document.documentElement.lang === 'en';
    const confirmed = await showConfirm({
      title: isEnglish ? 'Delete organization' : 'Eliminar organizacion',
      text: `${t.confirmDelete} "${org.name}"?`,
      confirmButtonText: isEnglish ? 'Delete' : 'Eliminar',
      cancelButtonText: isEnglish ? 'Cancel' : 'Cancelar',
    });

    if (!confirmed) {
      return;
    }

    try {
      await organizationService.delete(org.id);
      toast.success(t.orgDeleted);
      fetchOrganizations();
    } catch {
      toast.error(t.orgDeleteError);
    }
  };

  const handleCreate = () => {
    setSelectedOrg(null);
    setModalOpen(true);
  };

  return (
    <div className="enterprise-page">
      <PageHeader
        eyebrow={isEnglish ? 'Customer administration' : 'Administración de clientes'}
        title={t.pageTitle}
        description={t.pageSubtitle}
        actions={(
          <button onClick={handleCreate} className="btn-primary">
            <Plus className="w-5 h-5" />
            {t.newOrganization}
          </button>
        )}
      />

      {/* Filters */}
      <div className="enterprise-card p-4">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1">
            <SearchInput
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder={t.searchPlaceholder}
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
      <div className="enterprise-card overflow-hidden">
        {loading ? (
          <LoadingState label={t.loadingOrganizations} />
        ) : loadError ? (
          <ErrorState
            title={t.organizationsLoadError}
            description={t.organizationsLoadErrorHelp}
            action={<button type="button" onClick={fetchOrganizations} className="btn-secondary">{t.retry}</button>}
          />
        ) : organizations.length === 0 ? (
          <div className="p-6">
            <EmptyState
              icon={Building2}
              title={t.noOrganizations}
              description={isEnglish ? 'Create the first customer organization to assign products and subscriptions.' : 'Crea la primera organización cliente para asignar productos y suscripciones.'}
              action={<button onClick={handleCreate} className="btn-primary">{t.newOrganization}</button>}
            />
          </div>
        ) : (
          <DataTable>
              <thead>
                <tr>
                  <th>{t.organization}</th>
                  <th>{t.status}</th>
                  <th>{t.activeProducts}</th>
                  <th>{t.users}</th>
                  <th>{t.subscriptionPlan}</th>
                  <th>{t.updatedAt}</th>
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
          </DataTable>
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
