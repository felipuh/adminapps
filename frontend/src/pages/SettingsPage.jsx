import React, { useEffect, useMemo, useRef, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  User,
  Lock,
  Bell,
  Palette,
  Save,
  Eye,
  EyeOff,
  Camera,
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { authService } from '../services/api';
import toast from 'react-hot-toast';

const buildMediaUrl = (value) => {
  if (!value) {
    return null;
  }
  if (value.startsWith('http://') || value.startsWith('https://')) {
    return value;
  }
  return `${window.location.origin}${value.startsWith('/') ? '' : '/'}${value}`;
};

const getCopy = (locale) => {
  const es = {
    pageTitle: 'Configuracion',
    pageSubtitle: 'Gestiona tu cuenta y preferencias',
    tabs: {
      profile: 'Perfil',
      security: 'Seguridad',
      notifications: 'Notificaciones',
      appearance: 'Apariencia',
    },
    profile: {
      title: 'Informacion Personal',
      subtitle: 'Actualiza tu informacion de perfil y avatar',
      changePhoto: 'Cambiar Foto',
      uploading: 'Subiendo...',
      accepted: 'JPG, PNG o GIF. Maximo 2MB',
      firstName: 'Nombre',
      lastName: 'Apellido',
      email: 'Email',
      emailReadonly: 'El email no se puede cambiar',
      phone: 'Telefono',
      jobTitle: 'Cargo',
      department: 'Departamento',
      save: 'Guardar Cambios',
      saving: 'Guardando...',
    },
    security: {
      title: 'Seguridad',
      subtitle: 'Gestiona tu contrasena y seguridad de la cuenta',
      currentPassword: 'Contrasena Actual',
      newPassword: 'Nueva Contrasena',
      confirmPassword: 'Confirmar Nueva Contrasena',
      submit: 'Cambiar Contrasena',
      submitting: 'Actualizando...',
      sessions: 'Sesiones Activas',
      noSessions: 'No hay sesiones activas adicionales para mostrar.',
      current: 'Actual',
      active: 'Activa',
    },
    notifications: {
      title: 'Notificaciones',
      subtitle: 'Configura como y cuando recibir notificaciones',
      email: 'Notificaciones por Email',
      emailDesc: 'Recibir notificaciones en tu correo electronico',
      push: 'Notificaciones Push',
      pushDesc: 'Recibir notificaciones en el navegador',
      types: 'Tipos de Notificaciones',
      risk: 'Riesgos Criticos',
      riskDesc: 'Alertas de riesgos de nivel critico',
      objective: 'Objetivos por Vencer',
      objectiveDesc: 'Recordatorios de fechas limite',
      docs: 'Documentos por Expirar',
      docsDesc: 'Alertas de documentos proximos a vencer',
    },
    appearance: {
      title: 'Apariencia y Region',
      subtitle: 'Personaliza tema e idioma de la experiencia',
      theme: 'Tema',
      language: 'Idioma',
      languageHint: 'El idioma se aplica inmediatamente en este modulo.',
      light: 'Claro',
      dark: 'Oscuro',
      system: 'Sistema',
    },
    alerts: {
      mustChangePassword: 'El acceso al resto del sistema queda restringido hasta completar el cambio de contrasena inicial.',
      tempPassword: 'Tu contrasena temporal vence en',
      day: 'dia(s). Cambiala ahora para evitar el bloqueo de acceso.',
      mismatch: 'Las contrasenas no coinciden',
      profileSaved: 'Perfil actualizado correctamente',
      profileError: 'No se pudo actualizar el perfil',
      imageType: 'Selecciona una imagen valida (JPG, PNG o GIF).',
      imageSize: 'La imagen supera el limite de 2MB.',
      avatarSaved: 'Foto de perfil actualizada',
      avatarError: 'No se pudo actualizar la foto de perfil',
      passwordSaved: 'Contrasena actualizada correctamente',
      notificationsSaved: 'Configuracion actualizada',
      notificationsError: 'No se pudo guardar la configuracion',
      themeSaved: 'Tema actualizado',
      themeError: 'No se pudo guardar el tema',
      languageSaved: 'Idioma actualizado',
      languageError: 'No se pudo guardar el idioma',
    },
  };

  const en = {
    pageTitle: 'Settings',
    pageSubtitle: 'Manage your account and preferences',
    tabs: {
      profile: 'Profile',
      security: 'Security',
      notifications: 'Notifications',
      appearance: 'Appearance',
    },
    profile: {
      title: 'Personal Information',
      subtitle: 'Update your profile details and avatar',
      changePhoto: 'Change Photo',
      uploading: 'Uploading...',
      accepted: 'JPG, PNG or GIF. Max 2MB',
      firstName: 'First Name',
      lastName: 'Last Name',
      email: 'Email',
      emailReadonly: 'Email cannot be changed',
      phone: 'Phone',
      jobTitle: 'Job Title',
      department: 'Department',
      save: 'Save Changes',
      saving: 'Saving...',
    },
    security: {
      title: 'Security',
      subtitle: 'Manage your password and account protection',
      currentPassword: 'Current Password',
      newPassword: 'New Password',
      confirmPassword: 'Confirm New Password',
      submit: 'Change Password',
      submitting: 'Updating...',
      sessions: 'Active Sessions',
      noSessions: 'No additional active sessions to display.',
      current: 'Current',
      active: 'Active',
    },
    notifications: {
      title: 'Notifications',
      subtitle: 'Choose how and when you receive alerts',
      email: 'Email Notifications',
      emailDesc: 'Receive notifications by email',
      push: 'Push Notifications',
      pushDesc: 'Receive browser notifications',
      types: 'Notification Types',
      risk: 'Critical Risks',
      riskDesc: 'Alerts for critical-level risks',
      objective: 'Deadline Reminders',
      objectiveDesc: 'Reminders for upcoming due dates',
      docs: 'Expiring Documents',
      docsDesc: 'Alerts for documents close to expiration',
    },
    appearance: {
      title: 'Appearance & Region',
      subtitle: 'Customize theme and language preferences',
      theme: 'Theme',
      language: 'Language',
      languageHint: 'Language is applied immediately in this module.',
      light: 'Light',
      dark: 'Dark',
      system: 'System',
    },
    alerts: {
      mustChangePassword: 'Access to the rest of the system remains restricted until you complete the initial password change.',
      tempPassword: 'Your temporary password expires in',
      day: 'day(s). Change it now to avoid account lockout.',
      mismatch: 'Passwords do not match',
      profileSaved: 'Profile updated successfully',
      profileError: 'Could not update profile',
      imageType: 'Please select a valid image (JPG, PNG or GIF).',
      imageSize: 'Image exceeds the 2MB limit.',
      avatarSaved: 'Profile photo updated',
      avatarError: 'Could not update profile photo',
      passwordSaved: 'Password updated successfully',
      notificationsSaved: 'Settings updated',
      notificationsError: 'Could not save settings',
      themeSaved: 'Theme updated',
      themeError: 'Could not save theme',
      languageSaved: 'Language updated',
      languageError: 'Could not save language',
    },
  };

  return locale === 'en' ? en : es;
};

const Tab = ({ active, onClick, icon: Icon, children }) => (
  <button
    onClick={onClick}
    className={`
      group flex items-center gap-3 w-full px-4 py-3 rounded-xl text-left transition-all duration-200
      ${active
        ? 'bg-primary-500/12 text-primary-400 border border-primary-500/40 shadow-[0_8px_30px_rgba(0,73,144,0.2)]'
        : 'text-gray-400 hover:text-gray-200 hover:bg-dark-200/40 border border-transparent'
      }
    `}
  >
    <Icon className="w-5 h-5" />
    <span className="font-medium">{children}</span>
  </button>
);

const ProfileSettings = ({ user, onSave, copy }) => {
  const [formData, setFormData] = useState({
    first_name: user?.first_name || '',
    last_name: user?.last_name || '',
    phone: user?.phone || '',
    job_title: user?.job_title || '',
    department: user?.department || '',
  });
  const [loading, setLoading] = useState(false);
  const [uploadingAvatar, setUploadingAvatar] = useState(false);
  const [avatarPreview, setAvatarPreview] = useState(buildMediaUrl(user?.avatar));
  const fileInputRef = useRef(null);

  useEffect(() => {
    setFormData({
      first_name: user?.first_name || '',
      last_name: user?.last_name || '',
      phone: user?.phone || '',
      job_title: user?.job_title || '',
      department: user?.department || '',
    });
    setAvatarPreview(buildMediaUrl(user?.avatar));
  }, [user]);

  const initials = `${user?.first_name?.[0] || ''}${user?.last_name?.[0] || ''}`.trim() || 'U';

  const handleAvatarSelect = async (event) => {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }

    if (!file.type.startsWith('image/')) {
      toast.error(copy.alerts.imageType);
      event.target.value = '';
      return;
    }

    if (file.size > 2 * 1024 * 1024) {
      toast.error(copy.alerts.imageSize);
      event.target.value = '';
      return;
    }

    const optimisticPreview = URL.createObjectURL(file);
    setAvatarPreview(optimisticPreview);
    setUploadingAvatar(true);

    const payload = new FormData();
    payload.append('avatar', file);

    const result = await onSave(payload);
    if (result.success) {
      toast.success(copy.alerts.avatarSaved);
    } else {
      setAvatarPreview(buildMediaUrl(user?.avatar));
      toast.error(result.error || copy.alerts.avatarError);
    }

    URL.revokeObjectURL(optimisticPreview);
    setUploadingAvatar(false);
    event.target.value = '';
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    const result = await onSave(formData);
    if (result.success) {
      toast.success(copy.alerts.profileSaved);
    } else {
      toast.error(result.error || copy.alerts.profileError);
    }
    setLoading(false);
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-gray-100">{copy.profile.title}</h2>
        <p className="text-gray-500 mt-1">{copy.profile.subtitle}</p>
      </div>

      <div className="flex items-center gap-6 p-4 rounded-2xl border border-gray-700/40 bg-dark-400/30">
        <div className="relative w-20 h-20">
          {avatarPreview ? (
            <img src={avatarPreview} alt="Avatar" className="w-20 h-20 rounded-full object-cover ring-2 ring-primary-400/50" />
          ) : (
            <div className="w-20 h-20 rounded-full bg-gradient-to-br from-primary-400 to-primary-600 flex items-center justify-center text-white text-2xl font-bold">
              {initials}
            </div>
          )}
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            className="absolute -bottom-1 -right-1 w-8 h-8 rounded-full bg-primary-500 text-white flex items-center justify-center shadow-lg hover:bg-primary-400 transition-colors"
          >
            <Camera className="w-4 h-4" />
          </button>
        </div>

        <div>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/png,image/jpeg,image/jpg,image/gif"
            onChange={handleAvatarSelect}
            className="hidden"
          />
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            disabled={uploadingAvatar}
            className="btn-secondary"
          >
            {uploadingAvatar ? copy.profile.uploading : copy.profile.changePhoto}
          </button>
          <p className="text-xs text-gray-500 mt-2">{copy.profile.accepted}</p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">{copy.profile.firstName}</label>
            <input
              type="text"
              value={formData.first_name}
              onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
              className="input-glass"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">{copy.profile.lastName}</label>
            <input
              type="text"
              value={formData.last_name}
              onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
              className="input-glass"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-400 mb-2">{copy.profile.email}</label>
          <input type="email" value={user?.email || ''} className="input-glass bg-dark-400/30" disabled />
          <p className="text-xs text-gray-500 mt-1">{copy.profile.emailReadonly}</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">{copy.profile.phone}</label>
            <input
              type="tel"
              value={formData.phone}
              onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
              className="input-glass"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">{copy.profile.jobTitle}</label>
            <input
              type="text"
              value={formData.job_title}
              onChange={(e) => setFormData({ ...formData, job_title: e.target.value })}
              className="input-glass"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-400 mb-2">{copy.profile.department}</label>
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
            {loading ? copy.profile.saving : copy.profile.save}
          </button>
        </div>
      </form>
    </div>
  );
};

