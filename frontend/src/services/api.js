import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Interceptor para agregar token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Interceptor para manejar errores y refresh token
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true
      
      const refreshToken = localStorage.getItem('refresh_token')
      if (refreshToken) {
        try {
          const response = await axios.post('/api/auth/refresh/', {
            refresh: refreshToken
          })
          
          const { access } = response.data
          localStorage.setItem('access_token', access)
          api.defaults.headers.common['Authorization'] = `Bearer ${access}`
          originalRequest.headers['Authorization'] = `Bearer ${access}`
          
          return api(originalRequest)
        } catch (refreshError) {
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          window.location.href = '/login'
        }
      }
    }
    
    return Promise.reject(error)
  }
)

export default api

// Servicios específicos
export const dashboardService = {
  getDashboard: () => api.get('/dashboard/'),
  getStats: () => api.get('/stats/'),
}

export const organizationService = {
  getAll: (params) => api.get('/organizations/', { params }),
  getById: (id) => api.get(`/organizations/${id}/`),
  create: (data) => api.post('/organizations/', data),
  update: (id, data) => api.patch(`/organizations/${id}/`, data),
  delete: (id) => api.delete(`/organizations/${id}/`),
  getStats: (id) => api.get(`/organizations/${id}/stats/`),
  activate: (id) => api.post(`/organizations/${id}/activate/`),
  suspend: (id) => api.post(`/organizations/${id}/suspend/`),
}

export const isoStandardService = {
  getAll: (params) => api.get('/products/iso-standards/', { params }),
  getById: (id) => api.get(`/products/iso-standards/${id}/`),
  create: (data) => api.post('/products/iso-standards/', data),
  update: (id, data) => api.patch(`/products/iso-standards/${id}/`, data),
  getActive: () => api.get('/products/iso-standards/active/'),
}

export const moduleService = {
  getAll: (params) => api.get('/products/modules/', { params }),
  getById: (id) => api.get(`/products/modules/${id}/`),
  create: (data) => api.post('/products/modules/', data),
  toggle: (id, action, reason = '') => api.post(`/products/modules/${id}/toggle/`, { action, reason }),
  getByOrganization: (orgId) => api.get('/products/modules/by_organization/', { params: { organization_id: orgId } }),
  bulkAssign: (data) => api.post('/products/modules/bulk_assign/', data),
}

export const activityService = {
  getLogs: (params) => api.get('/products/module-logs/', { params }),
}
