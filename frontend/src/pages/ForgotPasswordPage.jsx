import { useState } from 'react';
import { Mail, Shield, ArrowLeft } from 'lucide-react';
import { Link } from 'react-router-dom';
import { authService } from '../services/api';
import toast from 'react-hot-toast';

const ForgotPasswordPage = () => {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const response = await authService.requestPasswordReset(email);
      toast.success(response.detail || 'Revisa tu correo para continuar.');
      setSubmitted(true);
    } catch (error) {
      const message = error.response?.data?.detail || 'No se pudo procesar la solicitud.';
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-shell flex items-center justify-center p-4">
      <div className="relative w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex h-16 w-16 items-center justify-center rounded-2xl bg-primary-600 text-white shadow-sm mb-4">
            <Shield className="w-8 h-8" />
          </div>
          <h1 className="text-3xl font-semibold text-slate-950">Recuperar acceso</h1>
          <p className="text-slate-500 mt-2">AdminApps Smart3AI</p>
        </div>

        <div className="auth-card rounded-2xl p-8 space-y-5">
          <p className="text-sm text-slate-600">
            Ingresa tu correo y te enviaremos un enlace seguro para restablecer tu contraseña.
          </p>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">Correo electrónico</label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="input-glass pl-11"
                  placeholder="correo@empresa.com"
                  required
                  autoComplete="email"
                />
              </div>
            </div>

            <button type="submit" disabled={loading} className="w-full btn-primary py-3">
              {loading ? 'Enviando...' : 'Enviar enlace de recuperación'}
            </button>
          </form>

          {submitted && (
            <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
              Si el correo existe, recibirás instrucciones para restablecer tu contraseña.
            </div>
          )}

          <Link to="/login" className="inline-flex items-center gap-2 text-sm font-semibold text-primary-700 hover:text-primary-900">
            <ArrowLeft className="w-4 h-4" />
            Volver al inicio de sesión
          </Link>
        </div>
      </div>
    </div>
  );
};

export default ForgotPasswordPage;
