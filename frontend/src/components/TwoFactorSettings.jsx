import React, { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import {
  AlertCircle, Check, Copy, Loader, Lock, Settings, Shield, ShieldAlert, X, Eye, EyeOff
} from 'lucide-react';
import { userService } from '../services/api';

const TwoFactorSettings = ({ user, onUpdate }) => {
  const [is2faEnabled, setIs2faEnabled] = useState(false);
  const [loading, setLoading] = useState(true);
  const [setupStep, setSetupStep] = useState(null); // null, 'initiate', 'verify', 'backup'
  const [secret, setSecret] = useState(null);
  const [qrCode, setQrCode] = useState(null);
  const [otp, setOtp] = useState('');
  const [backupCodes, setBackupCodes] = useState([]);
  const [showBackupCodes, setShowBackupCodes] = useState(false);
  const [disablePassword, setDisablePassword] = useState('');
  const [showDisablePassword, setShowDisablePassword] = useState(false);

  // Load 2FA status
  useEffect(() => {
    const load2faStatus = async () => {
      try {
        const response = await userService.get2faStatus();
        setIs2faEnabled(response.is_enabled);
        setLoading(false);
      } catch (error) {
        console.error('Failed to load 2FA status', error);
        setLoading(false);
      }
    };
    load2faStatus();
  }, []);

  // Initiate 2FA setup
  const handleInitiate2fa = async () => {
    try {
      setLoading(true);
      const response = await userService.initiate2faSetup();
      setSecret(response.secret);
      setQrCode(response.qr_code);
      setSetupStep('verify');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to initiate 2FA setup');
    } finally {
      setLoading(false);
    }
  };

  // Verify 2FA token
  const handleVerify2fa = async () => {
    if (!otp || otp.length !== 6) {
      toast.error('Please enter a 6-digit code');
      return;
    }

    try {
      setLoading(true);
      const response = await userService.verify2faSetup({ token: otp });
      setBackupCodes(response.backup_codes);
      setSetupStep('backup');
      toast.success('2FA enabled successfully!');
    } catch (error) {
      toast.error(error.response?.data?.token?.[0] || 'Invalid code. Try again.');
    } finally {
      setLoading(false);
    }
  };

  // Complete 2FA setup
  const handleComplete2fa = () => {
    setIs2faEnabled(true);
    setSetupStep(null);
    setSecret(null);
    setQrCode(null);
    setOtp('');
    setBackupCodes([]);
    if (onUpdate) onUpdate();
  };

  // Disable 2FA
  const handleDisable2fa = async () => {
    if (!disablePassword) {
      toast.error('Password required to disable 2FA');
      return;
    }

    try {
      setLoading(true);
      await userService.disable2fa({ password: disablePassword });
      setIs2faEnabled(false);
      setDisablePassword('');
      setShowDisablePassword(false);
      toast.success('2FA has been disabled');
      if (onUpdate) onUpdate();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to disable 2FA');
    } finally {
      setLoading(false);
    }
  };

  // Copy to clipboard
  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    toast.success('Copied to clipboard');
  };

  if (loading) {
    return (
      <div className="glass-card p-8">
        <div className="flex items-center justify-center gap-3">
          <Loader className="h-5 w-5 animate-spin text-primary-500" />
          <span>Loading 2FA settings...</span>
        </div>
      </div>
    );
  }

  // Initial state
  if (!setupStep && !is2faEnabled) {
    return (
      <div className="glass-card p-8">
        <div className="flex items-start gap-4">
          <Shield className="h-6 w-6 text-amber-500 mt-1 flex-shrink-0" />
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-gray-100 mb-2">
              Two-Factor Authentication
            </h3>
            <p className="text-gray-400 mb-4">
              Add an extra layer of security to your account. With 2FA enabled, you'll need to enter a code from your authenticator app in addition to your password.
            </p>
            <button
              onClick={handleInitiate2fa}
              disabled={loading}
              className="px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50"
            >
              Enable 2FA
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Setup step 1: Show QR code
  if (setupStep === 'verify' && qrCode) {
    return (
      <div className="glass-card p-8">
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-gray-100 mb-4">Set up Two-Factor Authentication</h3>
          <p className="text-sm text-gray-400 mb-6">
            Scan this QR code with your authenticator app (Google Authenticator, Authy, Microsoft Authenticator, etc.)
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
          {/* QR Code */}
          <div className="flex flex-col items-center">
            <img
              src={qrCode}
              alt="2FA QR Code"
              className="w-full max-w-xs border-2 border-gray-600 rounded-lg p-2 bg-white"
            />
            <p className="text-xs text-gray-400 mt-4 text-center">
              Can't scan? Enter this code manually:
            </p>
            <div className="mt-3 flex items-center gap-2 bg-gray-800 px-4 py-2 rounded-lg">
              <code className="font-mono text-sm text-gray-200 break-all">{secret}</code>
              <button
                onClick={() => copyToClipboard(secret)}
                className="text-primary-500 hover:text-primary-400"
              >
                <Copy className="h-4 w-4" />
              </button>
            </div>
          </div>

          {/* OTP Input */}
          <div className="flex flex-col justify-center">
            <label className="block text-sm font-medium text-gray-300 mb-4">
              Enter the 6-digit code from your authenticator
            </label>
            <input
              type="text"
              maxLength="6"
              placeholder="000000"
              value={otp}
              onChange={(e) => setOtp(e.target.value.replace(/\D/g, ''))}
              className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-center text-2xl font-mono tracking-widest mb-4"
            />
            <button
              onClick={handleVerify2fa}
              disabled={loading || otp.length !== 6}
              className="w-full px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50 mb-3"
            >
              {loading ? 'Verifying...' : 'Verify & Continue'}
            </button>
            <button
              onClick={() => setSetupStep(null)}
              className="w-full px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg font-medium transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Setup step 2: Backup codes
  if (setupStep === 'backup' && backupCodes.length > 0) {
    return (
      <div className="glass-card p-8">
        <div className="mb-6">
          <div className="flex items-start gap-3 mb-4">
            <ShieldAlert className="h-6 w-6 text-amber-500 mt-1 flex-shrink-0" />
            <div>
              <h3 className="text-lg font-semibold text-gray-100">Save Your Backup Codes</h3>
              <p className="text-sm text-gray-400 mt-1">
                Save these codes in a secure location. You can use them to access your account if you lose access to your authenticator app.
              </p>
            </div>
          </div>
        </div>

        <div className="bg-gray-800 rounded-lg p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <span className="text-sm font-medium text-gray-300">Backup Codes</span>
            <button
              onClick={() => setShowBackupCodes(!showBackupCodes)}
              className="text-gray-400 hover:text-gray-300"
            >
              {showBackupCodes ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          </div>
          <div className="grid grid-cols-2 gap-3 font-mono text-sm">
            {backupCodes.map((code, idx) => (
              <div key={idx} className="flex items-center gap-2">
                <span className={showBackupCodes ? 'text-gray-300' : 'text-gray-500'}>
                  {showBackupCodes ? code : '••••••'}
                </span>
                <button
                  onClick={() => copyToClipboard(code)}
                  className="text-primary-500 hover:text-primary-400"
                >
                  <Copy className="h-3 w-3" />
                </button>
              </div>
            ))}
          </div>
        </div>

        <button
          onClick={handleComplete2fa}
          className="w-full px-4 py-3 bg-primary-600 hover:bg-primary-700 text-white rounded-lg font-medium transition-colors mb-3 flex items-center justify-center gap-2"
        >
          <Check className="h-5 w-5" />
          I've Saved My Backup Codes
        </button>

        <p className="text-xs text-gray-500 text-center">
          You can download or print these codes later from your account settings.
        </p>
      </div>
    );
  }

  // 2FA Enabled state
  if (is2faEnabled) {
    return (
      <div className="glass-card p-8">
        <div className="flex items-start gap-4 mb-6">
          <div className="p-2 bg-emerald-500/20 rounded-lg">
            <Check className="h-6 w-6 text-emerald-500" />
          </div>
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-gray-100">Two-Factor Authentication Enabled</h3>
            <p className="text-sm text-gray-400 mt-1">
              Your account is protected with two-factor authentication. You'll need to enter a code from your authenticator app when you log in.
            </p>
          </div>
        </div>

        <div className="bg-gray-800 rounded-lg p-4 mb-6">
          <ul className="space-y-3 text-sm">
            <li className="flex items-center gap-3">
              <Check className="h-4 w-4 text-emerald-500 flex-shrink-0" />
              <span className="text-gray-300">OTP token verification is active</span>
            </li>
            <li className="flex items-center gap-3">
              <Check className="h-4 w-4 text-emerald-500 flex-shrink-0" />
              <span className="text-gray-300">Backup codes have been saved</span>
            </li>
            <li className="flex items-center gap-3">
              <Lock className="h-4 w-4 text-primary-500 flex-shrink-0" />
              <span className="text-gray-300">Your account has enhanced security</span>
            </li>
          </ul>
        </div>

        <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 mb-6">
          <div className="flex items-start gap-3">
            <AlertCircle className="h-5 w-5 text-red-500 mt-0.5 flex-shrink-0" />
            <div>
              <p className="text-sm font-medium text-red-200 mb-3">Disable 2FA</p>
              <p className="text-xs text-red-300 mb-4">
                Enter your password to disable two-factor authentication. This will reduce your account security.
              </p>
              <div className="space-y-3">
                <div className="relative">
                  <input
                    type={showDisablePassword ? 'text' : 'password'}
                    placeholder="Enter your password"
                    value={disablePassword}
                    onChange={(e) => setDisablePassword(e.target.value)}
                    className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm text-gray-100 placeholder-gray-500"
                  />
                  <button
                    onClick={() => setShowDisablePassword(!showDisablePassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-300"
                  >
                    {showDisablePassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
                <button
                  onClick={handleDisable2fa}
                  disabled={loading || !disablePassword}
                  className="w-full px-3 py-2 bg-red-600 hover:bg-red-700 text-white text-sm rounded-lg font-medium transition-colors disabled:opacity-50"
                >
                  {loading ? 'Disabling...' : 'Disable 2FA'}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return null;
};

export default TwoFactorSettings;
