/**
 * AuthContext - Contexto de Autenticación para ISO Smart
 * Maneja el estado de autenticación, tokens JWT y usuario actual
 */

/* eslint-disable react-refresh/only-export-components */

import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import api from '../services/api';
import { useI18n } from './I18nContext';

const getTokenPayload = (token) => {
  if (!token) return null;
  const parts = token.split('.');
  if (parts.length !== 3) return null;
  try {
    const payload = parts[1].replace(/-/g, '+').replace(/_/g, '/');
    const decoded = atob(payload);
    return JSON.parse(decoded);
  } catch {
    return null;
  }
};

const isTokenExpired = (token) => {
  const payload = getTokenPayload(token);
  if (!payload || !payload.exp) return true;
  const nowSeconds = Math.floor(Date.now() / 1000);
  return payload.exp <= nowSeconds;
};

const clearOnboardingSessionFlags = () => {
  if (typeof window === 'undefined') {
    return;
  }

  Object.keys(window.sessionStorage)
    .filter((key) => key.startsWith('isosmart_onboarding_seen_'))
    .forEach((key) => window.sessionStorage.removeItem(key));
};

const AuthContext = createContext(null);
const localAuthBypassEnabled = import.meta.env.VITE_LOCAL_AUTH_BYPASS === '1';

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth debe ser usado dentro de AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const { t } = useI18n();
  const [user, setUser] = useState(null);
  const [profile, setProfile] = useState(null);
  const [organizations, setOrganizations] = useState([]);
  const [currentOrganization, setCurrentOrganization] = useState(null);
  const [securityAlert, setSecurityAlert] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const mustChangePassword = Boolean(user?.must_change_password);

  // Verificar autenticación al cargar
  useEffect(() => {
    checkAuth();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const loadCurrentUser = async () => {
    const response = await api.get('/auth/me/');

    setUser(response.data.user);
    setProfile(response.data.profile);
    setOrganizations(response.data.organizations || []);

    const current = response.data.organizations?.find(org => org.is_current);
    setCurrentOrganization(current || response.data.organizations?.[0]);

    setIsAuthenticated(true);
  };

  // Verificar token existente
  const checkAuth = async () => {
    if (window.location.pathname === '/login') {
      setLoading(false);
      return;
    }

    const token = localStorage.getItem('access_token');
    const refreshTokenValue = localStorage.getItem('refresh_token');
    
    if (!token) {
      setLoading(false);
      return;
    }

    if (!refreshTokenValue || isTokenExpired(refreshTokenValue)) {
      clearAuth();
      setLoading(false);
      return;
    }

    try {
      if (token && isTokenExpired(token)) {
        localStorage.removeItem('access_token');
      } else if (token) {
        api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      }

      const refreshed = await refreshToken({ reloadUser: true });
      if (!refreshed) {
        clearAuth();
      }
    } catch (error) {
      console.error('Error verificando autenticación:', error);
      clearAuth();
    } finally {
      setLoading(false);
    }
  };

  // Login
  const login = async (email, password, organizationId = null) => {
    try {
      const normalizedEmail = String(email || '').trim().toLowerCase();
      const payload = { email: normalizedEmail, password };
      if (organizationId) {
        payload.organization_id = organizationId;
      }

      const response = await api.post('/auth/login/', payload, {
        headers: localAuthBypassEnabled ? { 'X-ISO-LOCAL-AUTH-BYPASS': '1' } : undefined,
      });
      const { access, refresh, user: userData, profile: profileData, organizations: orgs } = response.data;

      // Guardar tokens
      localStorage.setItem('access_token', access);
      localStorage.setItem('refresh_token', refresh);
      api.defaults.headers.common['Authorization'] = `Bearer ${access}`;

      // Actualizar estado
      setUser(userData);
      setProfile(profileData);
      setOrganizations(orgs || []);
      setSecurityAlert(response.data.security_alert || null);
      
      const current = orgs?.find(org => org.is_current);
      setCurrentOrganization(current || orgs?.[0]);
      
      setIsAuthenticated(true);

      return {
        success: true,
        mustChangePassword: Boolean(userData?.must_change_password),
        securityAlert: response.data.security_alert || null,
      };
    } catch (error) {
      const statusCode = error?.response?.status;
      if (statusCode && (statusCode === 400 || statusCode === 401)) {
        console.warn('Login rechazado por credenciales o autorización.');
      } else {
        console.error('Error de login:', error);
      }

      const responseData = error.response?.data;
      const backendMessage =
        responseData?.detail ||
        responseData?.non_field_errors?.[0] ||
        responseData?.email?.[0] ||
        responseData?.password?.[0] ||
        null;

      const networkMessage = !error.response
        ? t('auth.errors.connectionFailed')
        : null;

      return {
        success: false,
        error: backendMessage || networkMessage || t('auth.errors.loginFailed'),
      };
    }
  };

  // Logout
  const logout = async () => {
    try {
      const refresh = localStorage.getItem('refresh_token');
      if (refresh) {
        await api.post('/auth/logout/', { refresh });
      }
    } catch (error) {
      console.error('Error en logout:', error);
    } finally {
      clearAuth();
    }
  };

  // Limpiar autenticación
  const clearAuth = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    clearOnboardingSessionFlags();
    delete api.defaults.headers.common['Authorization'];
    setUser(null);
    setProfile(null);
    setOrganizations([]);
    setCurrentOrganization(null);
    setSecurityAlert(null);
    setIsAuthenticated(false);
  };

  // Refresh token
  const refreshToken = async ({ reloadUser = true } = {}) => {
    const refresh = localStorage.getItem('refresh_token');
    
    if (!refresh) {
      return false;
    }

    if (isTokenExpired(refresh)) {
      clearAuth();
      return false;
    }

    try {
      const response = await api.post('/auth/refresh/', { refresh });
      const { access, refresh: newRefresh } = response.data;

      localStorage.setItem('access_token', access);
      if (newRefresh) {
        localStorage.setItem('refresh_token', newRefresh);
      }
      api.defaults.headers.common['Authorization'] = `Bearer ${access}`;

      if (reloadUser) {
        await loadCurrentUser();
      }
      return true;
    } catch (error) {
      console.error('Error refrescando token:', error);
      return false;
    }
  };

  // Cambiar organización
  const switchOrganization = async (organizationId) => {
    try {
      const response = await api.post('/auth/switch-organization/', {
        organization_id: organizationId,
      });

      const { access, refresh, profile: profileData, organizations: orgs } = response.data;

      // Actualizar tokens
      localStorage.setItem('access_token', access);
      localStorage.setItem('refresh_token', refresh);
      api.defaults.headers.common['Authorization'] = `Bearer ${access}`;

      // Actualizar estado
      setProfile(profileData);
      setOrganizations(orgs || []);
      
      const current = orgs?.find(org => org.is_current);
      setCurrentOrganization(current || orgs?.[0]);

      return { success: true };
    } catch (error) {
      console.error('Error cambiando organización:', error);
      return {
        success: false,
        error: error.response?.data?.detail || t('auth.errors.switchOrganizationFailed'),
      };
    }
  };

  // Cambiar contraseña
  const changePassword = async (currentPassword, newPassword, confirmPassword) => {
    try {
      await api.post('/auth/change-password/', {
        current_password: currentPassword,
        new_password: newPassword,
        confirm_password: confirmPassword,
      });
      setUser((currentUser) => (
        currentUser
          ? { ...currentUser, must_change_password: false }
          : currentUser
      ));
      setSecurityAlert(null);
      return { success: true };
    } catch (error) {
      console.error('Error cambiando contraseña:', error);
      return {
        success: false,
        error: error.response?.data?.detail || 
               error.response?.data?.current_password?.[0] ||
               error.response?.data?.new_password?.[0] ||
               t('auth.errors.changePasswordFailed'),
      };
    }
  };

  const requestPasswordReset = async (email) => {
    try {
      await api.post('/auth/password-reset/request/', {
        email: String(email || '').trim().toLowerCase(),
      });
      return {
        success: true,
        message: t('auth.passwordReset.request.messages.success'),
      };
    } catch (error) {
      console.error('Error solicitando recuperación de contraseña:', error);
      return {
        success: false,
        error: error.response?.data?.detail || t('auth.passwordReset.request.messages.error'),
      };
    }
  };

  const confirmPasswordReset = async (selector, token, newPassword, confirmPassword) => {
    try {
      await api.post('/auth/password-reset/confirm/', {
        selector,
        token,
        new_password: newPassword,
        confirm_password: confirmPassword,
      });
      return {
        success: true,
        message: t('auth.passwordReset.confirm.messages.success'),
      };
    } catch (error) {
      console.error('Error confirmando recuperación de contraseña:', error);
      return {
        success: false,
        error:
          error.response?.data?.token?.[0] ||
          error.response?.data?.new_password?.[0] ||
          error.response?.data?.confirm_password?.[0] ||
          error.response?.data?.detail ||
          t('auth.passwordReset.confirm.messages.error'),
      };
    }
  };

  // Helpers de permisos
  const hasRole = useCallback((roles) => {
    if (!profile) return false;
    const roleList = Array.isArray(roles) ? roles : [roles];
    return roleList.includes(profile.role);
  }, [profile]);

  const isAdmin = useCallback(() => hasRole('org_admin'), [hasRole]);
  const isManager = useCallback(() => hasRole(['org_admin', 'iso_manager']), [hasRole]);
  const canEdit = useCallback(() => hasRole(['org_admin', 'iso_manager', 'user']), [hasRole]);

  const value = {
    // Estado
    user,
    profile,
    organizations,
    currentOrganization,
    securityAlert,
    loading,
    isAuthenticated,
    mustChangePassword,
    
    // Acciones
    login,
    logout,
    refreshToken,
    checkAuth,
    switchOrganization,
    changePassword,
    requestPasswordReset,
    confirmPasswordReset,
    
    // Helpers
    hasRole,
    isAdmin,
    isManager,
    canEdit,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export default AuthContext;
