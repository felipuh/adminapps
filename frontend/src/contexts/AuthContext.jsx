import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { authService, featureFlagService } from '../services/api';

const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [securityAlert, setSecurityAlert] = useState(null);
  const [featureFlags, setFeatureFlags] = useState({});
  const [featureFlagsLoading, setFeatureFlagsLoading] = useState(false);
  const [loading, setLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const mustChangePassword = Boolean(user?.must_change_password);

  const applyTheme = useCallback((theme) => {
    const root = document.documentElement;
    root.classList.remove('theme-light', 'theme-dark');

    const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    const resolved = theme === 'system' ? (prefersDark ? 'dark' : 'light') : (theme || 'dark');

    root.classList.add(resolved === 'light' ? 'theme-light' : 'theme-dark');
  }, []);

  const applyLanguage = useCallback((language) => {
    document.documentElement.lang = language || 'es';
  }, []);

  const loadFeatureFlags = useCallback(async () => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      setFeatureFlags({});
      setFeatureFlagsLoading(false);
      return {};
    }

    try {
      setFeatureFlagsLoading(true);
      const data = await featureFlagService.getAll();
      const nextFlags = data && typeof data === 'object' ? data : {};
      setFeatureFlags(nextFlags);
      return nextFlags;
    } catch (error) {
      console.warn('Feature flags unavailable, using defaults:', error);
      setFeatureFlags({});
      return {};
    } finally {
      setFeatureFlagsLoading(false);
    }
  }, []);

  // Check if user is logged in on mount
  const checkAuth = useCallback(async () => {
    const token = localStorage.getItem('access_token');
    if (token) {
      try {
        const userData = await authService.getCurrentUser();
        setUser(userData);
        setIsAuthenticated(true);
        await loadFeatureFlags();
      } catch (error) {
        console.error('Auth check failed:', error);
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        setUser(null);
        setSecurityAlert(null);
        setFeatureFlags({});
        setFeatureFlagsLoading(false);
        setIsAuthenticated(false);
      }
    } else {
      setFeatureFlags({});
      setFeatureFlagsLoading(false);
    }
    setLoading(false);
  }, [loadFeatureFlags]);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  useEffect(() => {
    const persistedTheme = localStorage.getItem('ui_theme') || 'dark';
    const persistedLanguage = localStorage.getItem('ui_language') || 'es';
    applyTheme(persistedTheme);
    applyLanguage(persistedLanguage);
  }, [applyTheme, applyLanguage]);

  useEffect(() => {
    if (!user) {
      return;
    }

    const nextTheme = user.theme || 'dark';
    const nextLanguage = user.language || 'es';
    applyTheme(nextTheme);
    applyLanguage(nextLanguage);
    localStorage.setItem('ui_theme', nextTheme);
    localStorage.setItem('ui_language', nextLanguage);
  }, [user, applyTheme, applyLanguage]);

  // Login function
  const login = async (email, password) => {
    try {
      const response = await authService.login({ email, password });
      
      // Store tokens
      localStorage.setItem('access_token', response.access);
      localStorage.setItem('refresh_token', response.refresh);
      
      // Set user data
      setUser(response.user);
      setSecurityAlert(response.security_alert || null);
      setIsAuthenticated(true);
      await loadFeatureFlags();
      
      return {
        success: true,
        user: response.user,
        mustChangePassword: Boolean(response.user?.must_change_password),
        securityAlert: response.security_alert || null,
      };
    } catch (error) {
      const message = error.response?.data?.detail || 
                      error.response?.data?.error ||
                      error.response?.data?.message ||
                      'Error al iniciar sesión';
      return { success: false, error: message };
    }
  };

  // Logout function
  const logout = async () => {
    try {
      await authService.logout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      setUser(null);
      setSecurityAlert(null);
      setFeatureFlags({});
      setFeatureFlagsLoading(false);
      setIsAuthenticated(false);
      applyTheme(localStorage.getItem('ui_theme') || 'dark');
      applyLanguage(localStorage.getItem('ui_language') || 'es');
    }
  };

  // Update user profile
  const updateProfile = async (data) => {
    try {
      const updatedUser = await authService.updateProfile(data);
      setUser(updatedUser);
      return { success: true, user: updatedUser };
    } catch (error) {
      const message = error.response?.data?.detail || 'Error al actualizar perfil';
      return { success: false, error: message };
    }
  };

  const changePassword = async (currentPassword, newPassword, newPasswordConfirm) => {
    try {
      await authService.changePassword(currentPassword, newPassword, newPasswordConfirm);
      setUser((currentUser) => (
        currentUser
          ? { ...currentUser, must_change_password: false }
          : currentUser
      ));
      setSecurityAlert(null);
      return { success: true };
    } catch (error) {
      const message = error.response?.data?.detail ||
        error.response?.data?.current_password?.[0] ||
        error.response?.data?.new_password?.[0] ||
        error.response?.data?.new_password_confirm?.[0] ||
        'Error al cambiar la contraseña';
      return { success: false, error: message };
    }
  };

  // Check if user has specific role
  const hasRole = (roles) => {
    if (!user) return false;
    if (typeof roles === 'string') {
      return user.role === roles;
    }
    return roles.includes(user.role);
  };

  // Check if user is admin
  const isAdmin = () => {
    return hasRole(['superadmin', 'admin']);
  };

  const isFeatureEnabled = (flagName) => Boolean(featureFlags?.[flagName]);

  const value = {
    user,
    loading,
    isAuthenticated,
    mustChangePassword,
    securityAlert,
    featureFlags,
    featureFlagsLoading,
    login,
    logout,
    updateProfile,
    changePassword,
    hasRole,
    isAdmin,
    checkAuth,
    refreshFeatureFlags: loadFeatureFlags,
    isFeatureEnabled,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