const SecuritySettings = ({ changePassword, mustChangePassword, securityAlert, copy }) => {
  const [formData, setFormData] = useState({
    current_password: '',
    new_password: '',
    confirm_password: '',
  });
  const [showPasswords, setShowPasswords] = useState({ current: false, new: false, confirm: false });
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
      toast.error(copy.alerts.mismatch);
      return;
    }

    setLoading(true);
    const result = await changePassword(formData.current_password, formData.new_password, formData.confirm_password);
    if (result.success) {
      toast.success(copy.alerts.passwordSaved);
      setFormData({ current_password: '', new_password: '', confirm_password: '' });
    } else {
      toast.error(result.error);
    }
    setLoading(false);
  };

  const PasswordField = ({ label, value, onChange, visible, toggle }) => (
    <div>
      <label className="block text-sm font-medium text-gray-400 mb-2">{label}</label>
      <div className="relative">
        <input type={visible ? 'text' : 'password'} value={value} onChange={onChange} className="input-glass pr-11" required />
        <button type="button" onClick={toggle} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-400">
          {visible ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
        </button>
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-gray-100">{copy.security.title}</h2>
        <p className="text-gray-500 mt-1">{copy.security.subtitle}</p>
      </div>

      {mustChangePassword && securityAlert?.reason_code === 'TEMP_PASSWORD_EXPIRING' && (
        <div className="rounded-lg border border-orange-500/30 bg-orange-500/10 px-4 py-3 text-sm text-orange-200">
          {copy.alerts.tempPassword} {securityAlert.days_left} {copy.alerts.day}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4 max-w-md">
        <PasswordField
          label={copy.security.currentPassword}
          value={formData.current_password}
          onChange={(e) => setFormData({ ...formData, current_password: e.target.value })}
          visible={showPasswords.current}
          toggle={() => setShowPasswords({ ...showPasswords, current: !showPasswords.current })}
        />
        <PasswordField
          label={copy.security.newPassword}
          value={formData.new_password}
          onChange={(e) => setFormData({ ...formData, new_password: e.target.value })}
          visible={showPasswords.new}
          toggle={() => setShowPasswords({ ...showPasswords, new: !showPasswords.new })}
        />
        <PasswordField
          label={copy.security.confirmPassword}
          value={formData.confirm_password}
          onChange={(e) => setFormData({ ...formData, confirm_password: e.target.value })}
          visible={showPasswords.confirm}
          toggle={() => setShowPasswords({ ...showPasswords, confirm: !showPasswords.confirm })}
        />

        <div className="pt-4">
          <button type="submit" disabled={loading} className="btn-primary flex items-center gap-2">
            <Lock className="w-4 h-4" />
            {loading ? copy.security.submitting : copy.security.submit}
          </button>
        </div>
      </form>

      <div className="pt-6 border-t border-gray-700/50">
        <h3 className="font-semibold text-gray-200 mb-4">{copy.security.sessions}</h3>
        <div className="space-y-3">
          {sessions.length === 0 && <div className="p-4 bg-dark-400/30 rounded-lg text-sm text-gray-500">{copy.security.noSessions}</div>}
          {sessions.map((session, index) => (
            <div key={session.id} className="flex items-center justify-between p-4 bg-dark-400/30 rounded-lg">
              <div>
                <p className="text-gray-200">{session.browser || 'Browser'} / {session.os || 'OS'}</p>
                <p className="text-sm text-gray-500">{session.ip_address || 'IP'} • {session.device_type || 'device'}</p>
              </div>
              {index === 0 ? <span className="badge-success">{copy.security.current}</span> : <span className="badge-neutral">{copy.security.active}</span>}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

const NotificationSettings = ({ user, onSave, copy }) => {
  const [settings, setSettings] = useState({
    email_notifications: Boolean(user?.email_notifications),
    push_notifications: Boolean(user?.push_notifications),
    notify_risk_critical: true,
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
        toast.error(result.error || copy.alerts.notificationsError);
        return;
      }
    }

    toast.success(copy.alerts.notificationsSaved);
  };

  const Toggle = ({ checked, onChange }) => (
    <button onClick={onChange} className={`relative w-11 h-6 rounded-full transition-colors ${checked ? 'bg-primary-500' : 'bg-gray-600'}`}>
      <span className={`absolute top-1 w-4 h-4 rounded-full bg-white transition-transform ${checked ? 'left-6' : 'left-1'}`} />
    </button>
  );

  const Row = ({ title, description, checked, onChange }) => (
    <div className="flex items-center justify-between p-4 bg-dark-400/30 rounded-lg">
      <div>
        <p className="font-medium text-gray-200">{title}</p>
        <p className="text-sm text-gray-500">{description}</p>
      </div>
      <Toggle checked={checked} onChange={onChange} />
    </div>
  );

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-gray-100">{copy.notifications.title}</h2>
        <p className="text-gray-500 mt-1">{copy.notifications.subtitle}</p>
      </div>

      <div className="space-y-4">
        <Row
          title={copy.notifications.email}
          description={copy.notifications.emailDesc}
          checked={settings.email_notifications}
          onChange={() => handleToggle('email_notifications')}
        />
        <Row
          title={copy.notifications.push}
          description={copy.notifications.pushDesc}
          checked={settings.push_notifications}
          onChange={() => handleToggle('push_notifications')}
        />
      </div>

      <div className="pt-6 border-t border-gray-700/50">
        <h3 className="font-semibold text-gray-200 mb-4">{copy.notifications.types}</h3>
        <div className="space-y-4">
          <Row
            title={copy.notifications.risk}
            description={copy.notifications.riskDesc}
            checked={settings.notify_risk_critical}
            onChange={() => handleToggle('notify_risk_critical')}
          />
          <Row
            title={copy.notifications.objective}
            description={copy.notifications.objectiveDesc}
            checked={settings.notify_objective_deadline}
            onChange={() => handleToggle('notify_objective_deadline')}
          />
          <Row
            title={copy.notifications.docs}
            description={copy.notifications.docsDesc}
            checked={settings.notify_document_expiry}
            onChange={() => handleToggle('notify_document_expiry')}
          />
        </div>
      </div>
    </div>
  );
};

const AppearanceSettings = ({ user, onSave, copy }) => {
  const [theme, setTheme] = useState(user?.theme || 'dark');
  const [language, setLanguage] = useState(user?.language || 'es');

  useEffect(() => {
    setTheme(user?.theme || 'dark');
    setLanguage(user?.language || 'es');
  }, [user]);

  const resolveTheme = (nextTheme) => {
    const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    if (nextTheme === 'system') {
      return prefersDark ? 'theme-dark' : 'theme-light';
    }
    return nextTheme === 'light' ? 'theme-light' : 'theme-dark';
  };

  const saveTheme = async (nextTheme) => {
    const root = document.documentElement;
    const beforeClasses = root.className;
    root.classList.remove('theme-light', 'theme-dark');
    root.classList.add(resolveTheme(nextTheme));

    setTheme(nextTheme);
    const result = await onSave({ theme: nextTheme });
    if (!result.success) {
      setTheme(user?.theme || 'dark');
      root.className = beforeClasses;
      toast.error(result.error || copy.alerts.themeError);
      return;
    }

    toast.success(copy.alerts.themeSaved);
  };

  const saveLanguage = async (nextLanguage) => {
    const previous = document.documentElement.lang;
    document.documentElement.lang = nextLanguage;

    setLanguage(nextLanguage);
    const result = await onSave({ language: nextLanguage });
    if (!result.success) {
      setLanguage(user?.language || 'es');
      document.documentElement.lang = previous;
      toast.error(result.error || copy.alerts.languageError);
      return;
    }

    toast.success(copy.alerts.languageSaved);
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-gray-100">{copy.appearance.title}</h2>
        <p className="text-gray-500 mt-1">{copy.appearance.subtitle}</p>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-400 mb-3">{copy.appearance.theme}</label>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {['light', 'dark', 'system'].map((t) => (
            <button
              key={t}
              onClick={() => saveTheme(t)}
              className={`
                p-4 rounded-xl border-2 transition-all duration-200
                ${theme === t
                  ? 'border-primary-500 bg-primary-500/10 shadow-[0_8px_20px_rgba(0,73,144,0.25)]'
                  : 'border-gray-700/50 hover:border-gray-600'
                }
              `}
            >
              <div className={`w-full h-16 rounded-lg mb-3 ${t === 'light' ? 'bg-gray-100' : t === 'dark' ? 'bg-dark-400' : 'bg-gradient-to-r from-gray-100 to-dark-400'}`} />
              <p className="text-sm font-medium text-gray-200 capitalize">
                {t === 'light' ? copy.appearance.light : t === 'dark' ? copy.appearance.dark : copy.appearance.system}
              </p>
            </button>
          ))}
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-400 mb-2">{copy.appearance.language}</label>
        <select value={language} onChange={(e) => saveLanguage(e.target.value)} className="input-glass w-auto min-w-[180px]">
          <option value="es">Espanol</option>
          <option value="en">English</option>
        </select>
        <p className="text-xs text-gray-500 mt-2">{copy.appearance.languageHint}</p>
      </div>
    </div>
  );
};

const SettingsPage = () => {
  const { user, changePassword, updateProfile, mustChangePassword, securityAlert } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();

  const locale = useMemo(() => (user?.language === 'en' ? 'en' : 'es'), [user?.language]);
  const copy = useMemo(() => getCopy(locale), [locale]);

  const initialTab = useMemo(() => {
    if (mustChangePassword) {
      return 'security';
    }

    const tab = searchParams.get('tab');
    const allowed = ['profile', 'security', 'notifications', 'appearance'];
    return allowed.includes(tab) ? tab : 'profile';
  }, [mustChangePassword, searchParams]);

  const [activeTab, setActiveTab] = useState(initialTab);

  useEffect(() => {
    setActiveTab(initialTab);
  }, [initialTab]);

  const switchTab = (tab) => {
    setActiveTab(tab);
    if (mustChangePassword) {
      return;
    }
    setSearchParams({ tab });
  };

  return (
    <div className="space-y-6 animate-fadeIn">
      <div>
        <h1 className="text-2xl font-bold text-gray-100">{copy.pageTitle}</h1>
        <p className="text-gray-500 mt-1">{copy.pageSubtitle}</p>
      </div>

      {mustChangePassword && (
        <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-200">
          {copy.alerts.mustChangePassword}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <div className="lg:col-span-1">
          <div className="glass-card p-4 space-y-2">
            {!mustChangePassword && (
              <Tab active={activeTab === 'profile'} onClick={() => switchTab('profile')} icon={User}>
                {copy.tabs.profile}
              </Tab>
            )}
            <Tab active={activeTab === 'security'} onClick={() => switchTab('security')} icon={Lock}>
              {copy.tabs.security}
            </Tab>
            {!mustChangePassword && (
              <Tab active={activeTab === 'notifications'} onClick={() => switchTab('notifications')} icon={Bell}>
                {copy.tabs.notifications}
              </Tab>
            )}
            {!mustChangePassword && (
              <Tab active={activeTab === 'appearance'} onClick={() => switchTab('appearance')} icon={Palette}>
                {copy.tabs.appearance}
              </Tab>
            )}
          </div>
        </div>

        <div className="lg:col-span-3">
          <div className="glass-card p-6">
            {!mustChangePassword && activeTab === 'profile' && <ProfileSettings user={user} onSave={updateProfile} copy={copy} />}
            {activeTab === 'security' && (
              <SecuritySettings
                changePassword={changePassword}
                mustChangePassword={mustChangePassword}
                securityAlert={securityAlert}
                copy={copy}
              />
            )}
            {!mustChangePassword && activeTab === 'notifications' && <NotificationSettings user={user} onSave={updateProfile} copy={copy} />}
            {!mustChangePassword && activeTab === 'appearance' && <AppearanceSettings user={user} onSave={updateProfile} copy={copy} />}
          </div>
        </div>
      </div>
    </div>
  );
};

export default SettingsPage;
