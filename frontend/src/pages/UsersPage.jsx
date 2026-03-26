import React, { useState, useEffect } from 'react';
import { 
  Users, 
  Plus, 
  Search, 
  Eye,
  Edit,
  Trash2,
  Mail,
  Shield,
  X
} from 'lucide-react';
import { userService } from '../services/api';
import toast from 'react-hot-toast';
import { useAuth } from '../contexts/AuthContext';

const UserRow = ({ user, onView, onEdit, onDelete, isEnglish, t }) => {
  const roleLabels = {
    superadmin: 'Super Admin',
    admin: isEnglish ? 'Administrator' : 'Administrador',
    org_admin: 'Admin Org',
    iso_manager: isEnglish ? 'ISO Manager' : 'Gestor ISO',
    auditor: isEnglish ? 'Auditor' : 'Auditor',
    user: isEnglish ? 'User' : 'Usuario',
    viewer: isEnglish ? 'Viewer' : 'Visualizador',
  };

  const roleColors = {
    superadmin: 'badge-danger',
    admin: 'badge-warning',
    org_admin: 'badge-info',
    iso_manager: 'badge-success',
    auditor: 'badge-neutral',
    user: 'badge-neutral',
    viewer: 'badge-neutral',
  };

  return (
    <tr className="border-b border-gray-700/30 hover:bg-dark-300/30 transition-colors">
      <td className="px-4 py-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary-400 to-primary-600 flex items-center justify-center text-white text-sm font-semibold flex-shrink-0">
            {user.first_name?.[0]}{user.last_name?.[0]}
          </div>
          <div>
            <p className="font-medium text-gray-200">{user.first_name} {user.last_name}</p>
            <p className="text-xs text-gray-500">{user.email}</p>
          </div>
        </div>
      </td>
      <td className="px-4 py-4 text-sm text-gray-400">{user.organization_name || '-'}</td>
      <td className="px-4 py-4">
        <span className={roleColors[user.role]}>{roleLabels[user.role]}</span>
      </td>
      <td className="px-4 py-4">
        <span className={user.is_active ? 'badge-success' : 'badge-danger'}>
          {user.is_active ? t.active : t.inactive}
        </span>
      </td>
      <td className="px-4 py-4 text-sm text-gray-400">
        {user.last_login_at 
          ? new Date(user.last_login_at).toLocaleDateString(isEnglish ? 'en-US' : 'es-MX')
          : t.never
        }
      </td>
      <td className="px-4 py-4">
        <div className="flex items-center gap-2 whitespace-nowrap">
          <button
            onClick={() => onView(user)}
            className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs text-gray-200 hover:bg-dark-200 transition-colors"
          >
            <Eye className="w-3.5 h-3.5" />
            {t.viewProfile}
          </button>
          <button
            onClick={() => onEdit(user)}
            className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs text-gray-200 hover:bg-dark-200 transition-colors"
          >
            <Edit className="w-3.5 h-3.5" />
            {t.edit}
          </button>
          <button
            onClick={() => onDelete(user)}
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

// Create/Edit User Modal
const UserModal = ({ isOpen, onClose, user, onSave, isEnglish, t }) => {
  const [formData, setFormData] = useState({
    email: '',
    first_name: '',
    last_name: '',
    phone: '',
    role: 'user',
    job_title: '',
    department: '',
    password: '',
    password_confirm: '',
  });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (user) {
      setFormData({
        email: user.email || '',
        first_name: user.first_name || '',
        last_name: user.last_name || '',
        phone: user.phone || '',
        role: user.role || 'user',
        job_title: user.job_title || '',
        department: user.department || '',
        password: '',
        password_confirm: '',
      });
    } else {
      setFormData({
        email: '',
        first_name: '',
        last_name: '',
        phone: '',
        role: 'user',
        job_title: '',
        department: '',
        password: '',
        password_confirm: '',
      });
    }
  }, [user]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!user && formData.password !== formData.password_confirm) {
      toast.error(t.passwordMismatch);
      return;
    }
    
    setLoading(true);
    
    try {
      if (user) {
        const { password, password_confirm, ...updateData } = formData;
        await userService.update(user.id, updateData);
        toast.success(t.userUpdated);
      } else {
        await userService.create(formData);
        toast.success(t.userCreated);
      }
      onSave();
      onClose();
    } catch (error) {
      toast.error(error.response?.data?.detail || t.userSaveError);
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
              <p className="text-xs uppercase tracking-[0.2em] text-primary-300">{isEnglish ? 'User form' : 'Formulario usuario'}</p>
              <h2 className="mt-1 text-xl font-semibold text-gray-100">{user ? t.editUser : t.newUser}</h2>
              <p className="mt-1 text-sm text-gray-500">{isEnglish ? 'Define identity, role and access information.' : 'Define identidad, rol e informacion de acceso.'}</p>
            </div>
            <button onClick={onClose} className="rounded-lg p-2 text-gray-400 hover:bg-dark-300 hover:text-gray-200 transition-colors">
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="flex h-[calc(100%-78px)] md:h-auto md:max-h-[calc(90vh-88px)] flex-col">
          <div className="flex-1 overflow-y-auto px-5 py-5 md:px-6 md:py-6 space-y-6">
            <div className="rounded-xl border border-gray-700/50 bg-dark-400/25 p-4 md:p-5">
              <p className="mb-4 text-xs font-semibold uppercase tracking-widest text-gray-500">{isEnglish ? 'Personal data' : 'Datos personales'}</p>
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <div>
                  <label className="mb-1.5 block text-sm font-medium text-gray-400">{t.firstName} *</label>
                  <input
                    type="text"
                    value={formData.first_name}
                    onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                    className="input-glass"
                    required
                  />
                </div>
                <div>
                  <label className="mb-1.5 block text-sm font-medium text-gray-400">{t.lastName} *</label>
                  <input
                    type="text"
                    value={formData.last_name}
                    onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                    className="input-glass"
                    required
                  />
                </div>
                <div className="md:col-span-2">
                  <label className="mb-1.5 block text-sm font-medium text-gray-400">Email *</label>
                  <input
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    className="input-glass"
                    required
                    disabled={!!user}
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
                <div>
                  <label className="mb-1.5 block text-sm font-medium text-gray-400">{t.jobTitle}</label>
                  <input
                    type="text"
                    value={formData.job_title}
                    onChange={(e) => setFormData({ ...formData, job_title: e.target.value })}
                    className="input-glass"
                  />
                </div>
              </div>
            </div>

            <div className="rounded-xl border border-gray-700/50 bg-dark-400/25 p-4 md:p-5">
              <p className="mb-4 text-xs font-semibold uppercase tracking-widest text-gray-500">{isEnglish ? 'Permissions' : 'Permisos'}</p>
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <div>
                  <label className="mb-1.5 block text-sm font-medium text-gray-400">{t.role} *</label>
                  <select
                    value={formData.role}
                    onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                    className="input-glass"
                  >
                    <option value="viewer">{isEnglish ? 'Viewer' : 'Visualizador'}</option>
                    <option value="user">{isEnglish ? 'User' : 'Usuario'}</option>
                    <option value="auditor">Auditor</option>
                    <option value="iso_manager">{isEnglish ? 'ISO Manager' : 'Gestor ISO'}</option>
                    <option value="org_admin">{isEnglish ? 'Org Admin' : 'Admin Organizacion'}</option>
                    <option value="admin">{isEnglish ? 'Administrator' : 'Administrador'}</option>
                    <option value="superadmin">Super Admin</option>
                  </select>
                </div>
                <div>
                  <label className="mb-1.5 block text-sm font-medium text-gray-400">{t.department}</label>
                  <input
                    type="text"
                    value={formData.department}
                    onChange={(e) => setFormData({ ...formData, department: e.target.value })}
                    className="input-glass"
                  />
                </div>
              </div>
            </div>

            {!user && (
              <div className="rounded-xl border border-gray-700/50 bg-dark-400/25 p-4 md:p-5">
                <p className="mb-4 text-xs font-semibold uppercase tracking-widest text-gray-500">{isEnglish ? 'Credentials' : 'Credenciales'}</p>
                <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                  <div>
                    <label className="mb-1.5 block text-sm font-medium text-gray-400">{t.password} *</label>
                    <input
                      type="password"
                      value={formData.password}
                      onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                      className="input-glass"
                      required={!user}
                    />
                  </div>
                  <div>
                    <label className="mb-1.5 block text-sm font-medium text-gray-400">{t.confirmPassword} *</label>
                    <input
                      type="password"
                      value={formData.password_confirm}
                      onChange={(e) => setFormData({ ...formData, password_confirm: e.target.value })}
                      className="input-glass"
                      required={!user}
                    />
                  </div>
                </div>
              </div>
            )}
          </div>

          <div className="border-t border-gray-700/50 bg-dark-400/20 px-5 py-4 md:px-6">
            <div className="flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
              <button type="button" onClick={onClose} className="btn-secondary w-full sm:w-auto">
                {t.cancel}
              </button>
              <button type="submit" disabled={loading} className="btn-primary w-full sm:w-auto">
                {loading ? t.saving : (user ? t.update : t.create)}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
};

const UsersPage = () => {
  const { user: authUser } = useAuth();
  const isEnglish = authUser?.language === 'en';
  const t = {
    active: isEnglish ? 'Active' : 'Activo',
    inactive: isEnglish ? 'Inactive' : 'Inactivo',
    never: isEnglish ? 'Never' : 'Nunca',
    viewProfile: isEnglish ? 'View profile' : 'Ver perfil',
    edit: isEnglish ? 'Edit' : 'Editar',
    delete: isEnglish ? 'Delete' : 'Eliminar',
    passwordMismatch: isEnglish ? 'Passwords do not match' : 'Las contrasenas no coinciden',
    userUpdated: isEnglish ? 'User updated successfully' : 'Usuario actualizado correctamente',
    userCreated: isEnglish ? 'User created successfully' : 'Usuario creado correctamente',
    userSaveError: isEnglish ? 'Error saving user' : 'Error al guardar el usuario',
    editUser: isEnglish ? 'Edit User' : 'Editar Usuario',
    newUser: isEnglish ? 'New User' : 'Nuevo Usuario',
    firstName: isEnglish ? 'First Name' : 'Nombre',
    lastName: isEnglish ? 'Last Name' : 'Apellido',
    phone: isEnglish ? 'Phone' : 'Telefono',
    role: isEnglish ? 'Role' : 'Rol',
    jobTitle: isEnglish ? 'Job Title' : 'Cargo',
    department: isEnglish ? 'Department' : 'Departamento',
    password: isEnglish ? 'Password' : 'Contrasena',
    confirmPassword: isEnglish ? 'Confirm Password' : 'Confirmar Contrasena',
    cancel: isEnglish ? 'Cancel' : 'Cancelar',
    saving: isEnglish ? 'Saving...' : 'Guardando...',
    update: isEnglish ? 'Update' : 'Actualizar',
    create: isEnglish ? 'Create' : 'Crear',
    confirmDelete: isEnglish ? 'Are you sure you want to delete' : 'Estas seguro de eliminar a',
    userDeleted: isEnglish ? 'User deleted' : 'Usuario eliminado',
    userDeleteError: isEnglish ? 'Error deleting user' : 'Error al eliminar el usuario',
    profileToast: isEnglish ? 'Viewing profile of' : 'Ver perfil de',
    pageTitle: isEnglish ? 'Users' : 'Usuarios',
    pageSubtitle: isEnglish ? 'Manage system users' : 'Gestiona los usuarios del sistema',
    newUserBtn: isEnglish ? 'New User' : 'Nuevo Usuario',
    searchPlaceholder: isEnglish ? 'Search users...' : 'Buscar usuarios...',
    allRoles: isEnglish ? 'All roles' : 'Todos los roles',
    admin: isEnglish ? 'Administrator' : 'Administrador',
    viewer: isEnglish ? 'Viewer' : 'Visualizador',
    org: isEnglish ? 'Organization' : 'Organizacion',
    status: isEnglish ? 'Status' : 'Estado',
    lastAccess: isEnglish ? 'Last Access' : 'Ultimo Acceso',
    loadingUsers: isEnglish ? 'Loading users...' : 'Cargando usuarios...',
    noUsers: isEnglish ? 'No users found' : 'No se encontraron usuarios',
    userLabel: isEnglish ? 'User' : 'Usuario',
  };
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState('');
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);

  const fetchUsers = async () => {
    try {
      const params = {};
      if (search) params.search = search;
      if (roleFilter) params.role = roleFilter;
      
      const data = await userService.getAll(params);
      setUsers(data.results || data);
    } catch (error) {
      // Mock data
      setUsers([
        { id: '1', email: 'admin@comtech.com', first_name: 'Admin', last_name: 'Comtech', role: 'superadmin', is_active: true, organization_name: null, last_login_at: '2026-02-04T10:00:00Z' },
        { id: '2', email: 'juan@techcorp.com', first_name: 'Juan', last_name: 'Pérez', role: 'org_admin', is_active: true, organization_name: 'Tech Corp', last_login_at: '2026-02-03T15:30:00Z' },
        { id: '3', email: 'maria@acme.com', first_name: 'María', last_name: 'García', role: 'iso_manager', is_active: true, organization_name: 'Acme Inc', last_login_at: '2026-02-02T09:00:00Z' },
        { id: '4', email: 'carlos@startup.io', first_name: 'Carlos', last_name: 'López', role: 'user', is_active: true, organization_name: 'StartupXYZ', last_login_at: null },
        { id: '5', email: 'ana@global.com', first_name: 'Ana', last_name: 'Martínez', role: 'auditor', is_active: false, organization_name: 'Global Services', last_login_at: '2026-01-15T12:00:00Z' },
      ]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, [search, roleFilter]);

  const handleView = (user) => {
    toast.success(`${t.profileToast} ${user.first_name}`);
  };

  const handleEdit = (user) => {
    setSelectedUser(user);
    setModalOpen(true);
  };

  const handleDelete = async (user) => {
    if (window.confirm(`${t.confirmDelete} "${user.first_name} ${user.last_name}"?`)) {
      try {
        await userService.delete(user.id);
        toast.success(t.userDeleted);
        fetchUsers();
      } catch (error) {
        toast.error(t.userDeleteError);
      }
    }
  };

  const handleCreate = () => {
    setSelectedUser(null);
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
          {t.newUserBtn}
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
          <select
            value={roleFilter}
            onChange={(e) => setRoleFilter(e.target.value)}
            className="input-glass w-auto"
          >
            <option value="">{t.allRoles}</option>
            <option value="superadmin">Super Admin</option>
            <option value="admin">{t.admin}</option>
            <option value="org_admin">Admin Org</option>
            <option value="iso_manager">{isEnglish ? 'ISO Manager' : 'Gestor ISO'}</option>
            <option value="auditor">Auditor</option>
            <option value="user">{isEnglish ? 'User' : 'Usuario'}</option>
            <option value="viewer">{t.viewer}</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="glass-card overflow-hidden">
        {loading ? (
          <div className="p-8 text-center">
            <div className="w-8 h-8 border-2 border-primary-500 border-t-transparent rounded-full animate-spin mx-auto" />
            <p className="text-gray-500 mt-4">{t.loadingUsers}</p>
          </div>
        ) : users.length === 0 ? (
          <div className="p-8 text-center">
            <Users className="w-12 h-12 text-gray-600 mx-auto mb-4" />
            <p className="text-gray-400">{t.noUsers}</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="table-glass">
              <thead>
                <tr>
                  <th>{t.userLabel}</th>
                  <th>{t.org}</th>
                  <th>{t.role}</th>
                  <th>{t.status}</th>
                  <th>{t.lastAccess}</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {users.map((user) => (
                  <UserRow
                    key={user.id}
                    user={user}
                    onView={handleView}
                    onEdit={handleEdit}
                    onDelete={handleDelete}
                    isEnglish={isEnglish}
                    t={t}
                  />
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Modal */}
      <UserModal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        user={selectedUser}
        onSave={fetchUsers}
        isEnglish={isEnglish}
        t={t}
      />
    </div>
  );
};

export default UsersPage;
