import React, { useEffect, useState } from 'react';
import { 
  User, 
  Lock, 
  Bell, 
  Palette, 
  Globe,
  Save,
  Eye,
  EyeOff
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { authService } from '../services/api';
import toast from 'react-hot-toast';

// Tab Component
const Tab = ({ active, onClick, icon: Icon, children }) => (
  <button
    onClick={onClick}
    className={`
      flex items-center gap-3 w-full px-4 py-3 rounded-lg text-left transition-colors
      ${active 
        ? 'bg-primary-500/10 text-primary-400 border-l-2 border-primary-500' 
        : 'text-gray-400 hover:text-gray-200 hover:bg-dark-200/50'
      }
    `}
  >
    <Icon className="w-5 h-5" />
    <span className="font-medium">{children}</span>
  </button>
);

// Profile Settings
const ProfileSettings = ({ user, onSave }) => {
  const [formData, setFormData] = useState({
    first_name: user?.first_name || '',
    last_name: user?.last_name || '',
    phone: user?.phone || '',
    job_title: user?.job_title || '',
    department: user?.department || '',
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    const result = await onSave(formData);
    if (result.success) {
      toast.success('Perfil actualizado correctamente');
    } else {
      toast.error(result.error || 'No se pudo actualizar el perfil');
    }
    setLoading(false);
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-gray-100">Información Personal</h2>
        <p className="text-gray-500 mt-1">Actualiza tu información de perfil</p>
      </div>

      <div className="flex items-center gap-6">
        <div className="w-20 h-20 rounded-full bg-gradient-to-br from-primary-400 to-primary-600 flex items-center justify-center text-white text-2xl font-bold">
          {user?.first_name?.[0]}{user?.last_name?.[0]}
        </div>
        <div>
          <button className="btn-secondary">Cambiar Foto</button>
          <p className="text-xs text-gray-500 mt-2">JPG, PNG o GIF. Máximo 2MB</p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">Nombre</label>
            <input
              type="text"
              value={formData.first_name}
              onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
              className="input-glass"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">Apellido</label>
            <input
              type="text"
              value={formData.last_name}
              onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
              className="input-glass"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-400 mb-2">Email</label>
          <input
            type="email"
            value={user?.email || ''}
            className="input-glass bg-dark-400/30"
            disabled
          />
          <p className="text-xs text-gray-500 mt-1">El email no se puede cambiar</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">Teléfono</label>
            <input
              type="tel"
              value={formData.phone}
              onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
              className="input-glass"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">Cargo</label>
            <input
              type="text"
              value={formData.job_title}
              onChange={(e) => setFormData({ ...formData, job_title: e.target.value })}
              className="input-glass"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-400 mb-2">Departamento</label>
          <input
            type="text"
            value={formData.department}
            onChange={(e) => setFormData({ ...formData, department: e.target.value })}
            className="input-glass"
          />
        </div>

        <div className="pt-4">
          <button type="submit" disabled={loading} className="btn-primary flex items-center gap-2">
            <Save className="w-4 h-4" />
            {loading ? 'Guardando...' : 'Guardar Cambios'}
          </button>
        </div>
      </form>
    </div>
  );
};

// Security Settings
const SecuritySettings = ({ changePassword, mustChangePassword, securityAlert }) => {
  const [formData, setFormData] = useState({
    current_password: '',
    new_password: '',
    confirm_password: '',
  });
  const [showPasswords, setShowPasswords] = useState({
    current: false,
    new: false,
    confirm: false,
  });
  const [loading, setLoading] = useState(false);
  const [sessions, setSessions] = useState([]);

  useEffect(() => {
    const loadSessions = async () => {
      try {
        const data = await authService.getMySessions();
        setSessions(Array.isArray(data) ? data : []);
      } catch (error) {
        setSessions([]);
      }
    };
    loadSessions();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (formData.new_password !== formData.confirm_password) {
      toast.error('Las contraseñas no coinciden');
      return;
    }

    setLoading(true);
    const result = await changePassword(
      formData.current_password,
      formData.new_password,
      formData.confirm_password,
    );

    if (result.success) {
      toast.success('Contraseña actualizada correctamente');
      setFormData({ current_password: '', new_password: '', confirm_password: '' });
    } else {
      toast.error(result.error);
    }

    setLoading(false);
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-gray-100">Seguridad</h2>
        <p className="text-gray-500 mt-1">Gestiona tu contraseña y seguridad de la cuenta</p>
      </div>

      {mustChangePassword && (
        <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-200">
          Debes cambiar tu contraseña temporal antes de continuar. Usa una contraseña o frase de al menos 12 caracteres y evita datos previsibles.
        </div>
      )}
      {mustChangePassword && securityAlert?.reason_code === 'TEMP_PASSWORD_EXPIRING' && (
        <div className="rounded-lg border border-orange-500/30 bg-orange-500/10 px-4 py-3 text-sm text-orange-200">
          Tu contraseña temporal vence en {securityAlert.days_left} dia(s). Cámbiala ahora para evitar el bloqueo de acceso.
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4 max-w-md">
        <div>
          <label className="block text-sm font-medium text-gray-400 mb-2">Contraseña Actual</label>
          <div className="relative">
            <input
              type={showPasswords.current ? 'text' : 'password'}
              value={formData.current_password}
              onChange={(e) => setFormData({ ...formData, current_password: e.target.value })}
              className="input-glass pr-11"
              required
            />
            <button
              type="button"
              onClick={() => setShowPasswords({ ...showPasswords, current: !showPasswords.current })}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-400"
            >
              {showPasswords.current ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
            </button>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-400 mb-2">Nueva Contraseña</label>
          <div className="relative">
            <input
              type={showPasswords.new ? 'text' : 'password'}
              value={formData.new_password}
              onChange={(e) => setFormData({ ...formData, new_password: e.target.value })}
              className="input-glass pr-11"
              required
            />
            <button
              type="button"
              onClick={() => setShowPasswords({ ...showPasswords, new: !showPasswords.new })}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-400"
            >
              {showPasswords.new ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
            </button>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-400 mb-2">Confirmar Nueva Contraseña</label>
          <div className="relative">
            <input
              type={showPasswords.confirm ? 'text' : 'password'}
              value={formData.confirm_password}
              onChange={(e) => setFormData({ ...formData, confirm_password: e.target.value })}
              className="input-glass pr-11"
              required
            />
            <button
              type="button"
              onClick={() => setShowPasswords({ ...showPasswords, confirm: !showPasswords.confirm })}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-400"
            >
              {showPasswords.confirm ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
            </button>
          </div>
        </div>

        <div className="pt-4">
          <button type="submit" disabled={loading} className="btn-primary flex items-center gap-2">
            <Lock className="w-4 h-4" />
            {loading ? 'Actualizando...' : 'Cambiar Contraseña'}
          </button>
        </div>
      </form>

      <div className="pt-6 border-t border-gray-700/50">
        <h3 className="font-semibold text-gray-200 mb-4">Sesiones Activas</h3>
        <div className="space-y-3">
          {sessions.length === 0 && (
            <div className="p-4 bg-dark-400/30 rounded-lg text-sm text-gray-500">
              No hay sesiones activas adicionales para mostrar.
            </div>
          )}
          {sessions.map((session, index) => (
            <div key={session.id} className="flex items-center justify-between p-4 bg-dark-400/30 rounded-lg">
              <div>
                <p className="text-gray-200">{session.browser || 'Navegador desconocido'} en {session.os || 'SO desconocido'}</p>
                <p className="text-sm text-gray-500">{session.ip_address || 'IP no disponible'} • {session.device_type || 'dispositivo'}</p>
              </div>
              {index === 0 ? <span className="badge-success">Actual</span> : <span className="badge-neutral">Activa</span>}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

// Notification Settings
const NotificationSettings = ({ user, onSave }) => {
  const [settings, setSettings] = useState({
    email_notifications: Boolean(user?.email_notifications),
    push_notifications: Boolean(user?.push_notifications),
    notify_risk_critical: true,
    notify_risk_high: true,
    notify_objective_deadline: true,
    notify_document_expiry: true,
  });

  useEffect(() => {
    setSettings((prev) => ({
      ...prev,
      email_notifications: Boolean(user?.email_notifications),
      push_notifications: Boolean(user?.push_notifications),
    }));
  }, [user]);

  const handleToggle = async (key) => {
    const nextValue = !settings[key];
    const updated = { ...settings, [key]: nextValue };
    setSettings(updated);

    if (key === 'email_notifications' || key === 'push_notifications') {
      const result = await onSave({ [key]: nextValue });
      if (!result.success) {
        setSettings(settings);
        toast.error(result.error || 'No se pudo guardar la configuración');
        return;
      }
    }

    toast.success('Configuración actualizada');
  };

  const Toggle = ({ checked, onChange }) => (
    <button
      onClick={onChange}
      className={`
        relative w-11 h-6 rounded-full transition-colors
        ${checked ? 'bg-primary-500' : 'bg-gray-600'}
      `}
    >
      <span className={`
        absolute top-1 w-4 h-4 rounded-full bg-white transition-transform
        ${checked ? 'left-6' : 'left-1'}
      `} />
    </button>
  );

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-gray-100">Notificaciones</h2>
        <p className="text-gray-500 mt-1">Configura cómo y cuándo recibir notificaciones</p>
      </div>

      <div className="space-y-4">
        <div className="flex items-center justify-between p-4 bg-dark-400/30 rounded-lg">
          <div>
            <p className="font-medium text-gray-200">Notificaciones por Email</p>
            <p className="text-sm text-gray-500">Recibir notificaciones en tu correo electrónico</p>
          </div>
          <Toggle 
            checked={settings.email_notifications} 
            onChange={() => handleToggle('email_notifications')} 
          />
        </div>

        <div className="flex items-center justify-between p-4 bg-dark-400/30 rounded-lg">
          <div>
            <p className="font-medium text-gray-200">Notificaciones Push</p>
            <p className="text-sm text-gray-500">Recibir notificaciones en el navegador</p>
          </div>
          <Toggle 
            checked={settings.push_notifications} 
            onChange={() => handleToggle('push_notifications')} 
          />
        </div>
      </div>

      <div className="pt-6 border-t border-gray-700/50">
        <h3 className="font-semibold text-gray-200 mb-4">Tipos de Notificaciones</h3>
        <div className="space-y-4">
          <div className="flex items-center justify-between p-4 bg-dark-400/30 rounded-lg">
            <div>
              <p className="font-medium text-gray-200">Riesgos Críticos</p>
              <p className="text-sm text-gray-500">Alertas de riesgos de nivel crítico</p>
            </div>
            <Toggle 
              checked={settings.notify_risk_critical} 
              onChange={() => handleToggle('notify_risk_critical')} 
            />
          </div>

          <div className="flex items-center justify-between p-4 bg-dark-400/30 rounded-lg">
            <div>
              <p className="font-medium text-gray-200">Objetivos por Vencer</p>
              <p className="text-sm text-gray-500">Recordatorios de fechas límite</p>
            </div>
            <Toggle 
              checked={settings.notify_objective_deadline} 
              onChange={() => handleToggle('notify_objective_deadline')} 
            />
          </div>

          <div className="flex items-center justify-between p-4 bg-dark-400/30 rounded-lg">
            <div>
              <p className="font-medium text-gray-200">Documentos por Expirar</p>
              <p className="text-sm text-gray-500">Alertas de documentos próximos a vencer</p>
            </div>
            <Toggle 
              checked={settings.notify_document_expiry} 
              onChange={() => handleToggle('notify_document_expiry')} 
            />
          </div>
        </div>
      </div>
    </div>
  );
};

// Appearance Settings
const AppearanceSettings = ({ user, onSave }) => {
  const [theme, setTheme] = useState(user?.theme || 'dark');
  const [language, setLanguage] = useState(user?.language || 'es');

  useEffect(() => {
    setTheme(user?.theme || 'dark');
    setLanguage(user?.language || 'es');
  }, [user]);

  const saveTheme = async (nextTheme) => {
    setTheme(nextTheme);
    const result = await onSave({ theme: nextTheme });
    if (!result.success) {
      setTheme(user?.theme || 'dark');
      toast.error(result.error || 'No se pudo guardar el tema');
      return;
    }
    toast.success('Tema actualizado');
  };

  const saveLanguage = async (nextLanguage) => {
    setLanguage(nextLanguage);
    const result = await onSave({ language: nextLanguage });
    if (!result.success) {
      setLanguage(user?.language || 'es');
      toast.error(result.error || 'No se pudo guardar el idioma');
      return;
    }
    toast.success('Idioma actualizado');
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-gray-100">Apariencia</h2>
        <p className="text-gray-500 mt-1">Personaliza la apariencia de la aplicación</p>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-400 mb-3">Tema</label>
        <div className="grid grid-cols-3 gap-4">
          {['light', 'dark', 'system'].map((t) => (
            <button
              key={t}
              onClick={() => saveTheme(t)}
              className={`
                p-4 rounded-lg border-2 transition-colors
                ${theme === t 
                  ? 'border-primary-500 bg-primary-500/10' 
                  : 'border-gray-700/50 hover:border-gray-600'
                }
              `}
            >
              <div className={`
                w-full h-16 rounded-lg mb-3
                ${t === 'light' ? 'bg-gray-100' : t === 'dark' ? 'bg-dark-400' : 'bg-gradient-to-r from-gray-100 to-dark-400'}
              `} />
              <p className="text-sm font-medium text-gray-200 capitalize">
                {t === 'light' ? 'Claro' : t === 'dark' ? 'Oscuro' : 'Sistema'}
              </p>
            </button>
          ))}
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-400 mb-2">Idioma</label>
        <select
          value={language}
          onChange={(e) => saveLanguage(e.target.value)}
          className="input-glass w-auto"
        >
          <option value="es">Español</option>
          <option value="en">English</option>
        </select>
      </div>
    </div>
  );
};

const SettingsPage = () => {
  const { user, changePassword, updateProfile, mustChangePassword, securityAlert } = useAuth();
  const [activeTab, setActiveTab] = useState(mustChangePassword ? 'security' : 'profile');

  useEffect(() => {
    if (mustChangePassword) {
      setActiveTab('security');
    }
  }, [mustChangePassword]);

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-100">Configuración</h1>
        <p className="text-gray-500 mt-1">Gestiona tu cuenta y preferencias</p>
      </div>

      {mustChangePassword && (
        <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-200">
          El acceso al resto del sistema queda restringido hasta completar el cambio de contraseña inicial.
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Sidebar */}
        <div className="lg:col-span-1">
          <div className="glass-card p-4 space-y-1">
            {!mustChangePassword && (
              <Tab active={activeTab === 'profile'} onClick={() => setActiveTab('profile')} icon={User}>
                Perfil
              </Tab>
            )}
            <Tab active={activeTab === 'security'} onClick={() => setActiveTab('security')} icon={Lock}>
              Seguridad
            </Tab>
            {!mustChangePassword && (
              <Tab active={activeTab === 'notifications'} onClick={() => setActiveTab('notifications')} icon={Bell}>
                Notificaciones
              </Tab>
            )}
            {!mustChangePassword && (
              <Tab active={activeTab === 'appearance'} onClick={() => setActiveTab('appearance')} icon={Palette}>
                Apariencia
              </Tab>
            )}
          </div>
        </div>

        {/* Content */}
        <div className="lg:col-span-3">
          <div className="glass-card p-6">
            {!mustChangePassword && activeTab === 'profile' && <ProfileSettings user={user} onSave={updateProfile} />}
            {activeTab === 'security' && (
              <SecuritySettings
                changePassword={changePassword}
                mustChangePassword={mustChangePassword}
                securityAlert={securityAlert}
              />
            )}
            {!mustChangePassword && activeTab === 'notifications' && <NotificationSettings user={user} onSave={updateProfile} />}
            {!mustChangePassword && activeTab === 'appearance' && <AppearanceSettings user={user} onSave={updateProfile} />}
          </div>
        </div>
      </div>
    </div>
  );
};

export default SettingsPage;
