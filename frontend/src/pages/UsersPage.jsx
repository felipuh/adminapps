import React, { useState, useEffect } from 'react';
import { 
  Users, 
  Plus, 
  Search, 
  MoreVertical,
  Eye,
  Edit,
  Trash2,
  Mail,
  Shield,
  X
} from 'lucide-react';
import { userService } from '../services/api';
import toast from 'react-hot-toast';

const UserRow = ({ user, onView, onEdit, onDelete }) => {
  const [menuOpen, setMenuOpen] = useState(false);

  const roleLabels = {
    superadmin: 'Super Admin',
    admin: 'Administrador',
    org_admin: 'Admin Org',
    iso_manager: 'Gestor ISO',
    auditor: 'Auditor',
    user: 'Usuario',
    viewer: 'Visualizador',
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
          {user.is_active ? 'Activo' : 'Inactivo'}
        </span>
      </td>
      <td className="px-4 py-4 text-sm text-gray-400">
        {user.last_login_at 
          ? new Date(user.last_login_at).toLocaleDateString('es-MX')
          : 'Nunca'
        }
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
                  onClick={() => { onView(user); setMenuOpen(false); }}
                  className="w-full flex items-center gap-3 px-4 py-3 text-sm text-gray-300 hover:bg-dark-300 transition-colors"
                >
                  <Eye className="w-4 h-4" />
                  Ver perfil
                </button>
                <button
                  onClick={() => { onEdit(user); setMenuOpen(false); }}
                  className="w-full flex items-center gap-3 px-4 py-3 text-sm text-gray-300 hover:bg-dark-300 transition-colors"
                >
                  <Edit className="w-4 h-4" />
                  Editar
                </button>
                <button
                  onClick={() => { onDelete(user); setMenuOpen(false); }}
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

// Create/Edit User Modal
const UserModal = ({ isOpen, onClose, user, onSave }) => {
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
      toast.error('Las contraseñas no coinciden');
      return;
    }
    
    setLoading(true);
    
    try {
      if (user) {
        const { password, password_confirm, ...updateData } = formData;
        await userService.update(user.id, updateData);
        toast.success('Usuario actualizado correctamente');
      } else {
        await userService.create(formData);
        toast.success('Usuario creado correctamente');
      }
      onSave();
      onClose();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al guardar el usuario');
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
            {user ? 'Editar Usuario' : 'Nuevo Usuario'}
          </h2>
          <button onClick={onClose} className="p-2 rounded-lg hover:bg-dark-300 text-gray-400">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">Nombre *</label>
              <input
                type="text"
                value={formData.first_name}
                onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                className="input-glass"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">Apellido *</label>
              <input
                type="text"
                value={formData.last_name}
                onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                className="input-glass"
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">Email *</label>
            <input
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              className="input-glass"
              required
              disabled={!!user}
            />
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
              <label className="block text-sm font-medium text-gray-400 mb-2">Rol *</label>
              <select
                value={formData.role}
                onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                className="input-glass"
              >
                <option value="viewer">Visualizador</option>
                <option value="user">Usuario</option>
                <option value="auditor">Auditor</option>
                <option value="iso_manager">Gestor ISO</option>
                <option value="org_admin">Admin Organización</option>
                <option value="admin">Administrador</option>
                <option value="superadmin">Super Admin</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">Cargo</label>
              <input
                type="text"
                value={formData.job_title}
                onChange={(e) => setFormData({ ...formData, job_title: e.target.value })}
                className="input-glass"
              />
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
          </div>

          {!user && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-2">Contraseña *</label>
                <input
                  type="password"
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  className="input-glass"
                  required={!user}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-2">Confirmar Contraseña *</label>
                <input
                  type="password"
                  value={formData.password_confirm}
                  onChange={(e) => setFormData({ ...formData, password_confirm: e.target.value })}
                  className="input-glass"
                  required={!user}
                />
              </div>
            </div>
          )}

          <div className="flex justify-end gap-3 pt-4">
            <button type="button" onClick={onClose} className="btn-secondary">
              Cancelar
            </button>
            <button type="submit" disabled={loading} className="btn-primary">
              {loading ? 'Guardando...' : (user ? 'Actualizar' : 'Crear')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

const UsersPage = () => {
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
    toast.success(`Ver perfil de ${user.first_name}`);
  };

  const handleEdit = (user) => {
    setSelectedUser(user);
    setModalOpen(true);
  };

  const handleDelete = async (user) => {
    if (window.confirm(`¿Estás seguro de eliminar a "${user.first_name} ${user.last_name}"?`)) {
      try {
        await userService.delete(user.id);
        toast.success('Usuario eliminado');
        fetchUsers();
      } catch (error) {
        toast.error('Error al eliminar el usuario');
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
          <h1 className="text-2xl font-bold text-gray-100">Usuarios</h1>
          <p className="text-gray-500 mt-1">Gestiona los usuarios del sistema</p>
        </div>
        <button onClick={handleCreate} className="btn-primary flex items-center gap-2">
          <Plus className="w-5 h-5" />
          Nuevo Usuario
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
              placeholder="Buscar usuarios..."
              className="input-glass pl-11"
            />
          </div>
          <select
            value={roleFilter}
            onChange={(e) => setRoleFilter(e.target.value)}
            className="input-glass w-auto"
          >
            <option value="">Todos los roles</option>
            <option value="superadmin">Super Admin</option>
            <option value="admin">Administrador</option>
            <option value="org_admin">Admin Org</option>
            <option value="iso_manager">Gestor ISO</option>
            <option value="auditor">Auditor</option>
            <option value="user">Usuario</option>
            <option value="viewer">Visualizador</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="glass-card overflow-hidden">
        {loading ? (
          <div className="p-8 text-center">
            <div className="w-8 h-8 border-2 border-primary-500 border-t-transparent rounded-full animate-spin mx-auto" />
            <p className="text-gray-500 mt-4">Cargando usuarios...</p>
          </div>
        ) : users.length === 0 ? (
          <div className="p-8 text-center">
            <Users className="w-12 h-12 text-gray-600 mx-auto mb-4" />
            <p className="text-gray-400">No se encontraron usuarios</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="table-glass">
              <thead>
                <tr>
                  <th>Usuario</th>
                  <th>Organización</th>
                  <th>Rol</th>
                  <th>Estado</th>
                  <th>Último Acceso</th>
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
      />
    </div>
  );
};

export default UsersPage;
