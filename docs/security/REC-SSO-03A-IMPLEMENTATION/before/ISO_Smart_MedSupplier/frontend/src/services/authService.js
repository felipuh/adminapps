/**
 * Servicio de Autenticación
 */
import api from './api';

const authService = {
  // Login
  login: async (email, password, organizationId = null) => {
    const payload = { email, password };
    if (organizationId) {
      payload.organization_id = organizationId;
    }
    const response = await api.post('/auth/login/', payload);
    return response.data;
  },

  // Logout
  logout: async () => {
    const refresh = localStorage.getItem('refresh_token');
    if (refresh) {
      try {
        await api.post('/auth/logout/', { refresh });
      } catch (error) {
        console.error('Error en logout:', error);
      }
    }
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  },

  // Refresh token
  refreshToken: async () => {
    const refresh = localStorage.getItem('refresh_token');
    if (!refresh) return null;
    
    const response = await api.post('/auth/refresh/', { refresh });
    return response.data;
  },

  // Obtener usuario actual
  getMe: async () => {
    const response = await api.get('/auth/me/');
    return response.data;
  },

  // Cambiar organización
  switchOrganization: async (organizationId) => {
    const response = await api.post('/auth/switch-organization/', {
      organization_id: organizationId,
    });
    return response.data;
  },

  // Cambiar contraseña
  changePassword: async (currentPassword, newPassword, confirmPassword) => {
    const response = await api.post('/auth/change-password/', {
      current_password: currentPassword,
      new_password: newPassword,
      confirm_password: confirmPassword,
    });
    return response.data;
  },

  // Obtener usuarios de la organización (admin only)
  getUsers: async () => {
    const response = await api.get('/auth/users/');
    return response.data.results || response.data;
  },

  // Crear usuario (admin only)
  createUser: async (data) => {
    const response = await api.post('/auth/users/', data);
    return response.data;
  },

  // Actualizar usuario (admin only)
  updateUser: async (id, data) => {
    const response = await api.put(`/auth/users/${id}/`, data);
    return response.data;
  },

  // Eliminar usuario (admin only)
  deleteUser: async (id) => {
    const response = await api.delete(`/auth/users/${id}/`);
    return response.data;
  },

  // Verificar si está autenticado
  isAuthenticated: () => {
    return !!localStorage.getItem('access_token');
  }
};

export default authService;
