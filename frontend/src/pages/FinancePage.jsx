import React, { useEffect, useState } from 'react';
import toast from 'react-hot-toast';
import {
  AlertTriangle, BadgeCheck, BarChart3, Building2, Calendar, CheckCircle2, Coins, Clock,
  Download, ExternalLink, FileWarning, FileX2, Landmark, Mail, Plus, PlayCircle, Receipt,
  RefreshCw, Send, TrendingDown, Users, Wallet, X, PenSquare, Trash2, MousePointer,
} from 'lucide-react';
import { Area, AreaChart, Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

import { billingService } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import { showConfirm } from '../services/dialogs';

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
  const isEnglish = document.documentElement.lang === 'en';
  const t = {
    title: isEnglish ? 'Run Billing Batch' : 'Ejecutar Batch de Cobro',
    subtitle: isEnglish ? 'Invoice all organizations with overdue billing.' : 'Factura todas las organizaciones con cobro vencido.',
    fiscalProfile: isEnglish ? 'Fiscal Profile' : 'Perfil Fiscal',
    selectFiscal: isEnglish ? 'Select a fiscal profile...' : 'Selecciona un perfil fiscal...',
    billedProduct: isEnglish ? 'Product to bill' : 'Producto a facturar',
    selectProduct: isEnglish ? 'Select a product...' : 'Selecciona un producto...',
    cancel: isEnglish ? 'Cancel' : 'Cancelar',
    running: isEnglish ? 'Running...' : 'Ejecutando...',
    run: isEnglish ? 'Run Batch' : 'Ejecutar Batch',
  };
  const [form, setForm] = useState({ fiscal_profile: '', product: '' });
  const canSubmit = form.fiscal_profile && form.product && !loading;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="glass-card w-full max-w-md p-6">
        <div className="flex items-start justify-between gap-4 mb-4">
          <div>
            <h2 className="text-lg font-semibold text-gray-100">{t.title}</h2>
            <p className="mt-1 text-sm text-gray-400">
              {t.subtitle}
            </p>
          </div>
          <button type="button" onClick={onClose} className="text-gray-500 hover:text-gray-200">
            <X className="h-5 w-5" />
          </button>
        </div>
        <div className="space-y-4">
          <div>
            <label className="block text-sm text-gray-400 mb-1.5">{t.fiscalProfile}</label>
            <select className="input-glass w-full" value={form.fiscal_profile}
              onChange={(e) => setForm((f) => ({ ...f, fiscal_profile: e.target.value }))}>
              <option value="">{t.selectFiscal}</option>
              {fiscalProfiles.map((fp) => (
                <option key={fp.id} value={fp.id}>{fp.legal_name} — {fp.tax_id}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1.5">{t.billedProduct}</label>
            <select className="input-glass w-full" value={form.product}
              onChange={(e) => setForm((f) => ({ ...f, product: e.target.value }))}>
              <option value="">{t.selectProduct}</option>
              {products.map((p) => (
                <option key={p.id} value={p.id}>{p.name} ({p.code})</option>
              ))}
            </select>
          </div>
        </div>
        <div className="mt-6 flex justify-end gap-3">
          <button type="button" onClick={onClose} className="btn-secondary">{t.cancel}</button>
          <button type="button" onClick={() => onSubmit(form)} disabled={!canSubmit}
            className="btn-primary inline-flex items-center gap-2">
            <PlayCircle className="h-4 w-4" />
            {loading ? t.running : t.run}
          </button>
        </div>
      </div>
    </div>
  );
};

const DAYS_OF_WEEK_LABELS_ES = ['Dom', 'Lun', 'Mar', 'Mie', 'Jue', 'Vie', 'Sab'];
const DAYS_OF_WEEK_LABELS_EN = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

const ReportScheduleModal = ({ onClose, onSubmit, loading, initialData = null }) => {
  const isEnglish = document.documentElement.lang === 'en';
  const t = {
    edit: isEnglish ? 'Edit Schedule' : 'Editar Programacion',
    create: isEnglish ? 'New Schedule' : 'Nueva Programacion',
    subtitle: isEnglish ? 'Automatic report delivery by email' : 'Envios automaticos de reportes por email',
    reportName: isEnglish ? 'Report name' : 'Nombre del reporte',
    reportNamePlaceholder: isEnglish ? 'Ex. Weekly financial summary' : 'Ej. Resumen financiero semanal',
    reportType: isEnglish ? 'Report type' : 'Tipo de reporte',
    billingSummary: isEnglish ? 'Billing Summary' : 'Resumen Billing',
    billingSummaryDesc: isEnglish ? 'Revenue, invoices, KPIs' : 'Ingresos, facturas, KPIs',
    collectionSnapshot: isEnglish ? 'Collections Snapshot' : 'Snapshot Cobranza',
    collectionSnapshotDesc: isEnglish ? 'Pending balances' : 'Cuentas pendientes',
    frequency: isEnglish ? 'Frequency' : 'Frecuencia',
    daily: isEnglish ? 'Daily' : 'Diaria',
    weekly: isEnglish ? 'Weekly' : 'Semanal',
    monthly: isEnglish ? 'Monthly' : 'Mensual',
    weekday: isEnglish ? 'Day of week' : 'Dia de la semana',
    dayOfMonth: isEnglish ? 'Day of month' : 'Dia del mes',
    dayPrefix: isEnglish ? 'Day' : 'Dia',
    sendTime: isEnglish ? 'Send time' : 'Hora de envio',
    recipients: isEnglish ? 'Recipients' : 'Destinatarios',
    recipientsHelp: isEnglish ? 'Separate multiple emails with comma.' : 'Separa multiples correos con coma.',
    statusActive: isEnglish ? 'Active' : 'Activo',
    statusInactive: isEnglish ? 'Inactive' : 'Inactivo',
    cancel: isEnglish ? 'Cancel' : 'Cancelar',
    saving: isEnglish ? 'Saving...' : 'Guardando...',
    saveChanges: isEnglish ? 'Save changes' : 'Guardar cambios',
    createSchedule: isEnglish ? 'Create schedule' : 'Crear programacion',
  };
  const dayLabels = isEnglish ? DAYS_OF_WEEK_LABELS_EN : DAYS_OF_WEEK_LABELS_ES;
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

  const isEditMode = Boolean(initialData?.id);

  useEffect(() => {
    if (!initialData) {
      setForm({
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
      return;
    }

    setForm({
      name: initialData.name || '',
      report_type: initialData.report_type || 'billing_summary',
      frequency: initialData.frequency || 'daily',
      day_of_week: initialData.day_of_week ?? 1,
      day_of_month: initialData.day_of_month ?? 1,
      hour: initialData.hour ?? 7,
      minute: initialData.minute ?? 0,
      recipients: Array.isArray(initialData.recipients) ? initialData.recipients.join(', ') : '',
      is_active: Boolean(initialData.is_active),
    });
  }, [initialData]);

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
            <h2 className="text-lg font-semibold text-gray-100">
              {isEditMode ? t.edit : t.create}
            </h2>
            <p className="mt-0.5 text-sm text-gray-500">{t.subtitle}</p>
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
              {t.reportName}
            </label>
            <input
              className="input-glass w-full"
              placeholder={t.reportNamePlaceholder}
              value={form.name}
              onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
            />
          </div>

          {/* Report type — card selector */}
          <div>
            <label className="mb-2 block text-xs font-medium tracking-wide uppercase text-gray-500">
              {t.reportType}
            </label>
            <div className="grid grid-cols-2 gap-3">
              {[
                { value: 'billing_summary', icon: Receipt, label: t.billingSummary, desc: t.billingSummaryDesc },
                { value: 'collections_snapshot', icon: BarChart3, label: t.collectionSnapshot, desc: t.collectionSnapshotDesc },
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
              {t.frequency}
            </label>
            <div className="grid grid-cols-3 gap-2">
              {[
                { value: 'daily', label: t.daily },
                { value: 'weekly', label: t.weekly },
                { value: 'monthly', label: t.monthly },
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
                {t.weekday}
              </label>
              <div className="flex gap-1.5">
                {dayLabels.map((day, i) => (
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
                {t.dayOfMonth}
              </label>
              <select
                className="input-glass w-full"
                value={form.day_of_month}
                onChange={(e) => setForm((f) => ({ ...f, day_of_month: e.target.value }))}
              >
                {Array.from({ length: 31 }, (_, i) => i + 1).map((d) => (
                  <option key={d} value={d}>{t.dayPrefix} {d}</option>
                ))}
              </select>
            </div>
          )}

          {/* Time picker */}
          <div>
            <label className="mb-1.5 block text-xs font-medium tracking-wide uppercase text-gray-500">
              {t.sendTime}
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
              {t.recipients}
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
            <p className="mt-1 text-xs text-gray-600">{t.recipientsHelp}</p>
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
              {form.is_active ? t.statusActive : t.statusInactive}
            </span>
          </div>
          <div className="flex gap-3">
            <button type="button" onClick={onClose} className="btn-secondary text-sm">{t.cancel}</button>
            <button
              type="button"
              onClick={submit}
              disabled={!canSubmit}
              className="btn-primary inline-flex items-center gap-2 text-sm"
            >
              <Send className="h-4 w-4" />
              {loading ? t.saving : isEditMode ? t.saveChanges : t.createSchedule}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

const PAYMENT_METHODS = ['sinpe', 'bank_transfer', 'cash', 'card', 'check', 'deposit', 'other'];
const PAYMENT_CHART_METRIC_KEY = 'finance.paymentMethodChartMetric';

const RegisterPaymentModal = ({ invoices, onClose, onRegistered }) => {
  const isEnglish = document.documentElement.lang === 'en';
  const t = {
    saved: isEnglish ? 'Pending payment registered successfully.' : 'Pago pendiente registrado correctamente.',
    saveError: isEnglish ? 'Could not register payment.' : 'No se pudo registrar el pago.',
    title: isEnglish ? 'Register Pending Payment' : 'Registrar Pago Pendiente',
    subtitle: isEnglish ? 'Payment remains pending until reconciliation.' : 'El pago quedara en estado pendiente hasta ser conciliado.',
    invoice: isEnglish ? 'Invoice' : 'Factura',
    selectInvoice: isEnglish ? 'Select an invoice...' : 'Selecciona una factura...',
    method: isEnglish ? 'Payment method' : 'Metodo de pago',
    reference: isEnglish ? 'Reference / transfer No.' : 'Referencia / N de transferencia',
    amount: isEnglish ? 'Amount (CRC)' : 'Monto (CRC)',
    notes: isEnglish ? 'Notes (optional)' : 'Notas (opcional)',
    cancel: isEnglish ? 'Cancel' : 'Cancelar',
    registering: isEnglish ? 'Registering...' : 'Registrando...',
    register: isEnglish ? 'Register Payment' : 'Registrar Pago',
  };
  const [form, setForm] = useState({ invoice: '', method: 'bank_transfer', reference: '', amount: '', notes: '' });
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
      toast.success(t.saved);
      onRegistered();
      onClose();
    } catch (err) {
      toast.error(err.response?.data?.detail || t.saveError);
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
            <h2 className="text-lg font-semibold text-gray-100">{t.title}</h2>
            <p className="mt-1 text-sm text-gray-400">{t.subtitle}</p>
          </div>
          <button type="button" onClick={onClose} className="text-gray-500 hover:text-gray-200">
            <X className="h-5 w-5" />
          </button>
        </div>
        <div className="space-y-4">
          <div>
            <label className="block text-sm text-gray-400 mb-1.5">{t.invoice}</label>
            <select className="input-glass w-full" value={form.invoice}
              onChange={(e) => setForm((f) => ({ ...f, invoice: e.target.value }))}>
              <option value="">{t.selectInvoice}</option>
              {invoices.filter((inv) => ['accepted', 'pending'].includes(inv.status)).map((inv) => (
                <option key={inv.id} value={inv.id}>{inv.invoice_number} — {inv.organization_name}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1.5">{t.method}</label>
            <select className="input-glass w-full" value={form.method}
              onChange={(e) => setForm((f) => ({ ...f, method: e.target.value }))}>
              {PAYMENT_METHODS.map((m) => <option key={m} value={m}>{paymentMethodLabel(m, isEnglish)}</option>)}
            </select>
          </div>
          {field('reference', t.reference)}
          {field('amount', t.amount, 'number', { min: 0, step: '0.01' })}
          <div>
            <label className="block text-sm text-gray-400 mb-1.5">{t.notes}</label>
            <textarea rows={2} className="input-glass w-full resize-none" value={form.notes}
              onChange={(e) => setForm((f) => ({ ...f, notes: e.target.value }))} />
          </div>
        </div>
        <div className="mt-6 flex justify-end gap-3">
          <button type="button" onClick={onClose} className="btn-secondary">{t.cancel}</button>
          <button type="button" onClick={submit} disabled={!canSubmit}
            className="btn-primary inline-flex items-center gap-2">
            <Plus className="h-4 w-4" />
            {saving ? t.registering : t.register}
          </button>
        </div>
      </div>
    </div>
  );
};

const InvoiceDrawer = ({ invoiceId, onClose, onCreditNoteIssued }) => {
  const isEnglish = document.documentElement.lang === 'en';
  const t = {
    loadError: isEnglish ? 'Could not load invoice.' : 'No se pudo cargar la factura.',
    creditReasonRequired: isEnglish ? 'Enter credit note reason.' : 'Ingresa el motivo de la nota de credito.',
    creditIssued: isEnglish ? 'Credit Note issued' : 'Nota de Credito emitida',
    creditIssueError: isEnglish ? 'Could not issue credit note.' : 'No se pudo emitir la nota de credito.',
    xmlError: isEnglish ? 'Could not generate XML.' : 'No se pudo generar el XML.',
    invoiceDetail: isEnglish ? 'Invoice Detail' : 'Detalle de Factura',
    commercialStatus: isEnglish ? 'Commercial status' : 'Estado comercial',
    taxStatus: isEnglish ? 'Tax authority status' : 'Estado Hacienda',
    receiver: isEnglish ? 'Receiver' : 'Receptor',
    taxId: isEnglish ? 'Tax ID' : 'RUC/Cedula',
    email: 'Email',
    currency: isEnglish ? 'Currency' : 'Moneda',
    issuedAt: isEnglish ? 'Issued' : 'Emitido',
    dueAt: isEnglish ? 'Due date' : 'Vence',
    subtotal: isEnglish ? 'Subtotal' : 'Subtotal',
    discount: isEnglish ? 'Discount' : 'Descuento',
    tax: isEnglish ? 'Tax' : 'Impuesto',
    total: isEnglish ? 'Total' : 'Total',
    taxData: isEnglish ? 'Tax authority data' : 'Datos Hacienda CR',
    seq: isEnglish ? 'Sequence' : 'Consecutivo',
    key: isEnglish ? 'Numeric key' : 'Clave numerica',
    trackId: isEnglish ? 'Track ID' : 'Track ID',
    submitted: isEnglish ? 'Submitted' : 'Enviado',
    replied: isEnglish ? 'Responded' : 'Respondido',
    message: isEnglish ? 'Message' : 'Mensaje',
    lineItems: isEnglish ? 'Line items' : 'Lineas de detalle',
    cabys: 'CAByS',
    generatingXml: isEnglish ? 'Generating XML...' : 'Generando XML...',
    downloadXml: isEnglish ? 'Download Tax XML' : 'Descargar XML Hacienda',
    cancel: isEnglish ? 'Cancel' : 'Cancelar',
    issueCredit: isEnglish ? 'Issue Credit Note' : 'Emitir Nota de Credito',
    reasonPlaceholder: isEnglish ? 'Credit note reason...' : 'Motivo de la nota de credito...',
    issuing: isEnglish ? 'Issuing...' : 'Emitiendo...',
    confirmCredit: isEnglish ? 'Confirm Credit Note' : 'Confirmar Nota de Credito',
  };
  const [detail, setDetail] = useState(null);
  const [downloading, setDownloading] = useState(false);
  const [showCreditNoteForm, setShowCreditNoteForm] = useState(false);
  const [creditNoteReason, setCreditNoteReason] = useState('');
  const [issuingCreditNote, setIssuingCreditNote] = useState(false);

  useEffect(() => {
    if (!invoiceId) return;
    billingService.getInvoiceDetail(invoiceId).then(setDetail).catch(() => toast.error(t.loadError));
  }, [invoiceId]);

  const issueCreditNote = async () => {
    if (!creditNoteReason.trim()) {
      toast.error(t.creditReasonRequired);
      return;
    }
    try {
      setIssuingCreditNote(true);
      const result = await billingService.createCreditNote(invoiceId, creditNoteReason.trim());
      toast.success(`${t.creditIssued}: ${result.credit_note_number}`);
      setShowCreditNoteForm(false);
      setCreditNoteReason('');
      if (onCreditNoteIssued) onCreditNoteIssued();
      onClose();
    } catch (err) {
      toast.error(err.response?.data?.detail || t.creditIssueError);
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
      toast.error(t.xmlError);
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
            <p className="text-xs uppercase tracking-widest text-primary-300">{t.invoiceDetail}</p>
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
                <p className="text-xs text-gray-500 mb-1">{t.commercialStatus}</p>
                <span className={statusBadge(detail.status)}>{detail.status}</span>
              </div>
              <div className="rounded-xl bg-dark-400/40 border border-gray-700/50 p-4">
                <p className="text-xs text-gray-500 mb-1">{t.taxStatus}</p>
                <span className={haciendaBadge(detail.hacienda_status)}>{detail.hacienda_status}</span>
              </div>
            </div>

            <div className="rounded-xl bg-dark-400/40 border border-gray-700/50 p-4 space-y-2">
              <Row label={t.receiver} value={detail.receiver_name} />
              <Row label={t.taxId} value={detail.receiver_tax_id || '—'} />
              <Row label={t.email} value={detail.receiver_email || '—'} />
              <Row label={t.currency} value={detail.currency} />
              <Row label={t.issuedAt} value={detail.issued_at ? new Date(detail.issued_at).toLocaleString(isEnglish ? 'en-US' : 'es-CR') : '—'} />
              <Row label={t.dueAt} value={detail.due_date || '—'} />
            </div>

            <div className="rounded-xl bg-dark-400/40 border border-gray-700/50 p-4 space-y-2">
              <Row label={t.subtotal} value={formatMoney(detail.subtotal, isEnglish)} />
              <Row label={t.discount} value={formatMoney(detail.discount_total, isEnglish)} />
              <Row label={t.tax} value={formatMoney(detail.tax_total, isEnglish)} />
              <div className="border-t border-gray-700/50 pt-2">
                <Row label={t.total} value={<span className="text-lg font-bold text-primary-300">{formatMoney(detail.total, isEnglish)}</span>} />
              </div>
            </div>

            {detail.consecutive_number && (
              <div className="rounded-xl bg-dark-400/40 border border-gray-700/50 p-4 space-y-2">
                <p className="text-xs uppercase tracking-widest text-gray-500 mb-2">{t.taxData}</p>
                <Row label={t.seq} value={<code className="text-xs text-primary-200">{detail.consecutive_number}</code>} />
                <Row label={t.key} value={<code className="text-[10px] text-primary-200 break-all">{detail.numeric_key}</code>} />
                {detail.hacienda_track_id && <Row label={t.trackId} value={detail.hacienda_track_id} />}
                {detail.submitted_at && <Row label={t.submitted} value={new Date(detail.submitted_at).toLocaleString(isEnglish ? 'en-US' : 'es-CR')} />}
                {detail.responded_at && <Row label={t.replied} value={new Date(detail.responded_at).toLocaleString(isEnglish ? 'en-US' : 'es-CR')} />}
                {detail.hacienda_message && <Row label={t.message} value={detail.hacienda_message} />}
              </div>
            )}

            {detail.lines && detail.lines.length > 0 && (
              <div className="rounded-xl bg-dark-400/40 border border-gray-700/50 p-4">
                <p className="text-xs uppercase tracking-widest text-gray-500 mb-3">{t.lineItems}</p>
                <div className="space-y-2">
                  {detail.lines.map((line, i) => (
                    <div key={i} className="flex items-start justify-between gap-2 border-b border-gray-700/30 pb-2 last:border-0 last:pb-0">
                      <div>
                        <p className="text-gray-200">{line.description}</p>
                        {line.cabys_code && <p className="text-xs text-gray-500">{t.cabys}: {line.cabys_code}</p>}
                      </div>
                      <p className="shrink-0 text-primary-300 font-medium">{formatMoney(line.total, isEnglish)}</p>
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
              {downloading ? t.generatingXml : t.downloadXml}
            </button>

            {['accepted', 'paid'].includes(detail.status) && detail.status !== 'reversed' && (
              <div className="rounded-xl border border-red-500/30 bg-red-500/5 p-4 space-y-3">
                <button
                  type="button"
                  onClick={() => setShowCreditNoteForm((v) => !v)}
                  className="inline-flex items-center gap-2 text-sm text-red-300 hover:text-red-100 transition-colors"
                >
                  <FileX2 className="h-4 w-4" />
                  {showCreditNoteForm ? t.cancel : t.issueCredit}
                </button>
                {showCreditNoteForm && (
                  <div className="space-y-3">
                    <textarea
                      rows={2}
                      placeholder={t.reasonPlaceholder}
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
                      {issuingCreditNote ? t.issuing : t.confirmCredit}
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

const formatMoney = (value, isEnglish = false) => {
  const amount = Number(value || 0);
  return new Intl.NumberFormat(isEnglish ? 'en-US' : 'es-CR', { style: 'currency', currency: 'CRC', maximumFractionDigits: 2 }).format(amount);
};

const paymentMethodLabel = (method, isEnglish = false) => {
  const labels = {
    sinpe: isEnglish ? 'SINPE' : 'SINPE',
    bank_transfer: isEnglish ? 'Bank transfer' : 'Transferencia bancaria',
    cash: isEnglish ? 'Cash' : 'Efectivo',
    card: isEnglish ? 'Card (offline)' : 'Tarjeta (offline)',
    check: isEnglish ? 'Check' : 'Cheque',
    deposit: isEnglish ? 'Bank deposit' : 'Deposito bancario',
    other: isEnglish ? 'Other' : 'Otro',
  };

  return labels[method] || method;
};

const PendingPaymentsList = ({ payments, onAction }) => {
  const isEnglish = document.documentElement.lang === 'en';
  const t = {
    confirmed: isEnglish ? 'Payment confirmed.' : 'Pago confirmado.',
    rejected: isEnglish ? 'Payment rejected.' : 'Pago rechazado.',
    actionError: isEnglish ? 'Action could not be processed.' : 'No se pudo procesar la accion.',
    reference: isEnglish ? 'Reference' : 'Referencia',
    method: isEnglish ? 'Method' : 'Metodo',
    amount: isEnglish ? 'Amount' : 'Monto',
    notes: isEnglish ? 'Notes' : 'Notas',
    actions: isEnglish ? 'Actions' : 'Acciones',
    confirm: isEnglish ? 'Confirm' : 'Confirmar',
    reject: isEnglish ? 'Reject' : 'Rechazar',
  };
  const [actingId, setActingId] = useState(null);

  const act = async (paymentId, action) => {
    try {
      setActingId(paymentId);
      if (action === 'confirm') await billingService.confirmPayment(paymentId);
      else await billingService.rejectPayment(paymentId);
      toast.success(action === 'confirm' ? t.confirmed : t.rejected);
      onAction();
    } catch (err) {
      toast.error(err.response?.data?.detail || t.actionError);
    } finally {
      setActingId(null);
    }
  };

  return (
    <div className="overflow-x-auto">
      <table className="table-glass">
        <thead>
          <tr>
            <th>{t.reference}</th>
            <th>{t.method}</th>
            <th>{t.amount}</th>
            <th>{t.notes}</th>
            <th>{t.actions}</th>
          </tr>
        </thead>
        <tbody>
          {payments.map((p) => (
            <tr key={p.id}>
              <td className="font-mono text-xs">{p.reference || '—'}</td>
              <td>{paymentMethodLabel(p.method, isEnglish)}</td>
              <td>{formatMoney(p.amount, isEnglish)}</td>
              <td className="text-xs text-gray-400">{p.notes || '—'}</td>
              <td>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    disabled={actingId === p.id}
                    onClick={() => act(p.id, 'confirm')}
                    className="rounded-lg bg-emerald-500/15 border border-emerald-500/30 px-3 py-1 text-xs text-emerald-300 hover:bg-emerald-500/25 transition-colors disabled:opacity-50"
                  >
                    {t.confirm}
                  </button>
                  <button
                    type="button"
                    disabled={actingId === p.id}
                    onClick={() => act(p.id, 'reject')}
                    className="rounded-lg bg-red-500/15 border border-red-500/30 px-3 py-1 text-xs text-red-300 hover:bg-red-500/25 transition-colors disabled:opacity-50"
                  >
                    {t.reject}
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
  const { user } = useAuth();
  const isEnglish = user?.language === 'en';
  const t = {
    panelLoadError: isEnglish ? 'Could not load the finance panel.' : 'No fue posible cargar el panel financiero.',
    batchRequired: isEnglish ? 'Fiscal profile and product are required to run batch.' : 'Se requiere perfil fiscal y producto para ejecutar el batch.',
    batchSuccess: isEnglish ? 'Batch executed' : 'Batch ejecutado',
    batchRunError: isEnglish ? 'Could not execute batch.' : 'No fue posible ejecutar el batch.',
    csvError: isEnglish ? 'Could not export CSV.' : 'No se pudo exportar el CSV.',
    schedulerRun: isEnglish ? 'Scheduler executed: status' : 'Scheduler ejecutado: estado',
    schedulerRunError: isEnglish ? 'Could not execute scheduler.' : 'No se pudo ejecutar el scheduler.',
    reportUpdated: isEnglish ? 'Report schedule updated.' : 'Programacion de reporte actualizada.',
    reportCreated: isEnglish ? 'Report schedule created.' : 'Programacion de reporte creada.',
    reportSaveError: isEnglish ? 'Could not save schedule.' : 'No se pudo guardar la programacion.',
    reportRunOk: isEnglish ? 'Report executed and sent by email.' : 'Reporte ejecutado y enviado por email.',
    reportRunError: isEnglish ? 'Could not execute report.' : 'No se pudo ejecutar el reporte.',
    scheduleDeleted: isEnglish ? 'Schedule deleted.' : 'Programacion eliminada.',
    scheduleDeleteError: isEnglish ? 'Could not delete schedule.' : 'No se pudo eliminar la programacion.',
    deleteScheduleConfirm: isEnglish ? 'Delete schedule' : 'Eliminar la programacion',
    alerts: isEnglish ? 'Operational Alerts' : 'Alertas Operativas',
    financeTitle: isEnglish ? 'Multi-product financial control' : 'Control financiero multi-producto',
    financeSubtitle: isEnglish ? 'Total revenue, receivables, product performance, customer behavior and backoffice batch operations.' : 'Revenue total, cuentas por cobrar, rendimiento por producto, comportamiento por cliente y operaciones de batch para el backoffice de Smart3AI.',
    runningBatch: isEnglish ? 'Running batch...' : 'Ejecutando batch...',
    runBatch: isEnglish ? 'Run Billing Batch' : 'Ejecutar Batch de Cobro',
    netRevenue: isEnglish ? 'Net Revenue' : 'Ingresos Netos',
    receivables: isEnglish ? 'Accounts Receivable' : 'Cuentas por Cobrar',
    taxCollected: isEnglish ? 'Tax Collected' : 'Impuesto Recaudado',
    activeProducts: isEnglish ? 'Active Products' : 'Productos Activos',
    activeSubscriptions: isEnglish ? 'Active Subscriptions' : 'Suscripciones Activas',
    trialConversion: isEnglish ? 'Trial Conversion' : 'Conversion de Trials',
    revenueTimeline: isEnglish ? 'Revenue Timeline' : 'Timeline de Revenue',
    revenueByProduct: isEnglish ? 'Revenue by Product' : 'Revenue por Producto',
    revenueByOrg: isEnglish ? 'Revenue by Organization' : 'Revenue por Organizacion',
    recentInvoices: isEnglish ? 'Recent invoices' : 'Facturas recientes',
    latestBatch: isEnglish ? 'Latest Batch' : 'Ultimo Batch',
    productDashboard: isEnglish ? 'Product Dashboard' : 'Dashboard por Producto',
    reconciliation: isEnglish ? 'Bank Reconciliation' : 'Conciliacion Bancaria',
    scheduler: isEnglish ? 'Automatic Scheduler' : 'Scheduler Automatico',
    emailReports: isEnglish ? 'Email Reports' : 'Reportes por Email',
    paidInvoicesHelper: isEnglish ? 'paid invoices' : 'facturas pagadas',
    pendingDocsHelper: isEnglish ? 'pending documents' : 'documentos pendientes',
    crTaxBase: isEnglish ? 'CR operating base for tax authority' : 'Base operativa CR para Hacienda',
    catalogedProducts: isEnglish ? 'cataloged products' : 'productos catalogados',
    monthlyRecurringRevenue: isEnglish ? 'Monthly Recurring Revenue' : 'Ingresos Recurrentes Mensuales',
    annualRecurringRevenue: isEnglish ? 'Annual Recurring Revenue' : 'Ingresos Recurrentes Anuales',
    activeSubsHelper: isEnglish ? 'Active subscriptions' : 'Suscripciones en estado activo',
    churnLast30: isEnglish ? 'Cancellations in the last 30 days' : 'Cancelaciones ultimos 30 dias',
    activeTrials: isEnglish ? 'Active Trials' : 'Trials Activos',
    trialsInPeriod: isEnglish ? 'Subscriptions in trial period' : 'Suscripciones en periodo de prueba',
    trialConverted30: isEnglish ? 'Trials converted in the last 30 days' : 'Trials convertidos en ultimos 30 dias',
    monthlyEvolution: isEnglish ? 'Consolidated monthly trend' : 'Evolucion mensual consolidada',
    netRevenueComparison: isEnglish ? 'Net revenue comparison' : 'Comparativo de ingresos netos',
    topCustomers: isEnglish ? 'Top contributing customers' : 'Clientes que mas aportan a Smart3AI',
    organization: isEnglish ? 'Organization' : 'Organizacion',
    netRevenueLabel: isEnglish ? 'Net Revenue' : 'Revenue Neto',
    issued: isEnglish ? 'Issued' : 'Emitidas',
    paid: isEnglish ? 'Paid' : 'Pagadas',
    aging: 'Aging',
    agingSubtitle: isEnglish ? 'Receivables by due bucket' : 'Cuentas por cobrar por vencimiento',
    current: isEnglish ? 'Current' : 'Corriente',
    days1to30: isEnglish ? '1 to 30 days' : '1 a 30 dias',
    days31to60: isEnglish ? '31 to 60 days' : '31 a 60 dias',
    days61Plus: isEnglish ? '61+ days' : '61+ dias',
    commercialOperationalStatus: isEnglish ? 'Commercial and operational status' : 'Estado comercial y operativo',
    exportCsvTitle: isEnglish ? 'Export invoices to CSV' : 'Exportar facturas a CSV',
    exportCsv: isEnglish ? 'Export CSV' : 'Exportar CSV',
    invoice: isEnglish ? 'Invoice' : 'Factura',
    customer: isEnglish ? 'Customer' : 'Cliente',
    status: isEnglish ? 'Status' : 'Estado',
    taxAuthority: isEnglish ? 'Tax authority' : 'Hacienda',
    latestBatchSubtitle: isEnglish ? 'Operational execution report' : 'Reporte de ejecucion operativa',
    processed: isEnglish ? 'Processed' : 'Procesadas',
    skipped: isEnglish ? 'Skipped' : 'Omitidas',
    errors: isEnglish ? 'Errors' : 'Errores',
    runDate: isEnglish ? 'Run date' : 'Fecha de ejecucion',
    latestProcessed: isEnglish ? 'Latest processed' : 'Ultimas procesadas',
    billingExempt: isEnglish ? 'Billing exempt' : 'Exenta de cobro',
    exemptAmount: isEnglish ? 'Exempt' : 'Exento',
    exemptSkippedReason: isEnglish ? 'Owner organization exempt from billing' : 'Organizacion dueña exenta de cobro',
    noBatchYet: isEnglish ? 'No batch has been run from this screen yet. Once you run one, the latest operational report will appear here.' : 'Aun no se ha ejecutado un batch desde esta pantalla. Cuando lo corras, aqui quedara el ultimo reporte operativo.',
    productDashboardSubtitle: isEnglish ? 'MRR, ARR and subscriptions by catalog product' : 'MRR, ARR y suscripciones por producto del catalogo',
    product: isEnglish ? 'Product' : 'Producto',
    model: isEnglish ? 'Model' : 'Modelo',
    subscriptions: isEnglish ? 'Subscriptions' : 'Suscripciones',
    invoicesLabel: isEnglish ? 'Invoices' : 'Facturas',
    reconciliationSubtitle: isEnglish ? 'Pending payment reconciliation status' : 'Estado de pagos pendientes de conciliacion',
    registerPayment: isEnglish ? 'Register Payment' : 'Registrar Pago',
    pendingPaymentsLabel: isEnglish ? 'Pending Payments' : 'Pagos pendientes',
    confirmedLabel: isEnglish ? 'Confirmed' : 'Confirmados',
    overdueInvoices: isEnglish ? 'Overdue invoices' : 'Facturas vencidas',
    unmatched: isEnglish ? 'Unmatched' : 'Sin conciliar',
    paidInvoicesNoPayment: isEnglish ? 'Paid invoices without payment record' : 'Facturas pagadas sin registro de pago',
    pendingToReconcile: isEnglish ? 'Pending payments to reconcile' : 'Pagos pendientes de conciliar',
    byPaymentMethod: isEnglish ? 'By payment method' : 'Por tipo de pago',
    byPaymentMethodSubtitle: isEnglish ? 'Counts and amounts registered in reconciliation.' : 'Conteos y montos registrados en conciliacion.',
    byPaymentMethodChart: isEnglish ? 'Payment method amount distribution' : 'Distribucion de montos por metodo de pago',
    byPaymentMethodChartSubtitle: isEnglish ? 'Visual comparison by registered amount.' : 'Comparativo visual por monto registrado.',
    byPaymentMethodChartSubtitleCount: isEnglish ? 'Visual comparison by number of records.' : 'Comparativo visual por cantidad de registros.',
    viewAmount: isEnglish ? 'Amount' : 'Monto',
    viewCount: isEnglish ? 'Count' : 'Cantidad',
    schedulerActiveAt: isEnglish ? 'Active - runs daily at' : 'Activo - corre diario a las',
    schedulerTz: isEnglish ? 'CR time' : 'hora CR',
    schedulerDisabled: isEnglish ? 'BILLING_SCHEDULER_ENABLED=false in this environment' : 'BILLING_SCHEDULER_ENABLED=false en este entorno',
    running: isEnglish ? 'Running' : 'Corriendo',
    stopped: isEnglish ? 'Stopped' : 'Detenido',
    runNow: isEnglish ? 'Run now' : 'Ejecutar ahora',
    nextRun: isEnglish ? 'Next run' : 'Proxima ejecucion',
    triggered: isEnglish ? 'Triggered' : 'Disparado',
    finished: isEnglish ? 'Finished' : 'Finalizado',
    result: isEnglish ? 'Result' : 'Resultado',
    runsProcessed: isEnglish ? 'pairs processed' : 'pares procesados',
    noSchedulerRuns: isEnglish ? 'No scheduler runs registered yet.' : 'Aun no hay ejecuciones de scheduler registradas.',
    recurringSchedules: isEnglish ? 'Recurring automatic schedules' : 'Programaciones automaticas recurrentes',
    total: isEnglish ? 'total' : 'total',
    activePlural: isEnglish ? 'active' : 'activas',
    newLabel: isEnglish ? 'New' : 'Nueva',
    name: isEnglish ? 'Name' : 'Nombre',
    type: isEnglish ? 'Type' : 'Tipo',
    frequencyLabel: isEnglish ? 'Frequency' : 'Frecuencia',
    recipientsLabel: isEnglish ? 'Recipients' : 'Destinatarios',
    nextRunAt: isEnglish ? 'Next run' : 'Proxima ejecucion',
    daily: isEnglish ? 'Daily' : 'Diaria',
    weekly: isEnglish ? 'Weekly' : 'Semanal',
    monthly: isEnglish ? 'Monthly' : 'Mensual',
    collections: isEnglish ? 'Collections' : 'Cobranza',
    emailsCount: isEnglish ? 'email' : 'correo',
    active: isEnglish ? 'Active' : 'Activo',
    inactive: isEnglish ? 'Inactive' : 'Inactivo',
    runNowTitle: isEnglish ? 'Run now' : 'Ejecutar ahora',
    editTitle: isEnglish ? 'Edit' : 'Editar',
    deactivate: isEnglish ? 'Deactivate' : 'Desactivar',
    activate: isEnglish ? 'Activate' : 'Activar',
    delete: isEnglish ? 'Delete' : 'Eliminar',
    noSchedulesYet: isEnglish ? 'No schedules yet' : 'Sin programaciones todavia',
    createFirstScheduleDesc: isEnglish ? 'Create your first schedule to receive automatic reports in your inbox.' : 'Crea tu primera programacion para recibir reportes automaticos en tu bandeja.',
    createFirstSchedule: isEnglish ? 'Create first schedule' : 'Crear primera programacion',
    scheduleActivated: isEnglish ? 'Schedule activated.' : 'Programacion activada.',
    scheduleDeactivated: isEnglish ? 'Schedule deactivated.' : 'Programacion desactivada.',
    scheduleToggleError: isEnglish ? 'Could not update status.' : 'No se pudo actualizar el estado.',
    landingAnalytics: isEnglish ? 'Landing analytics' : 'Analitica del landing',
    landingAnalyticsSubtitle: isEnglish ? 'A/B performance and CTA behavior by date and campaign.' : 'Desempeño A/B y comportamiento CTA por fecha y campaña.',
    campaignFilter: isEnglish ? 'Campaign' : 'Campaña',
    fromDate: isEnglish ? 'From' : 'Desde',
    toDate: isEnglish ? 'To' : 'Hasta',
    applyFilters: isEnglish ? 'Apply filters' : 'Aplicar filtros',
    winnerVariant: isEnglish ? 'Winning variant' : 'Variante ganadora',
    noWinnerYet: isEnglish ? 'Not enough data' : 'Sin datos suficientes',
    totalEvents: isEnglish ? 'Total events' : 'Eventos totales',
    ctaClicks: isEnglish ? 'CTA clicks' : 'Clicks CTA',
    variant: isEnglish ? 'Variant' : 'Variante',
    rate: isEnglish ? 'Rate' : 'Tasa',
    dailyBreakdown: isEnglish ? 'Daily breakdown' : 'Desglose diario',
    noLandingData: isEnglish ? 'No landing analytics data for selected filters.' : 'No hay datos de analitica para los filtros seleccionados.',
  };
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
  const [editingReportSchedule, setEditingReportSchedule] = useState(null);
  const [savingReportSchedule, setSavingReportSchedule] = useState(false);
  const [runningReportScheduleId, setRunningReportScheduleId] = useState(null);
  const [togglingReportScheduleId, setTogglingReportScheduleId] = useState(null);
  const [deletingReportScheduleId, setDeletingReportScheduleId] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [churnData, setChurnData] = useState(null);
  const [reconciliation, setReconciliation] = useState(null);
  const [productDashboard, setProductDashboard] = useState([]);
  const [pendingPayments, setPendingPayments] = useState([]);
  const [showRegisterPayment, setShowRegisterPayment] = useState(false);
  const [landingAnalytics, setLandingAnalytics] = useState(null);
  const [landingFilters, setLandingFilters] = useState(() => {
    const now = new Date();
    const from = new Date(now);
    from.setDate(now.getDate() - 30);
    const fmt = (date) => date.toISOString().slice(0, 10);
    return {
      campaign: '',
      from: fmt(from),
      to: fmt(now),
    };
  });
  const [paymentChartMetric, setPaymentChartMetric] = useState(() => {
    try {
      const saved = typeof window !== 'undefined' ? window.localStorage.getItem(PAYMENT_CHART_METRIC_KEY) : null;
      return saved === 'count' ? 'count' : 'amount';
    } catch {
      return 'amount';
    }
  });

  const loadData = async () => {
    try {
      setLoading(true);
      const [summaryData, productData, organizationData, timelineData, receivableData, invoiceData, fpData, prodData, schedData, reportSchedulesData, alertsData, churnData_, reconciliationData, dashboardData, landingAnalyticsData] = await Promise.all([
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
        billingService.getLandingAnalyticsSummary(landingFilters).catch(() => null),
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
      setLandingAnalytics(landingAnalyticsData);

      // grab pending payments for reconciliation panel
      const allInvoices = invoiceData.results || invoiceData || [];
      billingService.getInvoices({ ordering: '-created_at', page_size: 200 }).then((inv) => {
        const list = inv.results || inv || [];
        setPendingPayments(list.flatMap((i) => (i.payments || [])).filter((p) => p.status === 'pending'));
      }).catch(() => {});
    } catch (error) {
      console.error('Finance dashboard error:', error);
      toast.error(t.panelLoadError);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const applyLandingFilters = async () => {
    try {
      const payload = await billingService.getLandingAnalyticsSummary(landingFilters);
      setLandingAnalytics(payload);
    } catch {
      toast.error(t.panelLoadError);
    }
  };

  useEffect(() => {
    try {
      if (typeof window !== 'undefined') {
        window.localStorage.setItem(PAYMENT_CHART_METRIC_KEY, paymentChartMetric);
      }
    } catch {
      // Ignore localStorage write errors (private mode, quota, etc.)
    }
  }, [paymentChartMetric]);

  const runBatch = async ({ fiscal_profile, product }) => {
    if (!fiscal_profile || !product) {
      toast.error(t.batchRequired);
      return;
    }

    try {
      setRunningBatch(true);
      const report = await billingService.runBatch({ fiscal_profile, product });
      setBatchReport(report);
      setShowBatchModal(false);
      toast.success(`${t.batchSuccess}: ${report.summary.processed_count}`);
      await loadData();
    } catch (error) {
      console.error('Batch billing error:', error);
      toast.error(error.response?.data?.detail || t.batchRunError);
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
      toast.error(t.csvError);
    }
  };

  const triggerSchedulerNow = async () => {
    try {
      setTriggeringScheduler(true);
      const result = await billingService.triggerSchedulerNow();
      toast.success(`${t.schedulerRun} ${result.status}`);
      const schedData = await billingService.getSchedulerStatus().catch(() => null);
      if (schedData) setScheduler(schedData);
    } catch (error) {
      toast.error(error.response?.data?.detail || t.schedulerRunError);
    } finally {
      setTriggeringScheduler(false);
    }
  };

  const saveReportSchedule = async (payload) => {
    try {
      setSavingReportSchedule(true);
      if (editingReportSchedule?.id) {
        await billingService.updateReportSchedule(editingReportSchedule.id, payload);
        toast.success(t.reportUpdated);
      } else {
        await billingService.createReportSchedule(payload);
        toast.success(t.reportCreated);
      }
      setShowReportScheduleModal(false);
      setEditingReportSchedule(null);
      await loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || t.reportSaveError);
    } finally {
      setSavingReportSchedule(false);
    }
  };

  const openCreateReportSchedule = () => {
    setEditingReportSchedule(null);
    setShowReportScheduleModal(true);
  };

  const openEditReportSchedule = (schedule) => {
    setEditingReportSchedule(schedule);
    setShowReportScheduleModal(true);
  };

  const runReportScheduleNow = async (scheduleId) => {
    try {
      setRunningReportScheduleId(scheduleId);
      await billingService.runReportScheduleNow(scheduleId);
      toast.success(t.reportRunOk);
      await loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || t.reportRunError);
    } finally {
      setRunningReportScheduleId(null);
    }
  };

  const toggleReportSchedule = async (schedule) => {
    try {
      setTogglingReportScheduleId(schedule.id);
      await billingService.updateReportSchedule(schedule.id, {
        is_active: !schedule.is_active,
      });
      toast.success(!schedule.is_active ? t.scheduleActivated : t.scheduleDeactivated);
      await loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || t.scheduleToggleError);
    } finally {
      setTogglingReportScheduleId(null);
    }
  };

  const deleteReportSchedule = async (schedule) => {
    const confirmed = await showConfirm({
      title: isEnglish ? 'Delete schedule' : 'Eliminar programacion',
      text: `${t.deleteScheduleConfirm} "${schedule.name}"?`,
      confirmButtonText: isEnglish ? 'Delete' : 'Eliminar',
      cancelButtonText: isEnglish ? 'Cancel' : 'Cancelar',
    });
    if (!confirmed) return;

    try {
      setDeletingReportScheduleId(schedule.id);
      await billingService.deleteReportSchedule(schedule.id);
      toast.success(t.scheduleDeleted);
      await loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || t.scheduleDeleteError);
    } finally {
      setDeletingReportScheduleId(null);
    }
  };

  const methodOrder = ['sinpe', 'bank_transfer', 'cash', 'card', 'check', 'deposit', 'other'];
  const methodColors = {
    sinpe: '#22c55e',
    bank_transfer: '#3b82f6',
    cash: '#f59e0b',
    card: '#8b5cf6',
    check: '#ef4444',
    deposit: '#06b6d4',
    other: '#64748b',
  };

  const paymentMethodChartData = methodOrder
    .map((method) => ({
      key: method,
      label: paymentMethodLabel(method, isEnglish),
      amount: Number(reconciliation?.payment_methods_amount?.[method] || 0),
      count: Number(reconciliation?.payment_methods_count?.[method] || 0),
    }))
    .filter((item) => item.amount > 0 || item.count > 0);

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
          onClose={() => {
            setShowReportScheduleModal(false);
            setEditingReportSchedule(null);
          }}
          onSubmit={saveReportSchedule}
          loading={savingReportSchedule}
          initialData={editingReportSchedule}
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
            <h2 className="text-base font-semibold text-gray-100">{t.alerts}</h2>
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
            <h1 className="mt-2 text-3xl font-bold text-gray-100">{t.financeTitle}</h1>
            <p className="mt-2 max-w-3xl text-sm text-gray-400">
              {t.financeSubtitle}
            </p>
          </div>
          <button
            type="button"
            onClick={() => setShowBatchModal(true)}
            disabled={runningBatch}
            className="btn-primary inline-flex items-center gap-2"
          >
            <PlayCircle className="h-4 w-4" />
            {runningBatch ? t.runningBatch : t.runBatch}
          </button>
        </div>
      </div>

      <div className="glass-card p-6 space-y-5">
        <div className="flex flex-col gap-2 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <h2 className="text-xl font-semibold text-gray-100">{t.landingAnalytics}</h2>
            <p className="text-sm text-gray-400">{t.landingAnalyticsSubtitle}</p>
          </div>
          <div className="rounded-lg bg-primary-500/10 px-3 py-2 text-sm text-primary-200">
            {t.winnerVariant}: <strong>{landingAnalytics?.winner_variant || t.noWinnerYet}</strong>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-3 md:grid-cols-4">
          <input
            className="input-glass"
            placeholder={t.campaignFilter}
            value={landingFilters.campaign}
            onChange={(e) => setLandingFilters((prev) => ({ ...prev, campaign: e.target.value }))}
          />
          <input
            type="date"
            className="input-glass"
            value={landingFilters.from}
            onChange={(e) => setLandingFilters((prev) => ({ ...prev, from: e.target.value }))}
          />
          <input
            type="date"
            className="input-glass"
            value={landingFilters.to}
            onChange={(e) => setLandingFilters((prev) => ({ ...prev, to: e.target.value }))}
          />
          <button type="button" className="btn-primary" onClick={applyLandingFilters}>{t.applyFilters}</button>
        </div>

        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
          <MetricCard title={t.totalEvents} value={landingAnalytics?.totals?.events || 0} icon={BarChart3} tone="primary" />
          <MetricCard title={t.ctaClicks} value={landingAnalytics?.totals?.cta_clicks || 0} icon={MousePointer} tone="success" />
          <MetricCard title={t.fromDate} value={landingAnalytics?.filters?.from || '-'} icon={Calendar} tone="warning" />
          <MetricCard title={t.toDate} value={landingAnalytics?.filters?.to || '-'} icon={Calendar} tone="danger" />
        </div>

        {Array.isArray(landingAnalytics?.by_variant) && landingAnalytics.by_variant.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="table-glass">
              <thead>
                <tr>
                  <th>{t.variant}</th>
                  <th>{t.totalEvents}</th>
                  <th>{t.ctaClicks}</th>
                  <th>{t.rate}</th>
                </tr>
              </thead>
              <tbody>
                {landingAnalytics.by_variant.map((row) => (
                  <tr key={row.variant || 'na'}>
                    <td>{row.variant || 'N/A'}</td>
                    <td>{row.events}</td>
                    <td>{row.cta_clicks}</td>
                    <td>{row.cta_rate_percent}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-sm text-gray-500">{t.noLandingData}</p>
        )}

        {Array.isArray(landingAnalytics?.by_day) && landingAnalytics.by_day.length > 0 && (
          <div>
            <p className="mb-2 text-sm font-medium text-gray-300">{t.dailyBreakdown}</p>
            <div className="max-h-56 overflow-y-auto rounded-xl border border-gray-700/50">
              <table className="table-glass">
                <thead>
                  <tr>
                    <th>{t.fromDate}</th>
                    <th>{t.campaignFilter}</th>
                    <th>{t.variant}</th>
                    <th>{t.totalEvents}</th>
                  </tr>
                </thead>
                <tbody>
                  {landingAnalytics.by_day.map((item, idx) => (
                    <tr key={`${item.event_date}-${item.variant}-${idx}`}>
                      <td>{item.event_date}</td>
                      <td>{item.campaign || '-'}</td>
                      <td>{item.variant || 'N/A'}</td>
                      <td>{item.total}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 gap-6 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          title={t.netRevenue}
          value={formatMoney(summary?.net_revenue)}
          helper={`${summary?.paid_invoices || 0} ${t.paidInvoicesHelper}`}
          icon={Coins}
          tone="success"
        />
        <MetricCard
          title={t.receivables}
          value={formatMoney(summary?.accounts_receivable)}
          helper={`${summary?.pending_invoices || 0} ${t.pendingDocsHelper}`}
          icon={Wallet}
          tone="warning"
        />
        <MetricCard
          title={t.taxCollected}
          value={formatMoney(summary?.tax_collected)}
          helper={t.crTaxBase}
          icon={Landmark}
          tone="primary"
        />
        <MetricCard
          title={t.activeProducts}
          value={summary?.active_products || 0}
          helper={`${summary?.total_products || 0} ${t.catalogedProducts}`}
          icon={BarChart3}
          tone="danger"
        />
      </div>

      <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
        <MetricCard
          title="MRR"
          value={formatMoney(summary?.mrr)}
          helper={t.monthlyRecurringRevenue}
          icon={RefreshCw}
          tone="success"
        />
        <MetricCard
          title="ARR"
          value={formatMoney(summary?.arr)}
          helper={t.annualRecurringRevenue}
          icon={BarChart3}
          tone="primary"
        />
        <MetricCard
          title={t.activeSubscriptions}
          value={summary?.active_subscriptions || 0}
          helper={t.activeSubsHelper}
          icon={Building2}
          tone="warning"
        />
      </div>

      {/* Churn & trial metrics */}
      <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
        <MetricCard
          title="Churn Rate"
          value={churnData ? `${(churnData.churn_rate * 100).toFixed(1)}%` : '—'}
          helper={t.churnLast30}
          icon={TrendingDown}
          tone="danger"
        />
        <MetricCard
          title={t.activeTrials}
          value={churnData?.trial_subscriptions ?? (summary?.trial_subscriptions ?? '—')}
          helper={t.trialsInPeriod}
          icon={Clock}
          tone="warning"
        />
        <MetricCard
          title={t.trialConversion}
          value={churnData ? `${(churnData.trial_conversion_rate * 100).toFixed(1)}%` : '—'}
          helper={t.trialConverted30}
          icon={CheckCircle2}
          tone="success"
        />
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <div className="glass-card p-6">
          <div className="mb-6 flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-gray-100">{t.revenueTimeline}</h2>
              <p className="text-sm text-gray-500">{t.monthlyEvolution}</p>
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
              <h2 className="text-lg font-semibold text-gray-100">{t.revenueByProduct}</h2>
              <p className="text-sm text-gray-500">{t.netRevenueComparison}</p>
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
              <h2 className="text-lg font-semibold text-gray-100">{t.revenueByOrg}</h2>
              <p className="text-sm text-gray-500">{t.topCustomers}</p>
            </div>
            <Building2 className="h-5 w-5 text-primary-300" />
          </div>
          <div className="overflow-x-auto">
            <table className="table-glass">
              <thead>
                <tr>
                  <th>{t.organization}</th>
                  <th>{t.netRevenueLabel}</th>
                  <th>{t.tax}</th>
                  <th>{t.issued}</th>
                  <th>{t.paid}</th>
                </tr>
              </thead>
              <tbody>
                {byOrganization.map((item) => (
                  <tr key={item.organization__id}>
                    <td>
                      <div className="flex flex-wrap items-center gap-2">
                        <span>{item.organization__name}</span>
                        {item.billing_exempt && (
                          <span className="inline-flex items-center gap-1 rounded-full border border-emerald-400/30 bg-emerald-500/10 px-2 py-0.5 text-[11px] font-medium text-emerald-300">
                            <BadgeCheck className="h-3 w-3" />
                            {t.billingExempt}
                          </span>
                        )}
                      </div>
                    </td>
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
              <p className="text-sm text-gray-500">{t.agingSubtitle}</p>
            </div>
            <FileWarning className="h-5 w-5 text-amber-300" />
          </div>
          <div className="space-y-4 text-sm">
            <div className="rounded-xl border border-gray-700/50 bg-dark-400/40 p-4">
              <p className="text-gray-400">{t.current}</p>
              <p className="mt-1 text-xl font-semibold text-gray-100">{formatMoney(receivables?.current)}</p>
            </div>
            <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-4">
              <p className="text-amber-300">{t.days1to30}</p>
              <p className="mt-1 text-xl font-semibold text-amber-100">{formatMoney(receivables?.overdue_1_30)}</p>
            </div>
            <div className="rounded-xl border border-orange-500/30 bg-orange-500/10 p-4">
              <p className="text-orange-300">{t.days31to60}</p>
              <p className="mt-1 text-xl font-semibold text-orange-100">{formatMoney(receivables?.overdue_31_60)}</p>
            </div>
            <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-4">
              <p className="text-red-300">{t.days61Plus}</p>
              <p className="mt-1 text-xl font-semibold text-red-100">{formatMoney(receivables?.overdue_61_plus)}</p>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <div className="glass-card p-6">
          <div className="mb-5 flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-gray-100">{t.recentInvoices}</h2>
              <p className="text-sm text-gray-500">{t.commercialOperationalStatus}</p>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={exportCsv}
                className="btn-secondary inline-flex items-center gap-1.5 text-sm py-1.5 px-3"
                title={t.exportCsvTitle}
              >
                <Download className="h-3.5 w-3.5" />
                {t.exportCsv}
              </button>
              <Receipt className="h-5 w-5 text-primary-300" />
            </div>
          </div>
          <div className="overflow-x-auto">
            <table className="table-glass">
              <thead>
                <tr>
                  <th>{t.invoice}</th>
                  <th>{t.customer}</th>
                  <th>{t.total}</th>
                  <th>{t.status}</th>
                  <th>{t.taxAuthority}</th>
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
                    <td>
                      <div className="flex flex-wrap items-center gap-2">
                        <span>{invoice.organization_name}</span>
                        {invoice.billing_exempt && (
                          <span className="inline-flex items-center gap-1 rounded-full border border-emerald-400/30 bg-emerald-500/10 px-2 py-0.5 text-[11px] font-medium text-emerald-300">
                            <BadgeCheck className="h-3 w-3" />
                            {t.billingExempt}
                          </span>
                        )}
                      </div>
                    </td>
                    <td>{invoice.billing_exempt ? t.exemptAmount : formatMoney(invoice.total)}</td>
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
              <h2 className="text-lg font-semibold text-gray-100">{t.latestBatch}</h2>
              <p className="text-sm text-gray-500">{t.latestBatchSubtitle}</p>
            </div>
            <PlayCircle className="h-5 w-5 text-primary-300" />
          </div>
          {batchReport ? (
            <div className="space-y-4 text-sm">
              <div className="grid grid-cols-3 gap-3">
                <div className="rounded-xl bg-emerald-500/10 p-4 border border-emerald-500/25">
                  <p className="text-emerald-300">{t.processed}</p>
                  <p className="mt-1 text-2xl font-semibold text-emerald-100">{batchReport.summary.processed_count}</p>
                </div>
                <div className="rounded-xl bg-amber-500/10 p-4 border border-amber-500/25">
                  <p className="text-amber-300">{t.skipped}</p>
                  <p className="mt-1 text-2xl font-semibold text-amber-100">{batchReport.summary.skipped_count}</p>
                </div>
                <div className="rounded-xl bg-red-500/10 p-4 border border-red-500/25">
                  <p className="text-red-300">{t.errors}</p>
                  <p className="mt-1 text-2xl font-semibold text-red-100">{batchReport.summary.error_count}</p>
                </div>
              </div>
              <div className="rounded-xl border border-gray-700/50 bg-dark-400/40 p-4">
                <p className="text-xs uppercase tracking-[0.2em] text-gray-500">{t.runDate}</p>
                <p className="mt-2 text-gray-100">{batchReport.run_date}</p>
              </div>
              <div className="rounded-xl border border-gray-700/50 bg-dark-400/40 p-4">
                <p className="mb-2 text-xs uppercase tracking-[0.2em] text-gray-500">{t.latestProcessed}</p>
                <div className="space-y-2">
                  {batchReport.processed.slice(0, 4).map((item) => (
                    <div key={item.invoice_id} className="flex items-center justify-between gap-4 text-gray-300">
                      <div className="flex flex-wrap items-center gap-2">
                        <span>{item.organization_name}</span>
                        {item.billing_exempt && (
                          <span className="inline-flex items-center gap-1 rounded-full border border-emerald-400/30 bg-emerald-500/10 px-2 py-0.5 text-[11px] font-medium text-emerald-300">
                            <BadgeCheck className="h-3 w-3" />
                            {t.billingExempt}
                          </span>
                        )}
                      </div>
                      <span className="text-primary-300">{item.invoice_number}</span>
                    </div>
                  ))}
                  {batchReport.skipped?.slice(0, 4).map((item, index) => (
                    <div key={`skipped-${item.organization_id || index}`} className="flex items-center justify-between gap-4 text-gray-400">
                      <div className="flex flex-wrap items-center gap-2">
                        <span>{item.organization_name}</span>
                        <span className="inline-flex items-center gap-1 rounded-full border border-emerald-400/30 bg-emerald-500/10 px-2 py-0.5 text-[11px] font-medium text-emerald-300">
                          <BadgeCheck className="h-3 w-3" />
                          {t.billingExempt}
                        </span>
                      </div>
                      <span className="text-xs text-amber-300">{item.reason === 'owner_billing_exempt' ? t.exemptSkippedReason : item.reason}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="rounded-xl border border-dashed border-gray-700/60 bg-dark-400/30 p-6 text-sm text-gray-500">
              {t.noBatchYet}
            </div>
          )}
        </div>
      </div>

      {/* Product dashboard */}
      {productDashboard.length > 0 && (
        <div className="glass-card p-6">
          <div className="mb-5 flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-gray-100">{t.productDashboard}</h2>
              <p className="text-sm text-gray-500">{t.productDashboardSubtitle}</p>
            </div>
            <BarChart3 className="h-5 w-5 text-primary-300" />
          </div>
          <div className="overflow-x-auto">
            <table className="table-glass">
              <thead>
                <tr>
                  <th>{t.product}</th>
                  <th>{t.model}</th>
                  <th>{t.netRevenueLabel}</th>
                  <th>MRR</th>
                  <th>ARR</th>
                  <th>{t.subscriptions}</th>
                  <th>{t.invoicesLabel}</th>
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
              <h2 className="text-lg font-semibold text-gray-100">{t.reconciliation}</h2>
              <p className="text-sm text-gray-500">{t.reconciliationSubtitle}</p>
            </div>
            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={() => setShowRegisterPayment(true)}
                className="btn-secondary inline-flex items-center gap-2 text-sm"
              >
                <Plus className="h-4 w-4" />
                {t.registerPayment}
              </button>
              <Wallet className="h-5 w-5 text-primary-300" />
            </div>
          </div>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
            <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-4">
              <p className="text-xs text-amber-300 uppercase tracking-wider">{t.pendingPaymentsLabel}</p>
              <p className="mt-1 text-2xl font-semibold text-amber-100">{reconciliation.pending_payments}</p>
              <p className="mt-1 text-sm text-amber-300">{formatMoney(reconciliation.pending_amount)}</p>
            </div>
            <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-4">
              <p className="text-xs text-emerald-300 uppercase tracking-wider">{t.confirmedLabel}</p>
              <p className="mt-1 text-2xl font-semibold text-emerald-100">{reconciliation.confirmed_payments}</p>
              <p className="mt-1 text-sm text-emerald-300">{formatMoney(reconciliation.confirmed_amount)}</p>
            </div>
            <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-4">
              <p className="text-xs text-red-300 uppercase tracking-wider">{t.overdueInvoices}</p>
              <p className="mt-1 text-2xl font-semibold text-red-100">{reconciliation.overdue_invoices}</p>
              <p className="mt-1 text-sm text-red-300">{formatMoney(reconciliation.overdue_amount)}</p>
            </div>
            <div className="rounded-xl border border-gray-700/50 bg-dark-400/40 p-4">
              <p className="text-xs text-gray-400 uppercase tracking-wider">{t.unmatched}</p>
              <p className="mt-1 text-2xl font-semibold text-gray-100">{reconciliation.unmatched_invoices}</p>
              <p className="mt-1 text-xs text-gray-500">{t.paidInvoicesNoPayment}</p>
            </div>
          </div>

          {reconciliation.payment_methods_count && (
            <div className="mt-6">
              <p className="text-xs uppercase tracking-widest text-gray-500">{t.byPaymentMethod}</p>
              <p className="mt-1 text-sm text-gray-500">{t.byPaymentMethodSubtitle}</p>
              <div className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
                {['sinpe', 'bank_transfer', 'cash', 'card', 'check', 'deposit', 'other']
                  .filter((method) => Number(reconciliation.payment_methods_count?.[method] || 0) > 0 || Number(reconciliation.payment_methods_amount?.[method] || 0) > 0)
                  .map((method) => (
                    <div key={method} className="rounded-xl border border-gray-700/50 bg-dark-400/30 p-3">
                      <p className="text-xs text-gray-400 uppercase tracking-wide">{paymentMethodLabel(method, isEnglish)}</p>
                      <p className="mt-1 text-lg font-semibold text-gray-100">{reconciliation.payment_methods_count?.[method] || 0}</p>
                      <p className="text-sm text-primary-300">{formatMoney(reconciliation.payment_methods_amount?.[method], isEnglish)}</p>
                    </div>
                  ))}
              </div>
            </div>
          )}

          {paymentMethodChartData.length > 0 && (
            <div className="mt-6 rounded-xl border border-gray-700/50 bg-dark-400/30 p-4">
              <div className="mb-3">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="text-xs uppercase tracking-widest text-gray-500">{t.byPaymentMethodChart}</p>
                    <p className="mt-1 text-sm text-gray-500">{paymentChartMetric === 'amount' ? t.byPaymentMethodChartSubtitle : t.byPaymentMethodChartSubtitleCount}</p>
                  </div>
                  <div className="inline-flex rounded-lg border border-gray-700/50 bg-dark-300/40 p-1">
                    <button
                      type="button"
                      onClick={() => setPaymentChartMetric('amount')}
                      className={`px-2.5 py-1 text-xs rounded-md transition-colors ${paymentChartMetric === 'amount' ? 'bg-primary-500/20 text-primary-300' : 'text-gray-400 hover:text-gray-200'}`}
                    >
                      {t.viewAmount}
                    </button>
                    <button
                      type="button"
                      onClick={() => setPaymentChartMetric('count')}
                      className={`px-2.5 py-1 text-xs rounded-md transition-colors ${paymentChartMetric === 'count' ? 'bg-primary-500/20 text-primary-300' : 'text-gray-400 hover:text-gray-200'}`}
                    >
                      {t.viewCount}
                    </button>
                  </div>
                </div>
              </div>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={paymentMethodChartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.15)" />
                    <XAxis dataKey="label" tick={{ fill: '#94a3b8', fontSize: 12 }} />
                    <YAxis
                      tick={{ fill: '#94a3b8', fontSize: 12 }}
                      tickFormatter={(value) => {
                        if (paymentChartMetric === 'count') return Number(value).toLocaleString(isEnglish ? 'en-US' : 'es-CR');
                        return Number(value).toLocaleString(isEnglish ? 'en-US' : 'es-CR');
                      }}
                    />
                    <Tooltip
                      formatter={(value, _name, props) => {
                        if (paymentChartMetric === 'count') {
                          return [Number(value).toLocaleString(isEnglish ? 'en-US' : 'es-CR'), t.viewCount];
                        }
                        return [formatMoney(value, isEnglish), `${t.amount} (${props?.payload?.count || 0})`];
                      }}
                      contentStyle={{
                        backgroundColor: 'rgba(15, 23, 42, 0.95)',
                        border: '1px solid rgba(148, 163, 184, 0.25)',
                        borderRadius: '12px',
                        color: '#e2e8f0',
                      }}
                    />
                    <Bar dataKey={paymentChartMetric === 'amount' ? 'amount' : 'count'} radius={[8, 8, 0, 0]}>
                      {paymentMethodChartData.map((entry) => (
                        <Cell key={entry.key} fill={methodColors[entry.key] || '#64748b'} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {pendingPayments.length > 0 && (
            <div className="mt-6">
              <p className="mb-3 text-xs uppercase tracking-widest text-gray-500">{t.pendingToReconcile}</p>
              <PendingPaymentsList payments={pendingPayments} onAction={loadData} />
            </div>
          )}
        </div>
      )}

      {/* Scheduler panel */}
      <div className="glass-card p-6">
        <div className="mb-5 flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-gray-100">{t.scheduler}</h2>
            <p className="text-sm text-gray-500">
              {scheduler?.enabled
                ? `${t.schedulerActiveAt} ${String(scheduler.cron?.hour ?? 6).padStart(2, '0')}:${String(scheduler.cron?.minute ?? 0).padStart(2, '0')} ${t.schedulerTz}`
                : t.schedulerDisabled}
            </p>
          </div>
          <div className="flex items-center gap-3">
            <div className={`h-2.5 w-2.5 rounded-full ${scheduler?.running ? 'bg-emerald-400 animate-pulse' : 'bg-gray-600'}`} />
            <span className="text-sm text-gray-400">{scheduler?.running ? t.running : t.stopped}</span>
            <button
              type="button"
              onClick={triggerSchedulerNow}
              disabled={triggeringScheduler}
              className="btn-secondary inline-flex items-center gap-2 text-sm"
            >
              <RefreshCw className={`h-4 w-4 ${triggeringScheduler ? 'animate-spin' : ''}`} />
              {t.runNow}
            </button>
          </div>
        </div>

        {scheduler?.next_run && (
          <div className="mb-4 rounded-xl bg-primary-500/10 border border-primary-500/20 px-4 py-3 text-sm text-primary-200 inline-flex items-center gap-2">
            <Clock className="h-4 w-4" />
            {t.nextRun}: {new Date(scheduler.next_run).toLocaleString(isEnglish ? 'en-US' : 'es-CR')}
          </div>
        )}

        {scheduler?.last_logs?.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="table-glass">
              <thead>
                <tr>
                  <th>{t.triggered}</th>
                  <th>{t.finished}</th>
                  <th>{t.status}</th>
                  <th>{t.result}</th>
                </tr>
              </thead>
              <tbody>
                {scheduler.last_logs.slice(0, 8).map((log) => (
                  <tr key={log.id}>
                    <td>{log.triggered_at ? new Date(log.triggered_at).toLocaleString(isEnglish ? 'en-US' : 'es-CR') : '—'}</td>
                    <td>{log.finished_at ? new Date(log.finished_at).toLocaleString(isEnglish ? 'en-US' : 'es-CR') : '—'}</td>
                    <td>
                      <span className={log.status === 'success' ? 'badge-success' : log.status === 'running' ? 'badge-info' : log.status === 'skipped' ? 'badge-warning' : 'badge-danger'}>
                        {log.status}
                      </span>
                    </td>
                    <td className="text-xs text-gray-400">
                      {log.result_summary?.runs
                        ? `${log.result_summary.runs.length} ${t.runsProcessed}`
                        : log.result_summary?.reason || '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="rounded-xl border border-dashed border-gray-700/60 bg-dark-400/30 p-6 text-sm text-gray-500">
            {t.noSchedulerRuns}
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
              <h2 className="text-lg font-semibold text-gray-100">{t.emailReports}</h2>
              <p className="text-sm text-gray-500 mt-0.5">{t.recurringSchedules}</p>
            </div>
          </div>
          <div className="flex items-center gap-5">
            <div className="hidden sm:flex items-center gap-4 text-sm">
              <span className="text-gray-500">
                <span className="font-semibold text-gray-100">{reportSchedules.length}</span> {t.total}
              </span>
              <span className="text-gray-500">
                <span className="font-semibold text-emerald-400">
                  {reportSchedules.filter((s) => s.is_active).length}
                </span>{' '}{t.activePlural}
              </span>
            </div>
            <button
              type="button"
              onClick={openCreateReportSchedule}
              className="btn-primary inline-flex items-center gap-2 text-sm"
            >
              <Plus className="h-4 w-4" />
              {t.newLabel}
            </button>
          </div>
        </div>

        {reportSchedules.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="table-glass">
              <thead>
                <tr>
                  <th>{t.name}</th>
                  <th>{t.type}</th>
                  <th>{t.frequencyLabel}</th>
                  <th>{t.recipientsLabel}</th>
                  <th>{t.nextRunAt}</th>
                  <th>{t.status}</th>
                  <th className="text-right">{t.actions}</th>
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
                          <><BarChart3 className="h-3.5 w-3.5 text-emerald-400 flex-shrink-0" /><span>{t.collections}</span></>
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
                        {schedule.frequency === 'daily' ? t.daily : schedule.frequency === 'weekly' ? t.weekly : t.monthly}
                      </span>
                    </td>
                    <td>
                      <div className="flex items-center gap-1.5 text-xs text-gray-400">
                        <Users className="h-3.5 w-3.5 flex-shrink-0" />
                        <span>{schedule.recipients?.length ?? 0} {t.emailsCount}{schedule.recipients?.length !== 1 ? 's' : ''}</span>
                      </div>
                    </td>
                    <td className="text-xs text-gray-400">
                      {schedule.next_run_at
                        ? new Date(schedule.next_run_at).toLocaleString(isEnglish ? 'en-US' : 'es-CR')
                        : '—'}
                    </td>
                    <td>
                      <span className={schedule.is_active ? 'badge-success' : 'badge-neutral'}>
                        {schedule.is_active ? t.active : t.inactive}
                      </span>
                    </td>
                    <td className="text-right">
                      <div className="inline-flex items-center gap-1.5">
                        <button
                          type="button"
                          onClick={() => runReportScheduleNow(schedule.id)}
                          disabled={runningReportScheduleId === schedule.id}
                          className="inline-flex items-center gap-1.5 rounded-lg border border-emerald-500/20 bg-emerald-500/10 px-2.5 py-1.5 text-xs font-medium text-emerald-300 transition-colors hover:bg-emerald-500/20 disabled:opacity-50"
                          title={t.runNowTitle}
                        >
                          <PlayCircle className="h-3.5 w-3.5" />
                        </button>
                        <button
                          type="button"
                          onClick={() => openEditReportSchedule(schedule)}
                          className="inline-flex items-center gap-1.5 rounded-lg border border-blue-500/20 bg-blue-500/10 px-2.5 py-1.5 text-xs font-medium text-blue-300 transition-colors hover:bg-blue-500/20"
                          title={t.editTitle}
                        >
                          <PenSquare className="h-3.5 w-3.5" />
                        </button>
                        <button
                          type="button"
                          onClick={() => toggleReportSchedule(schedule)}
                          disabled={togglingReportScheduleId === schedule.id}
                          className="inline-flex items-center gap-1.5 rounded-lg border border-amber-500/20 bg-amber-500/10 px-2.5 py-1.5 text-xs font-medium text-amber-300 transition-colors hover:bg-amber-500/20 disabled:opacity-50"
                          title={schedule.is_active ? t.deactivate : t.activate}
                        >
                          {togglingReportScheduleId === schedule.id
                            ? '…'
                            : schedule.is_active ? 'Off' : 'On'}
                        </button>
                        <button
                          type="button"
                          onClick={() => deleteReportSchedule(schedule)}
                          disabled={deletingReportScheduleId === schedule.id}
                          className="inline-flex items-center gap-1.5 rounded-lg border border-red-500/20 bg-red-500/10 px-2.5 py-1.5 text-xs font-medium text-red-300 transition-colors hover:bg-red-500/20 disabled:opacity-50"
                          title={t.delete}
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </button>
                      </div>
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
              <p className="text-sm font-medium text-gray-300">{t.noSchedulesYet}</p>
              <p className="text-xs text-gray-500 mt-1 max-w-xs">
                {t.createFirstScheduleDesc}
              </p>
            </div>
            <button
              type="button"
              onClick={openCreateReportSchedule}
              className="btn-primary inline-flex items-center gap-2 text-sm mt-1"
            >
              <Plus className="h-4 w-4" />
              {t.createFirstSchedule}
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default FinancePage;
