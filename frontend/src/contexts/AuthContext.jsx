import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { authService, featureFlagService } from '../services/api';
import { authSession } from '../services/authRefresh.js';

const AuthContext = createContext(null);

// eslint-disable-next-line react-refresh/only-export-components
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
    const resolved = theme === 'system' ? (prefersDark ? 'dark' : 'light') : (theme || 'light');

    root.classList.add(resolved === 'light' ? 'theme-light' : 'theme-dark');
  }, []);

  const applyLanguage = useCallback((language) => {
    document.documentElement.lang = language || 'es';
  }, []);

  const loadFeatureFlags = useCallback(async (isEffectCurrent = () => true) => {
    const session = authSession.snapshot();
    const token = session.access;
    if (!token) {
      if (isEffectCurrent() && authSession.isCurrent(session)) {
        setFeatureFlags({});
        setFeatureFlagsLoading(false);
      }
      return {};
    }

    try {
      if (!isEffectCurrent() || !authSession.isCurrent(session)) return {};
      setFeatureFlagsLoading(true);
      const data = await featureFlagService.getAll();
      if (!isEffectCurrent() || !authSession.isCurrent(session)) return {};
      const nextFlags = data && typeof data === 'object' ? data : {};
      setFeatureFlags(nextFlags);
      return nextFlags;
    } catch {
      if (!isEffectCurrent() || !authSession.isCurrent(session)) return {};
      setFeatureFlags({});
      return {};
    } finally {
      if (isEffectCurrent() && authSession.isCurrent(session)) setFeatureFlagsLoading(false);
    }
  }, []);

  const checkAuthRun = useCallback(async (isEffectCurrent) => {
    const session = authSession.snapshot();
    const isRunCurrent = () => isEffectCurrent() && authSession.isCurrent(session);
    const token = session.access;
    if (token) {
      try {
        const userData = await authService.getCurrentUser();
        if (!isRunCurrent()) return;
        setUser(userData);
        setIsAuthenticated(true);
        await loadFeatureFlags(isEffectCurrent);
      } catch {
        if (!isEffectCurrent() || !authSession.isCurrent(session)) return;
        if (!authSession.clear(session)) return;
        if (!isEffectCurrent()) return;
        setLoading(false);
        setUser(null);
        setSecurityAlert(null);
        setFeatureFlags({});
        setFeatureFlagsLoading(false);
        setIsAuthenticated(false);
      }
    } else {
      if (!isRunCurrent()) return;
      setFeatureFlags({});
      setFeatureFlagsLoading(false);
    }
    if (isRunCurrent()) setLoading(false);
  }, [loadFeatureFlags]);

  // Check if user is logged in on mount
  const checkAuth = useCallback(() => checkAuthRun(() => true), [checkAuthRun]);

  useEffect(() => {
    let effectCurrent = true;
    checkAuthRun(() => effectCurrent);
    return () => {
      effectCurrent = false;
    };
  }, [checkAuthRun]);

  useEffect(() => {
    const persistedTheme = localStorage.getItem('ui_theme') || 'light';
    const persistedLanguage = localStorage.getItem('ui_language') || 'es';
    applyTheme(persistedTheme);
    applyLanguage(persistedLanguage);
  }, [applyTheme, applyLanguage]);

  useEffect(() => {
    if (!user) {
      return;
    }

    const nextTheme = user.theme || 'light';
    const nextLanguage = user.language || 'es';
    applyTheme(nextTheme);
    applyLanguage(nextLanguage);
    localStorage.setItem('ui_theme', nextTheme);
    localStorage.setItem('ui_language', nextLanguage);
  }, [user, applyTheme, applyLanguage]);

  // Login function
  const login = async (email, password) => {
    setUser(null);
    setSecurityAlert(null);
    setFeatureFlags({});
    setFeatureFlagsLoading(false);
    setIsAuthenticated(false);
    setLoading(false);
    try {
      const response = await authService.login({ email, password });
      
      if (!authSession.isLoginCurrent(response)) {
        return { success: false, error: 'La sesión ha cambiado o requiere verificación' };
      }
      
      // Set user data
      setUser(response.user);
      setSecurityAlert(response.security_alert || null);
      setIsAuthenticated(true);
      setLoading(false);
      await loadFeatureFlags();
      if (!authSession.isLoginCurrent(response)) {
        return { success: false, error: 'La sesión ha cambiado' };
      }
      
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
    // authService invalidates the generation before its first await.
    const pending = authService.logout();
    const loggedOut = authSession.snapshot();
    setUser(null);
    setSecurityAlert(null);
    setFeatureFlags({});
    setFeatureFlagsLoading(false);
    setIsAuthenticated(false);
    setLoading(false);
    try {
      await pending;
    } finally {
      if (authSession.isCurrent(loggedOut)) {
        applyTheme(localStorage.getItem('ui_theme') || 'light');
        applyLanguage(localStorage.getItem('ui_language') || 'es');
      }
    }
  };

  // Update user profile
  const updateProfile = async (data) => {
    const session = authSession.snapshot();
    try {
      const updatedUser = await authService.updateProfile(data);
      authSession.assertCurrent(session);
      setUser(updatedUser);
      return { success: true, user: updatedUser };
    } catch (error) {
      const message = error.response?.data?.detail || 'Error al actualizar perfil';
      return { success: false, error: message };
    }
  };

  const changePassword = async (currentPassword, newPassword, newPasswordConfirm) => {
    const session = authSession.snapshot();
    try {
      await authService.changePassword(currentPassword, newPassword, newPasswordConfirm);
      authSession.assertCurrent(session);
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
