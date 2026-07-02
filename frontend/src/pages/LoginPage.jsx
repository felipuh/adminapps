import { useState } from 'react';
import { Shield, Mail, Lock, Eye, EyeOff, AlertCircle, KeyRound } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { authService } from '../services/api';
import toast from 'react-hot-toast';

const LoginPage = () => {
  const { login } = useAuth();
  const navigate = useNavigate();
  
  // Login form state
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  
  // 2FA state
  const [requires2FA, setRequires2FA] = useState(false);
  const [otp, setOTP] = useState('');
  const [tempAccessToken, setTempAccessToken] = useState('');
  const [user2FA, setUser2FA] = useState(null);
  
  // UI state
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleLoginSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');

      const normalizedEmail = email.trim();
      const normalizedPassword = password;

      const response = await authService.login({
        email: normalizedEmail,
        password: normalizedPassword,
      });

      // Check if 2FA is required
      if (response.requires_2fa) {
        setRequires2FA(true);
        setTempAccessToken(response.access);
        setUser2FA(response.user);
        toast.info('Por favor, ingresa tu código de autenticación');
        setLoading(false);
        return;
      }

      // Normal login - use auth context
      const result = await login(normalizedEmail, normalizedPassword);
      
      if (result.success) {
        navigate(result.mustChangePassword ? '/settings' : '/', { replace: true });
        toast.success(`¡Bienvenido, ${result.user.full_name}!`);
      } else {
        setError(result.error);
        toast.error(result.error);
      }
    } catch (err) {
      const errorMsg = err.response?.data?.detail || err.response?.data?.error || 'Error al iniciar sesión';
      setError(errorMsg);
      toast.error(errorMsg);
    }
    
    setLoading(false);
  };

  const handleOTPSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    if (otp.length !== 6) {
      setError('El código debe tener 6 dígitos');
      setLoading(false);
      return;
    }

    try {
      const response = await authService.verify2fa(
        { token: otp },
        tempAccessToken
      );

      if (response.status === 'verified') {
        // Store tokens and redirect
        localStorage.setItem('access_token', tempAccessToken);
        // The refresh token should already be in storage from the initial login
        
        // Update auth context with full user data
        await login(email, password);
        
        toast.success('¡Sesión iniciada correctamente!');
        navigate('/', { replace: true });
      }
    } catch (err) {
      const errorMsg = err.response?.data?.token?.[0] || 'Código de autenticación inválido';
      setError(errorMsg);
      toast.error(errorMsg);
    }
    
    setLoading(false);
  };

  const handleCancel2FA = () => {
    setRequires2FA(false);
    setOTP('');
    setTempAccessToken('');
    setUser2FA(null);
    setError('');
  };

  // 2FA form
  if (requires2FA) {
    return (
      <div className="min-h-screen bg-dark-500 flex items-center justify-center p-4">
        {/* Background effects */}
        <div className="fixed inset-0 overflow-hidden pointer-events-none">
          <div className="absolute top-1/4 -left-20 w-96 h-96 bg-primary-500/10 rounded-full blur-3xl" />
          <div className="absolute bottom-1/4 -right-20 w-96 h-96 bg-primary-600/10 rounded-full blur-3xl" />
        </div>

        {/* 2FA card */}
        <div className="relative w-full max-w-md">
          {/* Logo */}
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-gradient-to-br from-amber-500 to-amber-600 shadow-xl shadow-amber-500/30 mb-4">
              <KeyRound className="w-10 h-10 text-white" />
            </div>
            <h1 className="text-3xl font-bold text-gray-100">Verificación 2FA</h1>
            <p className="text-gray-500 mt-2">Autenticación de dos factores</p>
          </div>

          {/* Form card */}
          <div className="glass-card p-8">
            <div className="text-center mb-6">
              <p className="text-gray-400">
                Hemos enviado un código a <span className="font-semibold text-gray-300">{user2FA?.email}</span>
              </p>
              <p className="text-gray-500 text-sm mt-2">Ingresa tu código de 6 dígitos</p>
            </div>

            {/* Error message */}
            {error && (
              <div className="mb-6 p-4 bg-red-500/10 border border-red-500/30 rounded-lg flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
                <p className="text-sm text-red-400">{error}</p>
              </div>
            )}

            <form onSubmit={handleOTPSubmit} className="space-y-5">
              {/* OTP field */}
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-2">
                  Código de Autenticación
                </label>
                <div className="relative">
                  <KeyRound className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
                  <input
                    type="text"
                    inputMode="numeric"
                    maxLength="6"
                    value={otp}
                    onChange={(e) => setOTP(e.target.value.replace(/\D/g, ''))}
                    className="input-glass pl-11 text-center text-2xl tracking-widest"
                    placeholder="000000"
                    required
                  />
                </div>
              </div>

              {/* Submit button */}
              <button
                type="submit"
                disabled={loading || otp.length !== 6}
                className="w-full btn-primary py-3 flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <>
                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    <span>Verificando...</span>
                  </>
                ) : (
                  <span>Verificar Código</span>
                )}
              </button>

              {/* Cancel button */}
              <button
                type="button"
                onClick={handleCancel2FA}
                className="w-full btn-secondary py-3"
              >
                Cancelar
              </button>
            </form>

            {/* Backup code option */}
            <div className="mt-6 pt-4 border-t border-gray-700/40 text-center text-sm">
              <p className="text-gray-500">¿Tienes un código de respaldo?</p>
              <p className="text-gray-600 text-xs mt-2">Los códigos de respaldo tienen el mismo formato (6 dígitos)</p>
            </div>
          </div>

          {/* Footer */}
          <p className="text-center text-gray-600 text-sm mt-6">
            © 2026 Smart3AI. Todos los derechos reservados.
          </p>
        </div>
      </div>
    );
  }

  // Login form
  return (
    <div className="min-h-screen bg-dark-500 flex items-center justify-center p-4">
      {/* Background effects */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 -left-20 w-96 h-96 bg-primary-500/10 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 -right-20 w-96 h-96 bg-primary-600/10 rounded-full blur-3xl" />
      </div>

      {/* Login card */}
      <div className="relative w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-gradient-to-br from-primary-500 to-primary-600 shadow-xl shadow-primary-500/30 mb-4">
            <Shield className="w-10 h-10 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-gray-100">Admin Apps</h1>
          <p className="text-gray-500 mt-2">Smart3AI Control Center</p>
        </div>

        {/* Form card */}
        <div className="glass-card p-8">
          <div className="text-center mb-6">
            <h2 className="text-xl font-semibold text-gray-100">Iniciar Sesión</h2>
            <p className="text-gray-500 text-sm mt-1">Ingresa tus credenciales para continuar</p>
          </div>

          {/* Error message */}
          {error && (
            <div className="mb-6 p-4 bg-red-500/10 border border-red-500/30 rounded-lg flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-red-400">{error}</p>
            </div>
          )}

          <form onSubmit={handleLoginSubmit} className="space-y-5">
            {/* Email field */}
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">
                Correo Electrónico
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="input-glass pl-11"
                  placeholder="correo@ejemplo.com"
                  required
                  autoComplete="email"
                />
              </div>
            </div>

            {/* Password field */}
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">
                Contraseña
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="input-glass pl-11 pr-11"
                  placeholder="••••••••"
                  required
                  autoComplete="current-password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  aria-label={showPassword ? 'Ocultar contrasena' : 'Mostrar contrasena'}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-400 transition-colors"
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
            </div>

            {/* Remember me & forgot password */}
            <div className="flex items-center justify-between text-sm">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  className="w-4 h-4 rounded border-gray-600 bg-dark-400 text-primary-500 focus:ring-primary-500/30"
                />
                <span className="text-gray-400">Recordarme</span>
              </label>
              <Link to="/forgot-password" className="text-primary-400 hover:text-primary-300 transition-colors">
                ¿Olvidaste tu contraseña?
              </Link>
            </div>

            {/* Submit button */}
            <button
              type="submit"
              disabled={loading}
              className="w-full btn-primary py-3 flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  <span>Iniciando sesión...</span>
                </>
              ) : (
                <span>Iniciar Sesión</span>
              )}
            </button>
          </form>

          <div className="mt-6 border-t border-gray-700/40 pt-4 text-center text-sm">
            <p className="text-gray-500 mb-2">Conoce la propuesta comercial de IsoSmart</p>
            <a
              href="http://landing.isosmart.local/"
              target="_blank"
              rel="noreferrer"
              className="text-primary-300 hover:text-primary-200 transition-colors font-medium"
            >
              Ver landing corporativa y demo conversacional
            </a>
          </div>
        </div>

        {/* Footer */}
        <p className="text-center text-gray-600 text-sm mt-6">
          © 2026 Smart3AI. Todos los derechos reservados.
        </p>
      </div>
    </div>
  );
};

export default LoginPage;
