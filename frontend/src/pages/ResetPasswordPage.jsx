import { useMemo, useState } from 'react';
import { Lock, Shield } from 'lucide-react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { authService } from '../services/api';
import toast from 'react-hot-toast';

const ResetPasswordPage = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const uid = searchParams.get('uid') || '';
  const token = searchParams.get('token') || '';
  const hasTokenData = useMemo(() => Boolean(uid && token), [uid, token]);

  const [newPassword, setNewPassword] = useState('');
  const [newPasswordConfirm, setNewPasswordConfirm] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (newPassword !== newPasswordConfirm) {
      toast.error('Las contraseñas no coinciden.');
      return;
    }

    setLoading(true);
    try {
      const response = await authService.confirmPasswordReset(uid, token, newPassword, newPasswordConfirm);
      toast.success(response.detail || 'Contraseña actualizada exitosamente.');
      navigate('/login', { replace: true });
    } catch (error) {
      const message = error.response?.data?.detail ||
        error.response?.data?.new_password?.[0] ||
        error.response?.data?.new_password_confirm?.[0] ||
        'No se pudo restablecer la contraseña.';
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
          <h1 className="text-3xl font-semibold text-slate-950">Nueva contraseña</h1>
          <p className="text-slate-500 mt-2">Configura una contraseña segura para tu cuenta</p>
        </div>

        <div className="auth-card rounded-2xl p-8">
          {!hasTokenData ? (
            <div className="space-y-4">
              <p className="text-sm text-red-700">El enlace de recuperación es inválido o está incompleto.</p>
              <Link to="/forgot-password" className="btn-secondary inline-flex">Solicitar un nuevo enlace</Link>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Nueva contraseña</label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
                  <input
                    type="password"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    className="input-glass pl-11"
                    placeholder="Mínimo 12 caracteres"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Confirmar nueva contraseña</label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
                  <input
                    type="password"
                    value={newPasswordConfirm}
                    onChange={(e) => setNewPasswordConfirm(e.target.value)}
                    className="input-glass pl-11"
                    placeholder="Repite la contraseña"
                    required
                  />
                </div>
              </div>

              <button type="submit" disabled={loading} className="w-full btn-primary py-3">
                {loading ? 'Actualizando...' : 'Guardar nueva contraseña'}
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};

export default ResetPasswordPage;
