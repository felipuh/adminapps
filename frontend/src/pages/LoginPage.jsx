import { useRef, useState } from 'react';
import { Shield, Mail, Lock, Eye, EyeOff, AlertCircle, KeyRound } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { authService } from '../services/api';
import { authSession } from '../services/authRefresh.js';
import toast from 'react-hot-toast';

const LANDING_URL = import.meta.env.VITE_LANDING_URL || '';

const LoginPage = () => {
  const { checkAuth } = useAuth();
  const navigate = useNavigate();
  
  // Login form state
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  
  // 2FA state
  const [requires2FA, setRequires2FA] = useState(false);
  const [otp, setOTP] = useState('');
  const [verificationMethod, setVerificationMethod] = useState('totp');
  const [tempAccessToken, setTempAccessToken] = useState('');
  const [user2FA, setUser2FA] = useState(null);
  const otpSubmissionInProgress = useRef(false);
  const challengeSession = useRef(null);
  
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
        challengeSession.current = authSession.snapshot();
        setRequires2FA(true);
        setTempAccessToken(response.temporary_token || response.access);
        setUser2FA(response.user);
        toast('Por favor, ingresa tu código de autenticación');
        setLoading(false);
        return;
      }

      // Normal login - authService.login already accepted login via authSession
      await checkAuth();
      const user = response.user;
      const mustChangePassword = Boolean(user?.must_change_password);
      navigate(mustChangePassword ? '/settings' : '/', { replace: true });
      toast.success(`¡Bienvenido, ${user?.full_name || 'Usuario'}!`);
    } catch (err) {
      const errorMsg = err.response?.data?.detail || err.response?.data?.error || 'Error al iniciar sesión';
      setError(errorMsg);
      toast.error(errorMsg);
    }
    
    setLoading(false);
  };

  const handleOTPSubmit = async (e) => {
    e.preventDefault();
    if (otpSubmissionInProgress.current) {
      return;
    }

    setError('');

    const isValidCode = verificationMethod === 'totp'
      ? /^\d{6}$/.test(otp)
      : /^[A-F0-9]{8}$/.test(otp);
    if (!isValidCode) {
      setError(verificationMethod === 'totp'
        ? 'El código de autenticación debe tener 6 dígitos.'
        : 'El código de respaldo debe tener 8 caracteres hexadecimales (0-9, A-F).');
      return;
    }

    otpSubmissionInProgress.current = true;
    setLoading(true);

    try {
      const session = challengeSession.current;
      if (!session) throw new Error('No hay un desafío de verificación vigente');
      authSession.assertCurrent(session);
      const response = await authService.verify2fa(
        { token: otp },
        tempAccessToken
      );

      if (response.status === 'verified') {
        const access = response.access || response.tokens?.access;
        const refresh = response.refresh || response.tokens?.refresh;

        if (access && refresh) {
          authSession.acceptLogin(session, { access, refresh });
          await checkAuth();
          authSession.assertCurrent(session);
          toast.success('¡Sesión iniciada correctamente!');
          navigate('/', { replace: true });
        } else {
          setError('El servidor no retornó credenciales de sesión.');
          toast.error('Error de autenticación: faltan tokens de acceso.');
        }
      } else {
        const errorMsg = response.message || 'Código de autenticación inválido';
        setError(errorMsg);
        toast.error(errorMsg);
      }
    } catch (err) {
      const tokenError = err.response?.data?.token;
      const errorMsg = (Array.isArray(tokenError) ? tokenError[0] : tokenError)
        || err.response?.data?.detail
        || err.response?.data?.message
        || (verificationMethod === 'totp'
          ? 'No se pudo verificar el código de autenticación. Intenta de nuevo o vuelve a iniciar sesión.'
          : 'No se pudo verificar el código de respaldo. Intenta de nuevo o vuelve a iniciar sesión.');
      setError(errorMsg);
      toast.error(errorMsg);
    } finally {
      otpSubmissionInProgress.current = false;
      setLoading(false);
    }
  };

  const handleCancel2FA = () => {
    if (otpSubmissionInProgress.current) return;
    challengeSession.current = null;
    setRequires2FA(false);
    setOTP('');
    setVerificationMethod('totp');
    setTempAccessToken('');
    setUser2FA(null);
    setError('');
  };

  // 2FA form
  if (requires2FA) {
    return (
      <div className="auth-shell flex items-center justify-center p-4">
        <div className="relative w-full max-w-md">
          <div className="text-center mb-8">
            <div className="inline-flex h-16 w-16 items-center justify-center rounded-2xl bg-amber-600 text-white shadow-sm mb-4">
              <KeyRound className="w-8 h-8" />
            </div>
            <h1 className="text-3xl font-semibold text-slate-950">Verificación 2FA</h1>
            <p className="text-slate-500 mt-2">Autenticación de dos factores</p>
          </div>

          <div className="auth-card rounded-2xl p-8">
            <div className="text-center mb-6">
              <p className="text-slate-600">
                Verifica tu identidad para <span className="font-semibold text-slate-900">{user2FA?.email}</span>
              </p>
              <p className="text-slate-500 text-sm mt-2">
                {verificationMethod === 'totp'
                  ? 'Ingresa el código de 6 dígitos de tu aplicación de autenticación.'
                  : 'Ingresa uno de tus códigos de respaldo de 8 caracteres hexadecimales.'}
              </p>
            </div>

            {/* Error message */}
            {error && (
              <div id="two-factor-error" role="alert" className="mb-6 p-4 bg-red-500/10 border border-red-500/30 rounded-lg flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
                <p className="text-sm text-red-400">{error}</p>
              </div>
            )}

            <form onSubmit={handleOTPSubmit} className="space-y-5">
              <fieldset className="space-y-3">
                <legend className="block text-sm font-medium text-slate-600 mb-2">
                  Método de verificación
                </legend>
                <label className="flex items-center gap-3 cursor-pointer text-sm text-slate-600">
                  <input
                    type="radio"
                    name="verificationMethod"
                    value="totp"
                    checked={verificationMethod === 'totp'}
                    onChange={() => {
                      setVerificationMethod('totp');
                      setOTP('');
                      setError('');
                    }}
                    disabled={loading}
                  />
                  <span>Código de autenticación (6 dígitos)</span>
                </label>
                <label className="flex items-center gap-3 cursor-pointer text-sm text-slate-600">
                  <input
                    type="radio"
                    name="verificationMethod"
                    value="backup"
                    checked={verificationMethod === 'backup'}
                    onChange={() => {
                      setVerificationMethod('backup');
                      setOTP('');
                      setError('');
                    }}
                    disabled={loading}
                  />
                  <span>Código de respaldo (8 caracteres hexadecimales)</span>
                </label>
              </fieldset>

              {/* OTP field */}
              <div>
                <label htmlFor="two-factor-code" className="block text-sm font-medium text-slate-600 mb-2">
                  {verificationMethod === 'totp' ? 'Código de autenticación' : 'Código de respaldo'}
                </label>
                <div className="relative">
                  <KeyRound className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
                  <input
                    id="two-factor-code"
                    type="text"
                    inputMode={verificationMethod === 'totp' ? 'numeric' : 'text'}
                    maxLength={verificationMethod === 'totp' ? 6 : undefined}
                    value={otp}
                    onChange={(e) => setOTP(verificationMethod === 'totp'
                      ? e.target.value.replace(/\D/g, '')
                      : e.target.value.toUpperCase())}
                    className="input-glass pl-11 text-center text-2xl tracking-widest"
                    placeholder={verificationMethod === 'totp' ? '000000' : 'A1B2C3D4'}
                    autoComplete={verificationMethod === 'totp' ? 'one-time-code' : 'off'}
                    spellCheck={false}
                    disabled={loading}
                    aria-invalid={Boolean(error)}
                    aria-describedby={error ? 'two-factor-error' : undefined}
                    required
                  />
                </div>
              </div>

              {/* Submit button */}
              <button
                type="submit"
                disabled={loading}
                className="w-full btn-primary py-3 flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <>
                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    <span>Verificando...</span>
                  </>
                ) : (
                  <span>Verificar {verificationMethod === 'totp' ? 'código' : 'código de respaldo'}</span>
                )}
              </button>

              {/* Cancel button */}
              <button
                type="button"
                onClick={handleCancel2FA}
                disabled={loading}
                className="w-full btn-secondary py-3"
              >
                Cancelar
              </button>
            </form>

          </div>

        <p className="text-center text-slate-500 text-sm mt-6">
            © 2026 Smart3AI. Todos los derechos reservados.
          </p>
        </div>
      </div>
    );
  }

  // Login form
  return (
    <div className="auth-shell flex items-center justify-center p-4">
      <div className="relative w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex h-16 w-16 items-center justify-center rounded-2xl bg-primary-600 text-white shadow-sm mb-4">
            <Shield className="w-8 h-8" />
          </div>
          <h1 className="text-3xl font-semibold text-slate-950">AdminApps</h1>
          <p className="text-slate-500 mt-2">Smart3AI SaaS Control Plane</p>
        </div>

        <div className="auth-card rounded-2xl p-8">
          <div className="text-center mb-6">
            <h2 className="text-xl font-semibold text-slate-950">Iniciar sesión</h2>
            <p className="text-slate-500 text-sm mt-1">Ingresa tus credenciales para continuar</p>
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

          {LANDING_URL && (
            <div className="mt-6 border-t border-slate-200 pt-4 text-center text-sm">
              <p className="text-slate-500 mb-2">Conoce la propuesta comercial de IsoSmart</p>
              <a
                href={LANDING_URL}
                target="_blank"
                rel="noreferrer"
                className="font-semibold text-primary-700 hover:text-primary-900"
              >
                Ver landing corporativa y demo conversacional
              </a>
            </div>
          )}
        </div>

        {/* Footer */}
        <p className="text-center text-slate-500 text-sm mt-6">
          © 2026 Smart3AI. Todos los derechos reservados.
        </p>
      </div>
    </div>
  );
};

export default LoginPage;
