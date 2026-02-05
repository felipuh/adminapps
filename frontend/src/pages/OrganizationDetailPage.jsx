import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  Building2, 
  ArrowLeft,
  Users,
  Mail,
  Phone,
  Globe,
  MapPin,
  Calendar,
  Settings,
  CreditCard,
  FileText,
  Shield,
  ToggleLeft,
  ToggleRight,
  Edit,
  Trash2
} from 'lucide-react';
import { organizationService } from '../services/api';
import toast from 'react-hot-toast';

// Tab Component
const Tab = ({ active, onClick, children }) => (
  <button
    onClick={onClick}
    className={`
      px-4 py-2 text-sm font-medium rounded-lg transition-colors
      ${active 
        ? 'bg-primary-500/20 text-primary-400' 
        : 'text-gray-400 hover:text-gray-200 hover:bg-dark-200/50'
      }
    `}
  >
    {children}
  </button>
);

// Info Row Component
const InfoRow = ({ icon: Icon, label, value }) => (
  <div className="flex items-start gap-3 py-3">
    <Icon className="w-5 h-5 text-gray-500 mt-0.5 flex-shrink-0" />
    <div>
      <p className="text-xs text-gray-500">{label}</p>
      <p className="text-gray-200">{value || '-'}</p>
    </div>
  </div>
);

// Module Toggle Component
const ModuleToggle = ({ name, enabled, onChange }) => (
  <div className="flex items-center justify-between py-3 border-b border-gray-700/30 last:border-0">
    <span className="text-gray-200">{name}</span>
    <button
      onClick={() => onChange(!enabled)}
      className={`transition-colors ${enabled ? 'text-emerald-400' : 'text-gray-500'}`}
    >
      {enabled ? <ToggleRight className="w-8 h-8" /> : <ToggleLeft className="w-8 h-8" />}
    </button>
  </div>
);

const OrganizationDetailPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [organization, setOrganization] = useState(null);
  const [settings, setSettings] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');

  // Validate ID - 'new' is not a valid organization ID
  useEffect(() => {
    if (id === 'new') {
      navigate('/organizations', { replace: true });
      return;
    }

    const fetchData = async () => {
      try {
        const [orgData, settingsData] = await Promise.all([
          organizationService.getById(id),
          organizationService.getSettings(id).catch(() => null),
        ]);
        setOrganization(orgData);
        setSettings(settingsData);
      } catch (error) {
        // Mock data for demo
        setOrganization({
          id,
          code: 'ORG00001',
          name: 'Tech Corp',
          legal_name: 'Tech Corporation S.A. de C.V.',
          email: 'contact@techcorp.com',
          phone: '+52 55 1234 5678',
          website: 'https://techcorp.com',
          address: 'Av. Reforma 123',
          city: 'Ciudad de México',
          state: 'CDMX',
          country: 'México',
          postal_code: '06600',
          industry: 'technology',
          size: 'medium',
          employees_count: 150,
          status: 'active',
          max_users: 20,
          max_documents: 500,
          max_storage_mb: 2048,
          iso_standards: ['ISO 9001', 'ISO 27001'],
          created_at: '2025-06-15T10:00:00Z',
          users_count: 15,
        });
        setSettings({
          module_sca_enabled: true,
          module_sie_enabled: true,
          module_asb_enabled: true,
          module_spm_enabled: true,
          module_documents_enabled: true,
          module_risks_enabled: true,
          module_objectives_enabled: true,
          ai_auto_analysis: false,
          theme: 'dark',
        });
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [id, navigate]);

  const handleModuleToggle = async (module, value) => {
    try {
      await organizationService.updateSettings(id, { [module]: value });
      setSettings({ ...settings, [module]: value });
      toast.success('Configuración actualizada');
    } catch (error) {
      toast.error('Error al actualizar configuración');
    }
  };

  const statusColors = {
    active: 'badge-success',
    trial: 'badge-info',
    suspended: 'badge-danger',
    inactive: 'badge-neutral',
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-12 w-64 skeleton rounded-lg" />
        <div className="glass-card p-8 h-96 skeleton" />
      </div>
    );
  }

  if (!organization) {
    return (
      <div className="glass-card p-8 text-center">
        <Building2 className="w-12 h-12 text-gray-600 mx-auto mb-4" />
        <p className="text-gray-400">Organización no encontrada</p>
        <button onClick={() => navigate('/organizations')} className="btn-primary mt-4">
          Volver a Organizaciones
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/organizations')}
            className="p-2 rounded-lg hover:bg-dark-300 text-gray-400 hover:text-gray-200 transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-primary-500/20 to-primary-600/20 flex items-center justify-center">
              <Building2 className="w-7 h-7 text-primary-400" />
            </div>
            <div>
              <div className="flex items-center gap-3">
                <h1 className="text-2xl font-bold text-gray-100">{organization.name}</h1>
                <span className={statusColors[organization.status]}>{organization.status}</span>
              </div>
              <p className="text-gray-500">{organization.code}</p>
            </div>
          </div>
        </div>
        <div className="flex gap-3">
          <button className="btn-secondary flex items-center gap-2">
            <Edit className="w-4 h-4" />
            Editar
          </button>
          <button className="btn-danger flex items-center gap-2">
            <Trash2 className="w-4 h-4" />
            Eliminar
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 overflow-x-auto pb-2">
        <Tab active={activeTab === 'overview'} onClick={() => setActiveTab('overview')}>
          Información General
        </Tab>
        <Tab active={activeTab === 'users'} onClick={() => setActiveTab('users')}>
          Usuarios
        </Tab>
        <Tab active={activeTab === 'modules'} onClick={() => setActiveTab('modules')}>
          Módulos ISO
        </Tab>
        <Tab active={activeTab === 'subscription'} onClick={() => setActiveTab('subscription')}>
          Suscripción
        </Tab>
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Contact Info */}
          <div className="glass-card p-6">
            <h2 className="text-lg font-semibold text-gray-100 mb-4">Información de Contacto</h2>
            <div className="divide-y divide-gray-700/30">
              <InfoRow icon={Mail} label="Email" value={organization.email} />
              <InfoRow icon={Phone} label="Teléfono" value={organization.phone} />
              <InfoRow icon={Globe} label="Sitio Web" value={organization.website} />
              <InfoRow icon={MapPin} label="Dirección" value={`${organization.address}, ${organization.city}, ${organization.country}`} />
            </div>
          </div>

          {/* Business Info */}
          <div className="glass-card p-6">
            <h2 className="text-lg font-semibold text-gray-100 mb-4">Información del Negocio</h2>
            <div className="divide-y divide-gray-700/30">
              <InfoRow icon={FileText} label="Razón Social" value={organization.legal_name} />
              <InfoRow icon={Building2} label="Industria" value={organization.industry} />
              <InfoRow icon={Users} label="Empleados" value={organization.employees_count?.toString()} />
              <InfoRow icon={Calendar} label="Fecha de Registro" value={new Date(organization.created_at).toLocaleDateString('es-MX')} />
            </div>
          </div>

          {/* Limits & Usage */}
          <div className="glass-card p-6">
            <h2 className="text-lg font-semibold text-gray-100 mb-4">Límites y Uso</h2>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-400">Usuarios</span>
                  <span className="text-gray-200">{organization.users_count} / {organization.max_users}</span>
                </div>
                <div className="w-full bg-dark-400 rounded-full h-2">
                  <div
                    className="bg-primary-500 h-2 rounded-full transition-all"
                    style={{ width: `${(organization.users_count / organization.max_users) * 100}%` }}
                  />
                </div>
              </div>
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-400">Documentos</span>
                  <span className="text-gray-200">125 / {organization.max_documents}</span>
                </div>
                <div className="w-full bg-dark-400 rounded-full h-2">
                  <div className="bg-emerald-500 h-2 rounded-full" style={{ width: '25%' }} />
                </div>
              </div>
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-400">Almacenamiento</span>
                  <span className="text-gray-200">512 MB / {organization.max_storage_mb} MB</span>
                </div>
                <div className="w-full bg-dark-400 rounded-full h-2">
                  <div className="bg-amber-500 h-2 rounded-full" style={{ width: '25%' }} />
                </div>
              </div>
            </div>
            
            {/* ISO Standards */}
            <div className="mt-6 pt-4 border-t border-gray-700/30">
              <p className="text-sm text-gray-400 mb-2">Estándares ISO</p>
              <div className="flex flex-wrap gap-2">
                {organization.iso_standards?.map((standard) => (
                  <span key={standard} className="badge-info">{standard}</span>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'users' && (
        <div className="glass-card p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-semibold text-gray-100">Usuarios de la Organización</h2>
            <button className="btn-primary flex items-center gap-2">
              <Users className="w-4 h-4" />
              Agregar Usuario
            </button>
          </div>
          <div className="text-center py-12 text-gray-400">
            <Users className="w-12 h-12 mx-auto mb-4 text-gray-600" />
            <p>Lista de usuarios se cargará aquí</p>
          </div>
        </div>
      )}

      {activeTab === 'modules' && settings && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="glass-card p-6">
            <h2 className="text-lg font-semibold text-gray-100 mb-4">Módulos ISO Smart</h2>
            <div className="divide-y divide-gray-700/30">
              <ModuleToggle
                name="SCA - Análisis de Contexto"
                enabled={settings.module_sca_enabled}
                onChange={(v) => handleModuleToggle('module_sca_enabled', v)}
              />
              <ModuleToggle
                name="SIE - Inteligencia de Stakeholders"
                enabled={settings.module_sie_enabled}
                onChange={(v) => handleModuleToggle('module_sie_enabled', v)}
              />
              <ModuleToggle
                name="ASB - Construcción de Alcance"
                enabled={settings.module_asb_enabled}
                onChange={(v) => handleModuleToggle('module_asb_enabled', v)}
              />
              <ModuleToggle
                name="SPM - Mapeo de Procesos"
                enabled={settings.module_spm_enabled}
                onChange={(v) => handleModuleToggle('module_spm_enabled', v)}
              />
              <ModuleToggle
                name="Gestión Documental"
                enabled={settings.module_documents_enabled}
                onChange={(v) => handleModuleToggle('module_documents_enabled', v)}
              />
              <ModuleToggle
                name="Gestión de Riesgos"
                enabled={settings.module_risks_enabled}
                onChange={(v) => handleModuleToggle('module_risks_enabled', v)}
              />
              <ModuleToggle
                name="Objetivos de Calidad"
                enabled={settings.module_objectives_enabled}
                onChange={(v) => handleModuleToggle('module_objectives_enabled', v)}
              />
            </div>
          </div>
          
          <div className="glass-card p-6">
            <h2 className="text-lg font-semibold text-gray-100 mb-4">Configuración de IA</h2>
            <div className="space-y-4">
              <ModuleToggle
                name="Análisis Automático"
                enabled={settings.ai_auto_analysis}
                onChange={(v) => handleModuleToggle('ai_auto_analysis', v)}
              />
              <p className="text-sm text-gray-500">
                Cuando está habilitado, el sistema ejecutará análisis automáticos periódicos 
                para detectar oportunidades de mejora y riesgos potenciales.
              </p>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'subscription' && (
        <div className="glass-card p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-semibold text-gray-100">Información de Suscripción</h2>
            <button className="btn-primary flex items-center gap-2">
              <CreditCard className="w-4 h-4" />
              Cambiar Plan
            </button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="p-4 bg-dark-400/30 rounded-lg">
              <p className="text-sm text-gray-500">Plan Actual</p>
              <p className="text-2xl font-bold text-gray-100 mt-1">Premium</p>
            </div>
            <div className="p-4 bg-dark-400/30 rounded-lg">
              <p className="text-sm text-gray-500">Próxima Facturación</p>
              <p className="text-2xl font-bold text-gray-100 mt-1">15 Feb 2026</p>
            </div>
            <div className="p-4 bg-dark-400/30 rounded-lg">
              <p className="text-sm text-gray-500">Monto Mensual</p>
              <p className="text-2xl font-bold text-gray-100 mt-1">$499 MXN</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default OrganizationDetailPage;
