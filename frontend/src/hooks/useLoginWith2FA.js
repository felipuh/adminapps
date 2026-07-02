import { useState, useCallback } from 'react';
import { authService } from '../services/api';

/**
 * Custom hook for handling login with 2FA flow
 * 
 * Usage:
 * const { login, loading, error } = useLoginWith2FA();
 * 
 * In login form:
 * const result = await login(email, password);
 * if (result.success) {
 *   // Login successful, redirect to dashboard
 * }
 */
export const useLoginWith2FA = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [requires2FA, setRequires2FA] = useState(false);
  const [accessToken, setAccessToken] = useState(null);
  const [userEmail, setUserEmail] = useState(null);

  const login = useCallback(async (email, password) => {
    setLoading(true);
    setError(null);

    try {
      const response = await authService.login({
        email,
        password,
      });

      // Check if 2FA is required
      if (response.requires_2fa) {
        setRequires2FA(true);
        setAccessToken(response.access);
        setUserEmail(email);
        setLoading(false);
        
        return {
          success: false,
          requires_2fa: true,
          message: 'Two-factor authentication required',
        };
      }

      // Normal login - store tokens
      localStorage.setItem('access_token', response.access);
      localStorage.setItem('refresh_token', response.refresh);
      
      setLoading(false);
      return {
        success: true,
        user: response.user,
        tokens: {
          access: response.access,
          refresh: response.refresh,
        },
      };
    } catch (err) {
      const errorMsg = err.response?.data?.detail || err.response?.data?.error || 'Login failed';
      setError(errorMsg);
      setLoading(false);
      
      return {
        success: false,
        error: errorMsg,
      };
    }
  }, []);

  const verify2FA = useCallback(async (otp) => {
    if (!accessToken) {
      throw new Error('No temporary token available');
    }

    setLoading(true);
    setError(null);

    try {
      // Use the temporary access token to verify 2FA
      const response = await authService.verify2fa({
        token: otp,
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      });

      // 2FA verified successfully
      setRequires2FA(false);
      setAccessToken(null);
      setUserEmail(null);

      setLoading(false);

      return {
        success: true,
        user: response.user,
        message: response.message,
      };
    } catch (err) {
      const errorMsg = err.response?.data?.token?.[0] || 'OTP verification failed';
      setError(errorMsg);
      setLoading(false);

      return {
        success: false,
        error: errorMsg,
      };
    }
  }, [accessToken]);

  const cancel2FA = useCallback(() => {
    setRequires2FA(false);
    setAccessToken(null);
    setUserEmail(null);
    setError(null);
  }, []);

  return {
    login,
    verify2FA,
    cancel2FA,
    loading,
    error,
    requires2FA,
    userEmail,
  };
};

export default useLoginWith2FA;
