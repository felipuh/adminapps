import axios from 'axios';

// Base API URL - usa variable de entorno de Vite o el proxy por defecto
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor - handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // If 401 and not already retrying
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
          const response = await axios.post(`${API_BASE_URL}/auth/token/refresh/`, {
            refresh: refreshToken,
          });

          const { access } = response.data;
          localStorage.setItem('access_token', access);

          originalRequest.headers.Authorization = `Bearer ${access}`;
          return api(originalRequest);
        }
      } catch (refreshError) {
        // Refresh failed - logout user
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

export default api;

// ========================================
// Auth Services
// ========================================

export const authService = {
  login: async (email, password) => {
    const response = await api.post('/auth/login/', { email, password });
    return response.data;
  },

  logout: async () => {
    const refreshToken = localStorage.getItem('refresh_token');
    if (refreshToken) {
      try {
        await api.post('/auth/logout/', { refresh: refreshToken });
      } catch (error) {
        console.error('Logout error:', error);
      }
    }
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  },

  getCurrentUser: async () => {
    const response = await api.get('/auth/users/me/');
    return response.data;
  },

  updateProfile: async (data) => {
    const response = await api.patch('/auth/users/me/', data);
    return response.data;
  },

  changePassword: async (currentPassword, newPassword, newPasswordConfirm) => {
    const response = await api.post('/auth/change-password/', {
      current_password: currentPassword,
      new_password: newPassword,
      new_password_confirm: newPasswordConfirm,
    });
    return response.data;
  },
};

// ========================================
// Organization Services
// ========================================

export const organizationService = {
  getAll: async (params = {}) => {
    const response = await api.get('/organizations/', { params });
    return response.data;
  },

  getById: async (id) => {
    const response = await api.get(`/organizations/${id}/`);
    return response.data;
  },

  create: async (data) => {
    const response = await api.post('/organizations/', data);
    return response.data;
  },

  update: async (id, data) => {
    const response = await api.patch(`/organizations/${id}/`, data);
    return response.data;
  },

  delete: async (id) => {
    await api.delete(`/organizations/${id}/`);
  },

  getSettings: async (id) => {
    const response = await api.get(`/organizations/${id}/organization_settings/`);
    return response.data;
  },

  updateSettings: async (id, data) => {
    const response = await api.patch(`/organizations/${id}/organization_settings/`, data);
    return response.data;
  },

  getStats: async (id) => {
    const response = await api.get(`/organizations/${id}/stats/`);
    return response.data;
  },

  getUsers: async (id) => {
    const response = await api.get(`/organizations/${id}/users/`);
    return response.data;
  },
};

// ========================================
// User Services
// ========================================

export const userService = {
  getAll: async (params = {}) => {
    const response = await api.get('/auth/users/', { params });
    return response.data;
  },

  getById: async (id) => {
    const response = await api.get(`/auth/users/${id}/`);
    return response.data;
  },

  create: async (data) => {
    const response = await api.post('/auth/users/', data);
    return response.data;
  },

  update: async (id, data) => {
    const response = await api.patch(`/auth/users/${id}/`, data);
    return response.data;
  },

  delete: async (id) => {
    await api.delete(`/auth/users/${id}/`);
  },

  getSessions: async (id) => {
    const response = await api.get(`/auth/users/${id}/sessions/`);
    return response.data;
  },

  getActivityLogs: async (id, params = {}) => {
    const response = await api.get(`/auth/users/${id}/activity/`, { params });
    return response.data;
  },
};

// ========================================
// Subscription Services
// ========================================

export const subscriptionService = {
  getPlans: async () => {
    const response = await api.get('/subscriptions/plans/');
    return response.data;
  },

  getAll: async (params = {}) => {
    const response = await api.get('/subscriptions/', { params });
    return response.data;
  },

  getById: async (id) => {
    const response = await api.get(`/subscriptions/${id}/`);
    return response.data;
  },

  create: async (data) => {
    const response = await api.post('/subscriptions/', data);
    return response.data;
  },

  update: async (id, data) => {
    const response = await api.patch(`/subscriptions/${id}/`, data);
    return response.data;
  },

  cancel: async (id) => {
    const response = await api.post(`/subscriptions/${id}/cancel/`);
    return response.data;
  },

  getInvoices: async (subscriptionId) => {
    const response = await api.get(`/subscriptions/${subscriptionId}/invoices/`);
    return response.data;
  },
};

// ========================================
// Dashboard Services
// ========================================

export const dashboardService = {
  getStats: async () => {
    const response = await api.get('/dashboard/');
    return response.data;
  },

  getRecentActivity: async (limit = 10) => {
    const response = await api.get('/dashboard/activity/', { params: { limit } });
    return response.data;
  },

  getOrganizationGrowth: async (period = '30d') => {
    const response = await api.get('/dashboard/growth/', { params: { period } });
    return response.data;
  },
};
// ========================================
// Products/Modules Services
// ========================================

export const moduleService = {
  getByOrganization: async (organizationId) => {
    if (!organizationId) {
      throw new Error('organizationId is required');
    }
    const response = await api.get('/products/modules/by_organization/', { params: { organization_id: organizationId } });
    return response.data;
  },

  getAll: async (params = {}) => {
    const response = await api.get('/products/modules/', { params });
    return response.data;
  },

  getById: async (id) => {
    const response = await api.get(`/products/modules/${id}/`);
    return response.data;
  },

  create: async (data) => {
    const response = await api.post('/products/modules/', data);
    return response.data;
  },

  toggle: async (id, data) => {
    const response = await api.post(`/products/modules/${id}/toggle/`, data);
    return response.data;
  },

  bulkAssign: async (data) => {
    const response = await api.post('/products/modules/bulk_assign/', data);
    return response.data;
  },
};