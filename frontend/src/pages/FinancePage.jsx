import React, { useEffect, useState } from 'react';
import toast from 'react-hot-toast';
import {
  AlertTriangle, BarChart3, Building2, Calendar, CheckCircle2, Coins, Clock,
  Download, ExternalLink, FileWarning, FileX2, Landmark, Mail, Plus, PlayCircle, Receipt,
  RefreshCw, Send, TrendingDown, Users, Wallet, X,
} from 'lucide-react';
import { Area, AreaChart, Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

import { billingService } from '../services/api';

const MetricCard = ({ title, value, helper, icon: Icon, tone = 'primary' }) => {
  const toneClasses = {
    primary: 'from-primary-600 to-primary-500 shadow-primary-500/20',
    success: 'from-emerald-600 to-emerald-500 shadow-emerald-500/20',
    warning: 'from-amber-600 to-amber-500 shadow-amber-500/20',
    danger: 'from-red-600 to-red-500 shadow-red-500/20',
  };
  return (
    <div className="glass-card p-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm text-gray-400">{title}</p>
          <p className="mt-2 text-2xl font-bold text-gray-100">{value}</p>
          {helper ? <p className="mt-2 text-xs text-gray-500">{helper}</p> : null}
        </div>
        <div className={`rounded-xl bg-gradient-to-br p-3 shadow-lg ${toneClasses[tone]}`}>
          <Icon className="h-5 w-5 text-white" />
        </div>
      </div>
    </div>
  );
};

const BatchModal = ({ fiscalProfiles, products, onClose, onSubmit, loading }) => {
  const [form, setForm] = useState({ fiscal_profile: '', product: '' });
  const canSubmit = form.fiscal_profile && form.product && !loading;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="glass-card w-full max-w-md p-6">
        <div className="flex items-start justify-between gap-4 mb-4">
          <div>
            <h2 className="text-lg font-semibold text-gray-100">Ejecutar Batch de Cobro</h2>
            <p className="mt-1 text-sm text-gray-400">
              Factura todas las organizaciones con cobro vencido.
            </p>
          </div>
          <button type="button" onClick={onClose} className="text-gray-500 hover:text-gray-200">
            <X className="h-5 w-5" />
          </button>
        </div>
        <div className="space-y-4">
          <div>
            <label className="block text-sm text-gray-400 mb-1.5">Perfil Fiscal</label>
            <select className="input-glass w-full" value={form.fiscal_profile}
              onChange={(e) => setForm((f) => ({ ...f, fiscal_profile: e.target.value }))}>
              <option value="">Selecciona un perfil fiscal...</option>
              {fiscalProfiles.map((fp) => (
                <option key={fp.id} value={fp.id}>{fp.legal_name} — {fp.tax_id}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1.5">Producto a facturar</label>
            <select className="input-glass w-full" value={form.product}
              onChange={(e) => setForm((f) => ({ ...f, product: e.target.value }))}>
              <option value="">Selecciona un producto...</option>
              {products.map((p) => (
                <option key={p.id} value={p.id}>{p.name} ({p.code})</option>
              ))}
            </select>
          </div>
        </div>
        <div className="mt-6 flex justify-end gap-3">
          <button type="button" onClick={onClose} className="btn-secondary">Cancelar</button>
          <button type="button" onClick={() => onSubmit(form)} disabled={!canSubmit}
            className="btn-primary inline-flex items-center gap-2">
            <PlayCircle className="h-4 w-4" />
            {loading ? 'Ejecutando...' : 'Ejecutar Batch'}
          </button>
        </div>
      </div>
    </div>
  );
};

const DAYS_OF_WEEK_LABELS = ['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb'];

const ReportScheduleModal = ({ onClose, onSubmit, loading }) => {
  const [form, setForm] = useState({
    name: '',
    report_type: 'billing_summary',
    frequency: 'daily',
    day_of_week: 1,
    day_of_month: 1,
    hour: 7,
    minute: 0,
    recipients: '',
    is_active: true,
  });

  const canSubmit = form.name.trim() && form.recipients.trim() && !loading;

  const submit = () => {
    const recipients = form.recipients
      .split(',')
      .map((item) => item.trim())
      .filter(Boolean);

    onSubmit({
      ...form,
      recipients,
      day_of_week: form.frequency === 'weekly' ? Number(form.day_of_week) : null,
      day_of_month: form.frequency === 'monthly' ? Number(form.day_of_month) : null,
      hour: Number(form.hour),
      minute: Number(form.minute),
    });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
      <div className="glass-card w-full max-w-lg overflow-hidden shadow-2xl">

        {/* Header */}
        <div className="flex items-start gap-4 px-6 pt-6 pb-5 border-b border-gray-700/50">
          <div className="flex-shrink-0 p-2.5 rounded-xl bg-gradient-to-br from-primary-500 to-primary-600 shadow-lg shadow-primary-500/25">
            <Calendar className="h-5 w-5 text-white" />
          </div>
          <div className="flex-1 min-w-0">
            <h2 className="text-lg font-semibold text-gray-100">Nueva Programación</h2>
            <p className="mt-0.5 text-sm text-gray-500">Envíos automáticos de reportes por email</p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 rounded-lg text-gray-500 hover:text-gray-200 hover:bg-dark-300 transition-colors -mr-1 flex-shrink-0"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Body */}
        <div className="px-6 py-5 space-y-5 max-h-[62vh] overflow-y-auto">

          {/* Name */}
          <div>
            <label className="mb-1.5 block text-xs font-medium tracking-wide uppercase text-gray-500">
              Nombre del reporte
            </label>
            <input
              className="input-glass w-full"
              placeholder="Ej. Resumen financiero semanal"
              value={form.name}
              onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
            />
          </div>

          {/* Report type — card selector */}
          <div>
            <label className="mb-2 block text-xs font-medium tracking-wide uppercase text-gray-500">
              Tipo de reporte
            </label>
            <div className="grid grid-cols-2 gap-3">
              {[
                { value: 'billing_summary', icon: Receipt, label: 'Resumen Billing', desc: 'Ingresos, facturas, KPIs' },
                { value: 'collections_snapshot', icon: BarChart3, label: 'Snapshot Cobranza', desc: 'Cuentas pendientes' },
              ].map(({ value, icon: Icon, label, desc }) => (
                <button
                  key={value}
                  type="button"
                  onClick={() => setForm((f) => ({ ...f, report_type: value }))}
                  className={`p-3.5 rounded-xl border text-left transition-all ${
                    form.report_type === value
                      ? 'border-primary-500/60 bg-primary-500/10 text-primary-200'
                      : 'border-gray-700/50 bg-dark-400/40 text-gray-400 hover:border-gray-600/70 hover:bg-dark-300/30'
                  }`}
                >
                  <Icon className="h-5 w-5 mb-2 opacity-80" />
                  <p className="text-sm font-medium">{label}</p>
                  <p className="text-xs opacity-60 mt-0.5">{desc}</p>
                </button>
              ))}
            </div>
          </div>

          {/* Frequency — pill buttons */}
          <div>
            <label className="mb-2 block text-xs font-medium tracking-wide uppercase text-gray-500">
              Frecuencia
            </label>
            <div className="grid grid-cols-3 gap-2">
              {[
                { value: 'daily', label: 'Diaria' },
                { value: 'weekly', label: 'Semanal' },
                { value: 'monthly', label: 'Mensual' },
              ].map(({ value, label }) => (
                <button
                  key={value}
                  type="button"
                  onClick={() => setForm((f) => ({ ...f, frequency: value }))}
                  className={`py-2.5 rounded-lg text-sm font-medium transition-all ${
                    form.frequency === value
                      ? 'bg-primary-500 text-white shadow-md shadow-primary-500/30'
                      : 'bg-dark-400/50 text-gray-400 hover:bg-dark-300/60'
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>

          {/* Weekday selector */}
          {form.frequency === 'weekly' && (
            <div>
              <label className="mb-2 block text-xs font-medium tracking-wide uppercase text-gray-500">
                Día de la semana
              </label>
              <div className="flex gap-1.5">
                {DAYS_OF_WEEK_LABELS.map((day, i) => (
                  <button
                    key={i}
                    type="button"
                    onClick={() => setForm((f) => ({ ...f, day_of_week: i }))}
                    className={`flex-1 py-2 rounded-lg text-xs font-medium transition-all ${
                      Number(form.day_of_week) === i
                        ? 'bg-primary-500 text-white shadow-sm shadow-primary-500/30'
                        : 'bg-dark-400/50 text-gray-400 hover:bg-dark-300/60'
                    }`}
                  >
                    {day}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Day of month */}
          {form.frequency === 'monthly' && (
            <div>
              <label className="mb-1.5 block text-xs font-medium tracking-wide uppercase text-gray-500">
                Día del mes
              </label>
              <select
                className="input-glass w-full"
                value={form.day_of_month}
                onChange={(e) => setForm((f) => ({ ...f, day_of_month: e.target.value }))}
              >
                {Array.from({ length: 31 }, (_, i) => i + 1).map((d) => (
                  <option key={d} value={d}>Día {d}</option>
                ))}
              </select>
            </div>
          )}

          {/* Time picker */}
          <div>
            <label className="mb-1.5 block text-xs font-medium tracking-wide uppercase text-gray-500">
              Hora de envío
            </label>
            <div className="flex items-center gap-2">
              <div className="relative flex-1">
                <Clock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-500 pointer-events-none" />
                <input
                  type="number"
                  min="0"
                  max="23"
                  className="input-glass w-full pl-9"
                  placeholder="07"
                  value={form.hour}
                  onChange={(e) => setForm((f) => ({ ...f, hour: e.target.value }))}
                />
              </div>
              <span className="text-xl text-gray-600 font-mono select-none pb-0.5">:</span>
              <input
                type="number"
                min="0"
                max="59"
                className="input-glass flex-1"
                placeholder="00"
                value={form.minute}
                onChange={(e) => setForm((f) => ({ ...f, minute: e.target.value }))}
              />
              <span className="text-xs text-gray-500 whitespace-nowrap pr-1">CR (UTC−6)</span>
            </div>
          </div>

          {/* Recipients */}
          <div>
            <label className="mb-1.5 block text-xs font-medium tracking-wide uppercase text-gray-500">
              Destinatarios
            </label>
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-500 pointer-events-none" />
              <input
                type="text"
                className="input-glass w-full pl-9"
                placeholder="finance@empresa.com, cfo@empresa.com"
                value={form.recipients}
                onChange={(e) => setForm((f) => ({ ...f, recipients: e.target.value }))}
              />
            </div>
            <p className="mt-1 text-xs text-gray-600">Separa múltiples correos con coma.</p>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-700/50 flex items-center justify-between gap-3">
          <div className="flex items-center gap-2.5">
            <button
              type="button"
              onClick={() => setForm((f) => ({ ...f, is_active: !f.is_active }))}
              className={`relative inline-flex h-5 w-9 flex-shrink-0 items-center rounded-full transition-colors ${
                form.is_active ? 'bg-primary-500' : 'bg-gray-600'
              }`}
            >
              <span className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white shadow transition-transform ${
                form.is_active ? 'translate-x-4' : 'translate-x-0.5'
              }`} />
            </button>
            <span className="text-xs text-gray-400">
              {form.is_active ? 'Activo al crear' : 'Inactivo al crear'}
            </span>
          </div>
          <div className="flex gap-3">
            <button type="button" onClick={onClose} className="btn-secondary text-sm">Cancelar</button>
            <button
              type="button"
              onClick={submit}
              disabled={!canSubmit}
              className="btn-primary inline-flex items-center gap-2 text-sm"
            >
              <Send className="h-4 w-4" />
              {loading ? 'Guardando…' : 'Crear programación'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

const PAYMENT_METHODS = ['transfer', 'cash', 'card', 'check', 'other'];

const RegisterPaymentModal = ({ invoices, onClose, onRegistered }) => {
  const [form, setForm] = useState({ invoice: '', method: 'transfer', reference: '', amount: '', notes: '' });
  const [saving, setSaving] = useState(false);
  const canSubmit = form.invoice && form.method && Number(form.amount) > 0 && !saving;

  const submit = async () => {
    try {
      setSaving(true);
      await billingService.registerPendingPayment({
        invoice: form.invoice,
        method: form.method,
        reference: form.reference,
        amount: form.amount,
        notes: form.notes,
      });
      toast.success('Pago pendiente registrado correctamente.');
      onRegistered();
      onClose();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'No se pudo registrar el pago.');
    } finally {
      setSaving(false);
    }
  };

  const field = (key, label, type = 'text', extra = {}) => (
    <div>
      <label className="block text-sm text-gray-400 mb-1.5">{label}</label>
      <input
        type={type}
        className="input-glass w-full"
        value={form[key]}
        onChange={(e) => setForm((f) => ({ ...f, [key]: e.target.value }))}
        {...extra}
      />
    </div>
  );

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="glass-card w-full max-w-md p-6">
        <div className="flex items-start justify-between gap-4 mb-5">
          <div>
            <h2 className="text-lg font-semibold text-gray-100">Registrar Pago Pendiente</h2>
            <p className="mt-1 text-sm text-gray-400">El pago quedará en estado pendiente hasta ser conciliado.</p>
          </div>
          <button type="button" onClick={onClose} className="text-gray-500 hover:text-gray-200">
            <X className="h-5 w-5" />
          </button>
        </div>
        <div className="space-y-4">
          <div>
            <label className="block text-sm text-gray-400 mb-1.5">Factura</label>
            <select className="input-glass w-full" value={form.invoice}
              onChange={(e) => setForm((f) => ({ ...f, invoice: e.target.value }))}>
              <option value="">Selecciona una factura...</option>
              {invoices.filter((inv) => ['accepted', 'pending'].includes(inv.status)).map((inv) => (
                <option key={inv.id} value={inv.id}>{inv.invoice_number} — {inv.organization_name}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1.5">Método de pago</label>
            <select className="input-glass w-full" value={form.method}
              onChange={(e) => setForm((f) => ({ ...f, method: e.target.value }))}>
              {PAYMENT_METHODS.map((m) => <option key={m} value={m}>{m}</option>)}
            </select>
          </div>
          {field('reference', 'Referencia / N° de transferencia')}
          {field('amount', 'Monto (CRC)', 'number', { min: 0, step: '0.01' })}
          <div>
            <label className="block text-sm text-gray-400 mb-1.5">Notas (opcional)</label>
            <textarea rows={2} className="input-glass w-full resize-none" value={form.notes}
              onChange={(e) => setForm((f) => ({ ...f, notes: e.target.value }))} />
          </div>
        </div>
        <div className="mt-6 flex justify-end gap-3">
          <button type="button" onClick={onClose} className="btn-secondary">Cancelar</button>
          <button type="button" onClick={submit} disabled={!canSubmit}
            className="btn-primary inline-flex items-center gap-2">
            <Plus className="h-4 w-4" />
            {saving ? 'Registrando...' : 'Registrar Pago'}
          </button>
        </div>
      </div>
    </div>
  );
};

const InvoiceDrawer = ({ invoiceId, onClose, onCreditNoteIssued }) => {
  const [detail, setDetail] = useState(null);
  const [downloading, setDownloading] = useState(false);
  const [showCreditNoteForm, setShowCreditNoteForm] = useState(false);
  const [creditNoteReason, setCreditNoteReason] = useState('');
  const [issuingCreditNote, setIssuingCreditNote] = useState(false);

  useEffect(() => {
    if (!invoiceId) return;
    billingService.getInvoiceDetail(invoiceId).then(setDetail).catch(() => toast.error('No se pudo cargar la factura.'));
  }, [invoiceId]);

  const issueCreditNote = async () => {
    if (!creditNoteReason.trim()) {
      toast.error('Ingresa el motivo de la nota de crédito.');
      return;
    }
    try {
      setIssuingCreditNote(true);
      const result = await billingService.createCreditNote(invoiceId, creditNoteReason.trim());
      toast.success(`Nota de Crédito ${result.credit_note_number} emitida.`);
      setShowCreditNoteForm(false);
      setCreditNoteReason('');
      if (onCreditNoteIssued) onCreditNoteIssued();
      onClose();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'No se pudo emitir la nota de crédito.');
    } finally {
      setIssuingCreditNote(false);
    }
  };

  const downloadXml = async () => {
    try {
      setDownloading(true);
      const xml = await billingService.getInvoiceXml(invoiceId);
      const blob = new Blob([xml], { type: 'application/xml' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${detail?.invoice_number || invoiceId}.xml`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      toast.error('No se pudo generar el XML.');
    } finally {
      setDownloading(false);
    }
  };

  const haciendaBadge = (s) => {
    if (s === 'accepted') return 'badge-success';
    if (s === 'rejected' || s === 'error') return 'badge-danger';
    if (s === 'processing') return 'badge-info';
    return 'badge-warning';
  };

  const statusBadge = (s) => {
    if (s === 'paid') return 'badge-success';
    if (s === 'accepted') return 'badge-info';
    if (s === 'reversed') return 'badge-danger';
    return 'badge-warning';
  };

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/50 backdrop-blur-sm" onClick={onClose}>
      <div className="glass-card h-full w-full max-w-lg overflow-y-auto p-6 rounded-none" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-start justify-between gap-4 mb-6">
          <div>
            <p className="text-xs uppercase tracking-widest text-primary-300">Detalle de Factura</p>
            <h2 className="mt-1 text-xl font-bold text-gray-100">{detail?.invoice_number || '...'}</h2>
          </div>
          <button type="button" onClick={onClose} className="text-gray-500 hover:text-gray-200">
            <X className="h-5 w-5" />
          </button>
        </div>

        {!detail ? (
          <div className="space-y-4">
            {[1, 2, 3, 4].map((i) => <div key={i} className="h-12 skeleton rounded-xl" />)}
          </div>
        ) : (
          <div className="space-y-5 text-sm">
            <div className="grid grid-cols-2 gap-4">
              <div className="rounded-xl bg-dark-400/40 border border-gray-700/50 p-4">
                <p className="text-xs text-gray-500 mb-1">Estado comercial</p>
                <span className={statusBadge(detail.status)}>{detail.status}</span>
              </div>
              <div className="rounded-xl bg-dark-400/40 border border-gray-700/50 p-4">
                <p className="text-xs text-gray-500 mb-1">Estado Hacienda</p>
                <span className={haciendaBadge(detail.hacienda_status)}>{detail.hacienda_status}</span>
              </div>
            </div>

            <div className="rounded-xl bg-dark-400/40 border border-gray-700/50 p-4 space-y-2">
              <Row label="Receptor" value={detail.receiver_name} />
              <Row label="RUC/Cédula" value={detail.receiver_tax_id || '—'} />
              <Row label="Email" value={detail.receiver_email || '—'} />
              <Row label="Moneda" value={detail.currency} />
              <Row label="Emitido" value={detail.issued_at ? new Date(detail.issued_at).toLocaleString('es-CR') : '—'} />
              <Row label="Vence" value={detail.due_date || '—'} />
            </div>

            <div className="rounded-xl bg-dark-400/40 border border-gray-700/50 p-4 space-y-2">
              <Row label="Subtotal" value={formatMoney(detail.subtotal)} />
              <Row label="Descuento" value={formatMoney(detail.discount_total)} />
              <Row label="Impuesto" value={formatMoney(detail.tax_total)} />
              <div className="border-t border-gray-700/50 pt-2">
                <Row label="Total" value={<span className="text-lg font-bold text-primary-300">{formatMoney(detail.total)}</span>} />
              </div>
            </div>

            {detail.consecutive_number && (
              <div className="rounded-xl bg-dark-400/40 border border-gray-700/50 p-4 space-y-2">
                <p className="text-xs uppercase tracking-widest text-gray-500 mb-2">Datos Hacienda CR</p>
                <Row label="Consecutivo" value={<code className="text-xs text-primary-200">{detail.consecutive_number}</code>} />
                <Row label="Clave numérica" value={<code className="text-[10px] text-primary-200 break-all">{detail.numeric_key}</code>} />
                {detail.hacienda_track_id && <Row label="Track ID" value={detail.hacienda_track_id} />}
                {detail.submitted_at && <Row label="Enviado" value={new Date(detail.submitted_at).toLocaleString('es-CR')} />}
                {detail.responded_at && <Row label="Respondido" value={new Date(detail.responded_at).toLocaleString('es-CR')} />}
                {detail.hacienda_message && <Row label="Mensaje" value={detail.hacienda_message} />}
              </div>
            )}

            {detail.lines && detail.lines.length > 0 && (
              <div className="rounded-xl bg-dark-400/40 border border-gray-700/50 p-4">
                <p className="text-xs uppercase tracking-widest text-gray-500 mb-3">Líneas de detalle</p>
                <div className="space-y-2">
                  {detail.lines.map((line, i) => (
                    <div key={i} className="flex items-start justify-between gap-2 border-b border-gray-700/30 pb-2 last:border-0 last:pb-0">
                      <div>
                        <p className="text-gray-200">{line.description}</p>
                        {line.cabys_code && <p className="text-xs text-gray-500">CAByS: {line.cabys_code}</p>}
                      </div>
                      <p className="shrink-0 text-primary-300 font-medium">{formatMoney(line.total)}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <button
              type="button"
              onClick={downloadXml}
              disabled={downloading}
              className="btn-secondary w-full inline-flex items-center justify-center gap-2"
            >
              <Download className="h-4 w-4" />
              {downloading ? 'Generando XML...' : 'Descargar XML Hacienda'}
            </button>

            {['accepted', 'paid'].includes(detail.status) && detail.status !== 'reversed' && (
              <div className="rounded-xl border border-red-500/30 bg-red-500/5 p-4 space-y-3">
                <button
                  type="button"
                  onClick={() => setShowCreditNoteForm((v) => !v)}
                  className="inline-flex items-center gap-2 text-sm text-red-300 hover:text-red-100 transition-colors"
                >
                  <FileX2 className="h-4 w-4" />
                  {showCreditNoteForm ? 'Cancelar' : 'Emitir Nota de Crédito'}
                </button>
                {showCreditNoteForm && (
                  <div className="space-y-3">
                    <textarea
                      rows={2}
                      placeholder="Motivo de la nota de crédito..."
                      value={creditNoteReason}
                      onChange={(e) => setCreditNoteReason(e.target.value)}
                      className="input-glass w-full resize-none text-sm"
                    />
                    <button
                      type="button"
                      onClick={issueCreditNote}
                      disabled={issuingCreditNote || !creditNoteReason.trim()}
                      className="btn-primary w-full inline-flex items-center justify-center gap-2 text-sm"
                    >
                      <FileX2 className="h-4 w-4" />
                      {issuingCreditNote ? 'Emitiendo...' : 'Confirmar Nota de Crédito'}
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

const Row = ({ label, value }) => (
  <div className="flex items-start justify-between gap-4">
    <span className="text-gray-500 shrink-0">{label}</span>
    <span className="text-gray-200 text-right">{value}</span>
  </div>
);

const formatMoney = (value) => {
  const amount = Number(value || 0);
  return new Intl.NumberFormat('es-CR', { style: 'currency', currency: 'CRC', maximumFractionDigits: 2 }).format(amount);
};

const PendingPaymentsList = ({ payments, onAction }) => {
  const [actingId, setActingId] = useState(null);

  const act = async (paymentId, action) => {
    try {
      setActingId(paymentId);
      if (action === 'confirm') await billingService.confirmPayment(paymentId);
      else await billingService.rejectPayment(paymentId);
      toast.success(action === 'confirm' ? 'Pago confirmado.' : 'Pago rechazado.');
      onAction();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'No se pudo procesar la acción.');
    } finally {
      setActingId(null);
    }
  };

  return (
    <div className="overflow-x-auto">
      <table className="table-glass">
        <thead>
          <tr>
            <th>Referencia</th>
            <th>Método</th>
            <th>Monto</th>
            <th>Notas</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          {payments.map((p) => (
            <tr key={p.id}>
              <td className="font-mono text-xs">{p.reference || '—'}</td>
              <td>{p.method}</td>
              <td>{formatMoney(p.amount)}</td>
              <td className="text-xs text-gray-400">{p.notes || '—'}</td>
              <td>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    disabled={actingId === p.id}
                    onClick={() => act(p.id, 'confirm')}
                    className="rounded-lg bg-emerald-500/15 border border-emerald-500/30 px-3 py-1 text-xs text-emerald-300 hover:bg-emerald-500/25 transition-colors disabled:opacity-50"
                  >
                    Confirmar
                  </button>
                  <button
                    type="button"
                    disabled={actingId === p.id}
                    onClick={() => act(p.id, 'reject')}
                    className="rounded-lg bg-red-500/15 border border-red-500/30 px-3 py-1 text-xs text-red-300 hover:bg-red-500/25 transition-colors disabled:opacity-50"
                  >
                    Rechazar
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};


const FinancePage = () => {
  const [loading, setLoading] = useState(true);
  const [runningBatch, setRunningBatch] = useState(false);
  const [showBatchModal, setShowBatchModal] = useState(false);
  const [selectedInvoiceId, setSelectedInvoiceId] = useState(null);
  const [fiscalProfiles, setFiscalProfiles] = useState([]);
  const [products, setProducts] = useState([]);
  const [summary, setSummary] = useState(null);
  const [byProduct, setByProduct] = useState([]);
  const [byOrganization, setByOrganization] = useState([]);
  const [timeline, setTimeline] = useState([]);
  const [receivables, setReceivables] = useState(null);
  const [invoices, setInvoices] = useState([]);
  const [batchReport, setBatchReport] = useState(null);
  const [scheduler, setScheduler] = useState(null);
  const [triggeringScheduler, setTriggeringScheduler] = useState(false);
  const [reportSchedules, setReportSchedules] = useState([]);
  const [showReportScheduleModal, setShowReportScheduleModal] = useState(false);
  const [creatingReportSchedule, setCreatingReportSchedule] = useState(false);
  const [runningReportScheduleId, setRunningReportScheduleId] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [churnData, setChurnData] = useState(null);
  const [reconciliation, setReconciliation] = useState(null);
  const [productDashboard, setProductDashboard] = useState([]);
  const [pendingPayments, setPendingPayments] = useState([]);
  const [showRegisterPayment, setShowRegisterPayment] = useState(false);

  const loadData = async () => {
    try {
      setLoading(true);
      const [summaryData, productData, organizationData, timelineData, receivableData, invoiceData, fpData, prodData, schedData, reportSchedulesData, alertsData, churnData_, reconciliationData, dashboardData] = await Promise.all([
        billingService.getSummary(),
        billingService.getRevenueByProduct(),
        billingService.getRevenueByOrganization(),
        billingService.getRevenueTimeline(),
        billingService.getAccountsReceivable(),
        billingService.getInvoices({ ordering: '-created_at' }),
        billingService.getFiscalProfiles(),
        billingService.getProducts(),
        billingService.getSchedulerStatus().catch(() => null),
        billingService.getReportSchedules().catch(() => []),
        billingService.getAlerts().catch(() => ({ alerts: [] })),
        billingService.getChurnAnalytics().catch(() => null),
        billingService.getReconciliationSummary().catch(() => null),
        billingService.getProductDashboard().catch(() => []),
        billingService.getInvoices({ ordering: '-created_at', status: 'pending,accepted', page_size: 100 }).catch(() => ({ results: [] })),
      ]);

      setSummary(summaryData);
      setByProduct(productData);
      setByOrganization(organizationData);
      setTimeline(timelineData);
      setReceivables(receivableData);
      setInvoices(invoiceData.results || invoiceData || []);
      setFiscalProfiles(fpData);
      setProducts(prodData);
      if (schedData) setScheduler(schedData);
      setReportSchedules(reportSchedulesData.results || reportSchedulesData || []);
      setAlerts((alertsData?.alerts || alertsData || []));
      setChurnData(churnData_);
      setReconciliation(reconciliationData);
      setProductDashboard(Array.isArray(dashboardData) ? dashboardData : []);

      // grab pending payments for reconciliation panel
      const allInvoices = invoiceData.results || invoiceData || [];
      billingService.getInvoices({ ordering: '-created_at', page_size: 200 }).then((inv) => {
        const list = inv.results || inv || [];
        setPendingPayments(list.flatMap((i) => (i.payments || [])).filter((p) => p.status === 'pending'));
      }).catch(() => {});
    } catch (error) {
      console.error('Finance dashboard error:', error);
      toast.error('No fue posible cargar el panel financiero.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const runBatch = async ({ fiscal_profile, product }) => {
    if (!fiscal_profile || !product) {
      toast.error('Se requiere perfil fiscal y producto para ejecutar el batch.');
      return;
    }

    try {
      setRunningBatch(true);
      const report = await billingService.runBatch({ fiscal_profile, product });
      setBatchReport(report);
      setShowBatchModal(false);
      toast.success(`Batch ejecutado: ${report.summary.processed_count} procesadas`);
      await loadData();
    } catch (error) {
      console.error('Batch billing error:', error);
      toast.error(error.response?.data?.detail || 'No fue posible ejecutar el batch.');
    } finally {
      setRunningBatch(false);
    }
  };

  const exportCsv = async () => {
    try {
      const blob = await billingService.exportInvoicesCsv();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `facturas_${new Date().toISOString().slice(0, 10)}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch {
      toast.error('No se pudo exportar el CSV.');
    }
  };

  const triggerSchedulerNow = async () => {
    try {
      setTriggeringScheduler(true);
      const result = await billingService.triggerSchedulerNow();
      toast.success(`Scheduler ejecutado: estado ${result.status}`);
      const schedData = await billingService.getSchedulerStatus().catch(() => null);
      if (schedData) setScheduler(schedData);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'No se pudo ejecutar el scheduler.');
    } finally {
      setTriggeringScheduler(false);
    }
  };

  const createReportSchedule = async (payload) => {
    try {
      setCreatingReportSchedule(true);
      await billingService.createReportSchedule(payload);
      toast.success('Programación de reporte creada.');
      setShowReportScheduleModal(false);
      await loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'No se pudo crear la programación.');
    } finally {
      setCreatingReportSchedule(false);
    }
  };

  const runReportScheduleNow = async (scheduleId) => {
    try {
      setRunningReportScheduleId(scheduleId);
      await billingService.runReportScheduleNow(scheduleId);
      toast.success('Reporte ejecutado y enviado por email.');
      await loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'No se pudo ejecutar el reporte.');
    } finally {
      setRunningReportScheduleId(null);
    }
  };

  if (loading) {
    return (
      <div className="space-y-6 animate-fadeIn">
        <div className="glass-card h-28 skeleton" />
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-4">
          {[1, 2, 3, 4].map((item) => (
            <div key={item} className="glass-card h-36 skeleton" />
          ))}
        </div>
        <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
          <div className="glass-card h-96 skeleton" />
          <div className="glass-card h-96 skeleton" />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fadeIn">
      {showBatchModal && (
        <BatchModal
          fiscalProfiles={fiscalProfiles}
          products={products}
          loading={runningBatch}
          onClose={() => setShowBatchModal(false)}
          onSubmit={runBatch}
        />
      )}
      {showReportScheduleModal && (
        <ReportScheduleModal
          onClose={() => setShowReportScheduleModal(false)}
          onSubmit={createReportSchedule}
          loading={creatingReportSchedule}
        />
      )}
      {showRegisterPayment && (
        <RegisterPaymentModal
          invoices={invoices}
          onClose={() => setShowRegisterPayment(false)}
          onRegistered={loadData}
        />
      )}
      {selectedInvoiceId && (
        <InvoiceDrawer
          invoiceId={selectedInvoiceId}
          onClose={() => setSelectedInvoiceId(null)}
          onCreditNoteIssued={loadData}
        />
      )}

      {/* Operational alerts */}
      {alerts.length > 0 && (
        <div className="glass-card p-5">
          <div className="mb-4 flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-amber-400" />
            <h2 className="text-base font-semibold text-gray-100">Alertas Operativas</h2>
            <span className="ml-auto rounded-full bg-amber-500/15 px-2.5 py-0.5 text-xs font-medium text-amber-300">{alerts.length}</span>
          </div>
          <div className="space-y-2">
            {alerts.map((alert, i) => {
              const badgeClass = alert.severity === 'danger' ? 'border-red-500/30 bg-red-500/10 text-red-200'
                : alert.severity === 'warning' ? 'border-amber-500/30 bg-amber-500/10 text-amber-200'
                : 'border-blue-500/30 bg-blue-500/10 text-blue-200';
              return (
                <div key={i} className={`rounded-xl border px-4 py-3 text-sm flex items-start gap-3 ${badgeClass}`}>
                  <AlertTriangle className="h-4 w-4 mt-0.5 shrink-0 opacity-70" />
                  <div>
                    <span className="font-medium capitalize">{alert.type?.replace(/_/g, ' ')}</span>
                    {alert.detail && <span className="ml-2 opacity-80">{alert.detail}</span>}
                    {alert.count != null && <span className="ml-2 opacity-70">({alert.count})</span>}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      <div className="glass-card p-6">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-sm uppercase tracking-[0.24em] text-primary-300">Smart3AI Finance Desk</p>
            <h1 className="mt-2 text-3xl font-bold text-gray-100">Control financiero multi-producto</h1>
            <p className="mt-2 max-w-3xl text-sm text-gray-400">
              Revenue total, cuentas por cobrar, rendimiento por producto, comportamiento por cliente y operaciones de batch para el backoffice de Smart3AI.
            </p>
          </div>
          <button
            type="button"
            onClick={() => setShowBatchModal(true)}
            disabled={runningBatch}
            className="btn-primary inline-flex items-center gap-2"
          >
            <PlayCircle className="h-4 w-4" />
            {runningBatch ? 'Ejecutando batch...' : 'Ejecutar Batch de Cobro'}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          title="Ingresos Netos"
          value={formatMoney(summary?.net_revenue)}
          helper={`${summary?.paid_invoices || 0} facturas pagadas`}
          icon={Coins}
          tone="success"
        />
        <MetricCard
          title="Cuentas por Cobrar"
          value={formatMoney(summary?.accounts_receivable)}
          helper={`${summary?.pending_invoices || 0} documentos pendientes`}
          icon={Wallet}
          tone="warning"
        />
        <MetricCard
          title="Impuesto Recaudado"
          value={formatMoney(summary?.tax_collected)}
          helper="Base operativa CR para Hacienda"
          icon={Landmark}
          tone="primary"
        />
        <MetricCard
          title="Productos Activos"
          value={summary?.active_products || 0}
          helper={`${summary?.total_products || 0} productos catalogados`}
          icon={BarChart3}
          tone="danger"
        />
      </div>

      <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
        <MetricCard
          title="MRR"
          value={formatMoney(summary?.mrr)}
          helper="Ingresos Recurrentes Mensuales"
          icon={RefreshCw}
          tone="success"
        />
        <MetricCard
          title="ARR"
          value={formatMoney(summary?.arr)}
          helper="Ingresos Recurrentes Anuales"
          icon={BarChart3}
          tone="primary"
        />
        <MetricCard
          title="Suscripciones Activas"
          value={summary?.active_subscriptions || 0}
          helper="Suscripciones en estado activo"
          icon={Building2}
          tone="warning"
        />
      </div>

      {/* Churn & trial metrics */}
      <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
        <MetricCard
          title="Churn Rate"
          value={churnData ? `${(churnData.churn_rate * 100).toFixed(1)}%` : '—'}
          helper="Cancelaciones últimos 30 días"
          icon={TrendingDown}
          tone="danger"
        />
        <MetricCard
          title="Trials Activos"
          value={churnData?.trial_subscriptions ?? (summary?.trial_subscriptions ?? '—')}
          helper="Suscripciones en período de prueba"
          icon={Clock}
          tone="warning"
        />
        <MetricCard
          title="Conversión de Trials"
          value={churnData ? `${(churnData.trial_conversion_rate * 100).toFixed(1)}%` : '—'}
          helper="Trials convertidos en últimos 30 días"
          icon={CheckCircle2}
          tone="success"
        />
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <div className="glass-card p-6">
          <div className="mb-6 flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-gray-100">Timeline de Revenue</h2>
              <p className="text-sm text-gray-500">Evolución mensual consolidada</p>
            </div>
            <Receipt className="h-5 w-5 text-primary-300" />
          </div>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={timeline}>
                <defs>
                  <linearGradient id="financeRevenue" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#004990" stopOpacity={0.35} />
                    <stop offset="95%" stopColor="#004990" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.25} />
                <XAxis dataKey="period" stroke="#94a3b8" fontSize={12} />
                <YAxis stroke="#94a3b8" fontSize={12} tickFormatter={(value) => `${Math.round(Number(value) / 1000)}k`} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#10233e',
                    border: '1px solid rgba(133, 173, 214, 0.25)',
                    borderRadius: '12px',
                    color: '#f8fafc',
                  }}
                  formatter={(value) => formatMoney(value)}
                />
                <Area type="monotone" dataKey="net_revenue" stroke="#004990" fill="url(#financeRevenue)" strokeWidth={2.5} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="glass-card p-6">
          <div className="mb-6 flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-gray-100">Revenue por Producto</h2>
              <p className="text-sm text-gray-500">Comparativo de ingresos netos</p>
            </div>
            <BarChart3 className="h-5 w-5 text-primary-300" />
          </div>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={byProduct}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.2} />
                <XAxis dataKey="product__code" stroke="#94a3b8" fontSize={12} />
                <YAxis stroke="#94a3b8" fontSize={12} tickFormatter={(value) => `${Math.round(Number(value) / 1000)}k`} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#10233e',
                    border: '1px solid rgba(133, 173, 214, 0.25)',
                    borderRadius: '12px',
                    color: '#f8fafc',
                  }}
                  formatter={(value) => formatMoney(value)}
                />
                <Bar dataKey="net_revenue" radius={[10, 10, 0, 0]} fill="#004990" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
        <div className="glass-card p-6 xl:col-span-2">
          <div className="mb-5 flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-gray-100">Revenue por Organización</h2>
              <p className="text-sm text-gray-500">Clientes que más aportan a Smart3AI</p>
            </div>
            <Building2 className="h-5 w-5 text-primary-300" />
          </div>
          <div className="overflow-x-auto">
            <table className="table-glass">
              <thead>
                <tr>
                  <th>Organización</th>
                  <th>Revenue Neto</th>
                  <th>Impuesto</th>
                  <th>Emitidas</th>
                  <th>Pagadas</th>
                </tr>
              </thead>
              <tbody>
                {byOrganization.map((item) => (
                  <tr key={item.organization__id}>
                    <td>{item.organization__name}</td>
                    <td>{formatMoney(item.net_revenue)}</td>
                    <td>{formatMoney(item.tax_collected)}</td>
                    <td>{item.invoices_issued}</td>
                    <td>{item.invoices_paid}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="glass-card p-6">
          <div className="mb-5 flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-gray-100">Aging</h2>
              <p className="text-sm text-gray-500">Cuentas por cobrar por vencimiento</p>
            </div>
            <FileWarning className="h-5 w-5 text-amber-300" />
          </div>
          <div className="space-y-4 text-sm">
            <div className="rounded-xl border border-gray-700/50 bg-dark-400/40 p-4">
              <p className="text-gray-400">Corriente</p>
              <p className="mt-1 text-xl font-semibold text-gray-100">{formatMoney(receivables?.current)}</p>
            </div>
            <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-4">
              <p className="text-amber-300">1 a 30 días</p>
              <p className="mt-1 text-xl font-semibold text-amber-100">{formatMoney(receivables?.overdue_1_30)}</p>
            </div>
            <div className="rounded-xl border border-orange-500/30 bg-orange-500/10 p-4">
              <p className="text-orange-300">31 a 60 días</p>
              <p className="mt-1 text-xl font-semibold text-orange-100">{formatMoney(receivables?.overdue_31_60)}</p>
            </div>
            <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-4">
              <p className="text-red-300">61+ días</p>
              <p className="mt-1 text-xl font-semibold text-red-100">{formatMoney(receivables?.overdue_61_plus)}</p>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <div className="glass-card p-6">
          <div className="mb-5 flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-gray-100">Facturas recientes</h2>
              <p className="text-sm text-gray-500">Estado comercial y operativo</p>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={exportCsv}
                className="btn-secondary inline-flex items-center gap-1.5 text-sm py-1.5 px-3"
                title="Exportar facturas a CSV"
              >
                <Download className="h-3.5 w-3.5" />
                Exportar CSV
              </button>
              <Receipt className="h-5 w-5 text-primary-300" />
            </div>
          </div>
          <div className="overflow-x-auto">
            <table className="table-glass">
              <thead>
                <tr>
                  <th>Factura</th>
                  <th>Cliente</th>
                  <th>Total</th>
                  <th>Estado</th>
                  <th>Hacienda</th>
                </tr>
              </thead>
              <tbody>
                {invoices.slice(0, 8).map((invoice) => (
                  <tr key={invoice.id}
                    className="cursor-pointer hover:bg-white/5 transition-colors"
                    onClick={() => setSelectedInvoiceId(invoice.id)}
                  >
                    <td className="inline-flex items-center gap-1.5">
                      {invoice.invoice_number}
                      <ExternalLink className="h-3 w-3 text-primary-400 opacity-60" />
                    </td>
                    <td>{invoice.organization_name}</td>
                    <td>{formatMoney(invoice.total)}</td>
                    <td>
                      <span className={invoice.status === 'paid' ? 'badge-success' : invoice.status === 'accepted' ? 'badge-info' : invoice.status === 'reversed' ? 'badge-danger' : 'badge-warning'}>
                        {invoice.status}
                      </span>
                    </td>
                    <td>
                      <span className={invoice.hacienda_status === 'accepted' ? 'badge-success' : invoice.hacienda_status === 'rejected' || invoice.hacienda_status === 'error' ? 'badge-danger' : 'badge-info'}>
                        {invoice.hacienda_status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="glass-card p-6">
          <div className="mb-5 flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-gray-100">Último Batch</h2>
              <p className="text-sm text-gray-500">Reporte de ejecución operativa</p>
            </div>
            <PlayCircle className="h-5 w-5 text-primary-300" />
          </div>
          {batchReport ? (
            <div className="space-y-4 text-sm">
              <div className="grid grid-cols-3 gap-3">
                <div className="rounded-xl bg-emerald-500/10 p-4 border border-emerald-500/25">
                  <p className="text-emerald-300">Procesadas</p>
                  <p className="mt-1 text-2xl font-semibold text-emerald-100">{batchReport.summary.processed_count}</p>
                </div>
                <div className="rounded-xl bg-amber-500/10 p-4 border border-amber-500/25">
                  <p className="text-amber-300">Omitidas</p>
                  <p className="mt-1 text-2xl font-semibold text-amber-100">{batchReport.summary.skipped_count}</p>
                </div>
                <div className="rounded-xl bg-red-500/10 p-4 border border-red-500/25">
                  <p className="text-red-300">Errores</p>
                  <p className="mt-1 text-2xl font-semibold text-red-100">{batchReport.summary.error_count}</p>
                </div>
              </div>
              <div className="rounded-xl border border-gray-700/50 bg-dark-400/40 p-4">
                <p className="text-xs uppercase tracking-[0.2em] text-gray-500">Fecha de ejecución</p>
                <p className="mt-2 text-gray-100">{batchReport.run_date}</p>
              </div>
              <div className="rounded-xl border border-gray-700/50 bg-dark-400/40 p-4">
                <p className="mb-2 text-xs uppercase tracking-[0.2em] text-gray-500">Últimas procesadas</p>
                <div className="space-y-2">
                  {batchReport.processed.slice(0, 4).map((item) => (
                    <div key={item.invoice_id} className="flex items-center justify-between gap-4 text-gray-300">
                      <span>{item.organization_name}</span>
                      <span className="text-primary-300">{item.invoice_number}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="rounded-xl border border-dashed border-gray-700/60 bg-dark-400/30 p-6 text-sm text-gray-500">
              Aún no se ha ejecutado un batch desde esta pantalla. Cuando lo corras, aquí quedará el último reporte operativo.
            </div>
          )}
        </div>
      </div>

      {/* Product dashboard */}
      {productDashboard.length > 0 && (
        <div className="glass-card p-6">
          <div className="mb-5 flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-gray-100">Dashboard por Producto</h2>
              <p className="text-sm text-gray-500">MRR, ARR y suscripciones por producto del catálogo</p>
            </div>
            <BarChart3 className="h-5 w-5 text-primary-300" />
          </div>
          <div className="overflow-x-auto">
            <table className="table-glass">
              <thead>
                <tr>
                  <th>Producto</th>
                  <th>Modelo</th>
                  <th>Revenue</th>
                  <th>MRR</th>
                  <th>ARR</th>
                  <th>Suscripciones</th>
                  <th>Facturas</th>
                </tr>
              </thead>
              <tbody>
                {productDashboard.map((p) => (
                  <tr key={p.product_id}>
                    <td>
                      <div className="font-medium text-gray-100">{p.product_name}</div>
                      <div className="text-xs text-gray-500">{p.product_code}</div>
                    </td>
                    <td className="text-xs text-gray-400">{p.billing_model}</td>
                    <td>{formatMoney(p.revenue)}</td>
                    <td className="text-emerald-300">{formatMoney(p.mrr)}</td>
                    <td className="text-primary-300">{formatMoney(p.arr)}</td>
                    <td>{p.active_subscriptions + p.trial_subscriptions}</td>
                    <td>{p.invoice_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Reconciliation panel */}
      {reconciliation && (
        <div className="glass-card p-6">
          <div className="mb-5 flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-gray-100">Conciliación Bancaria</h2>
              <p className="text-sm text-gray-500">Estado de pagos pendientes de conciliación</p>
            </div>
            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={() => setShowRegisterPayment(true)}
                className="btn-secondary inline-flex items-center gap-2 text-sm"
              >
                <Plus className="h-4 w-4" />
                Registrar Pago
              </button>
              <Wallet className="h-5 w-5 text-primary-300" />
            </div>
          </div>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
            <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-4">
              <p className="text-xs text-amber-300 uppercase tracking-wider">Pagos pendientes</p>
              <p className="mt-1 text-2xl font-semibold text-amber-100">{reconciliation.pending_payments}</p>
              <p className="mt-1 text-sm text-amber-300">{formatMoney(reconciliation.pending_amount)}</p>
            </div>
            <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-4">
              <p className="text-xs text-emerald-300 uppercase tracking-wider">Confirmados</p>
              <p className="mt-1 text-2xl font-semibold text-emerald-100">{reconciliation.confirmed_payments}</p>
              <p className="mt-1 text-sm text-emerald-300">{formatMoney(reconciliation.confirmed_amount)}</p>
            </div>
            <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-4">
              <p className="text-xs text-red-300 uppercase tracking-wider">Facturas vencidas</p>
              <p className="mt-1 text-2xl font-semibold text-red-100">{reconciliation.overdue_invoices}</p>
              <p className="mt-1 text-sm text-red-300">{formatMoney(reconciliation.overdue_amount)}</p>
            </div>
            <div className="rounded-xl border border-gray-700/50 bg-dark-400/40 p-4">
              <p className="text-xs text-gray-400 uppercase tracking-wider">Sin conciliar</p>
              <p className="mt-1 text-2xl font-semibold text-gray-100">{reconciliation.unmatched_invoices}</p>
              <p className="mt-1 text-xs text-gray-500">Facturas pagadas sin registro de pago</p>
            </div>
          </div>

          {pendingPayments.length > 0 && (
            <div className="mt-6">
              <p className="mb-3 text-xs uppercase tracking-widest text-gray-500">Pagos pendientes de conciliar</p>
              <PendingPaymentsList payments={pendingPayments} onAction={loadData} />
            </div>
          )}
        </div>
      )}

      {/* Scheduler panel */}
      <div className="glass-card p-6">
        <div className="mb-5 flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-gray-100">Scheduler Automático</h2>
            <p className="text-sm text-gray-500">
              {scheduler?.enabled
                ? `Activo — corre diario a las ${String(scheduler.cron?.hour ?? 6).padStart(2, '0')}:${String(scheduler.cron?.minute ?? 0).padStart(2, '0')} hora CR`
                : 'BILLING_SCHEDULER_ENABLED=false en este entorno'}
            </p>
          </div>
          <div className="flex items-center gap-3">
            <div className={`h-2.5 w-2.5 rounded-full ${scheduler?.running ? 'bg-emerald-400 animate-pulse' : 'bg-gray-600'}`} />
            <span className="text-sm text-gray-400">{scheduler?.running ? 'Corriendo' : 'Detenido'}</span>
            <button
              type="button"
              onClick={triggerSchedulerNow}
              disabled={triggeringScheduler}
              className="btn-secondary inline-flex items-center gap-2 text-sm"
            >
              <RefreshCw className={`h-4 w-4 ${triggeringScheduler ? 'animate-spin' : ''}`} />
              Ejecutar ahora
            </button>
          </div>
        </div>

        {scheduler?.next_run && (
          <div className="mb-4 rounded-xl bg-primary-500/10 border border-primary-500/20 px-4 py-3 text-sm text-primary-200 inline-flex items-center gap-2">
            <Clock className="h-4 w-4" />
            Próxima ejecución: {new Date(scheduler.next_run).toLocaleString('es-CR')}
          </div>
        )}

        {scheduler?.last_logs?.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="table-glass">
              <thead>
                <tr>
                  <th>Disparado</th>
                  <th>Finalizado</th>
                  <th>Estado</th>
                  <th>Resultado</th>
                </tr>
              </thead>
              <tbody>
                {scheduler.last_logs.slice(0, 8).map((log) => (
                  <tr key={log.id}>
                    <td>{log.triggered_at ? new Date(log.triggered_at).toLocaleString('es-CR') : '—'}</td>
                    <td>{log.finished_at ? new Date(log.finished_at).toLocaleString('es-CR') : '—'}</td>
                    <td>
                      <span className={log.status === 'success' ? 'badge-success' : log.status === 'running' ? 'badge-info' : log.status === 'skipped' ? 'badge-warning' : 'badge-danger'}>
                        {log.status}
                      </span>
                    </td>
                    <td className="text-xs text-gray-400">
                      {log.result_summary?.runs
                        ? `${log.result_summary.runs.length} pares procesados`
                        : log.result_summary?.reason || '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="rounded-xl border border-dashed border-gray-700/60 bg-dark-400/30 p-6 text-sm text-gray-500">
            Aún no hay ejecuciones de scheduler registradas.
          </div>
        )}
      </div>

      {/* Recurring Email Reports — professional panel */}
      <div className="glass-card overflow-hidden">
        <div className="px-6 pt-6 pb-5 border-b border-gray-700/40 flex flex-wrap items-start justify-between gap-4">
          <div className="flex items-start gap-4">
            <div className="flex-shrink-0 p-2.5 rounded-xl bg-gradient-to-br from-emerald-600 to-emerald-500 shadow-lg shadow-emerald-500/20">
              <Mail className="h-5 w-5 text-white" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-gray-100">Reportes por Email</h2>
              <p className="text-sm text-gray-500 mt-0.5">Programaciones automáticas recurrentes</p>
            </div>
          </div>
          <div className="flex items-center gap-5">
            <div className="hidden sm:flex items-center gap-4 text-sm">
              <span className="text-gray-500">
                <span className="font-semibold text-gray-100">{reportSchedules.length}</span> total
              </span>
              <span className="text-gray-500">
                <span className="font-semibold text-emerald-400">
                  {reportSchedules.filter((s) => s.is_active).length}
                </span>{' '}activas
              </span>
            </div>
            <button
              type="button"
              onClick={() => setShowReportScheduleModal(true)}
              className="btn-primary inline-flex items-center gap-2 text-sm"
            >
              <Plus className="h-4 w-4" />
              Nueva
            </button>
          </div>
        </div>

        {reportSchedules.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="table-glass">
              <thead>
                <tr>
                  <th>Nombre</th>
                  <th>Tipo</th>
                  <th>Frecuencia</th>
                  <th>Destinatarios</th>
                  <th>Próxima ejecución</th>
                  <th>Estado</th>
                  <th className="text-right">Acción</th>
                </tr>
              </thead>
              <tbody>
                {reportSchedules.map((schedule) => (
                  <tr key={schedule.id}>
                    <td>
                      <p className="font-medium text-gray-200">{schedule.name}</p>
                    </td>
                    <td>
                      <div className="flex items-center gap-1.5 text-sm text-gray-400">
                        {schedule.report_type === 'billing_summary' ? (
                          <><Receipt className="h-3.5 w-3.5 text-primary-400 flex-shrink-0" /><span>Billing</span></>
                        ) : (
                          <><BarChart3 className="h-3.5 w-3.5 text-emerald-400 flex-shrink-0" /><span>Cobranza</span></>
                        )}
                      </div>
                    </td>
                    <td>
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        schedule.frequency === 'daily'
                          ? 'bg-sky-500/10 text-sky-300'
                          : schedule.frequency === 'weekly'
                          ? 'bg-violet-500/10 text-violet-300'
                          : 'bg-amber-500/10 text-amber-300'
                      }`}>
                        {schedule.frequency === 'daily' ? 'Diaria' : schedule.frequency === 'weekly' ? 'Semanal' : 'Mensual'}
                      </span>
                    </td>
                    <td>
                      <div className="flex items-center gap-1.5 text-xs text-gray-400">
                        <Users className="h-3.5 w-3.5 flex-shrink-0" />
                        <span>{schedule.recipients?.length ?? 0} correo{schedule.recipients?.length !== 1 ? 's' : ''}</span>
                      </div>
                    </td>
                    <td className="text-xs text-gray-400">
                      {schedule.next_run_at
                        ? new Date(schedule.next_run_at).toLocaleString('es-CR')
                        : '—'}
                    </td>
                    <td>
                      <span className={schedule.is_active ? 'badge-success' : 'badge-neutral'}>
                        {schedule.is_active ? 'Activo' : 'Inactivo'}
                      </span>
                    </td>
                    <td className="text-right">
                      <button
                        type="button"
                        onClick={() => runReportScheduleNow(schedule.id)}
                        disabled={runningReportScheduleId === schedule.id}
                        className="inline-flex items-center gap-1.5 rounded-lg border border-emerald-500/20 bg-emerald-500/10 px-3 py-1.5 text-xs font-medium text-emerald-300 transition-colors hover:bg-emerald-500/20 disabled:opacity-50"
                      >
                        <PlayCircle className="h-3.5 w-3.5" />
                        {runningReportScheduleId === schedule.id ? 'Enviando…' : 'Ejecutar'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center gap-4 py-16 px-6 text-center">
            <div className="p-5 rounded-2xl bg-gradient-to-br from-dark-300 to-dark-400/60 border border-gray-700/40">
              <Mail className="h-9 w-9 text-gray-600" />
            </div>
            <div>
              <p className="text-sm font-medium text-gray-300">Sin programaciones todavía</p>
              <p className="text-xs text-gray-500 mt-1 max-w-xs">
                Crea tu primera programación para recibir reportes automáticos en tu bandeja.
              </p>
            </div>
            <button
              type="button"
              onClick={() => setShowReportScheduleModal(true)}
              className="btn-primary inline-flex items-center gap-2 text-sm mt-1"
            >
              <Plus className="h-4 w-4" />
              Crear primera programación
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default FinancePage;
