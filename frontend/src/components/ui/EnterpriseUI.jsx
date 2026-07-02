import { AlertTriangle, Inbox, Loader2, Search } from 'lucide-react';

export const PageHeader = ({ eyebrow, title, description, actions }) => (
  <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
    <div className="min-w-0">
      {eyebrow && <p className="enterprise-kicker">{eyebrow}</p>}
      <h1 className="enterprise-page-title">{title}</h1>
      {description && <p className="enterprise-page-subtitle">{description}</p>}
    </div>
    {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
  </div>
);

export const SectionHeader = ({ eyebrow, title, description, action }) => (
  <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
    <div>
      {eyebrow && <p className="enterprise-kicker">{eyebrow}</p>}
      <h2 className="text-lg font-semibold text-slate-950">{title}</h2>
      {description && <p className="mt-1 text-sm text-slate-500">{description}</p>}
    </div>
    {action}
  </div>
);

export const Card = ({ children, className = '' }) => (
  <div className={`enterprise-card ${className}`}>{children}</div>
);

export const MetricCard = ({ label, value, helper, icon: Icon, tone = 'blue' }) => {
  const tones = {
    blue: 'bg-blue-50 text-blue-700 border-blue-100',
    emerald: 'bg-emerald-50 text-emerald-700 border-emerald-100',
    amber: 'bg-amber-50 text-amber-700 border-amber-100',
    red: 'bg-red-50 text-red-700 border-red-100',
    slate: 'bg-slate-50 text-slate-700 border-slate-200',
  };

  return (
    <Card className="p-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-slate-500">{label}</p>
          <p className="mt-2 text-3xl font-semibold tracking-normal text-slate-950">{value}</p>
          {helper && <p className="mt-2 text-sm text-slate-500">{helper}</p>}
        </div>
        {Icon && (
          <div className={`flex h-11 w-11 items-center justify-center rounded-xl border ${tones[tone] || tones.blue}`}>
            <Icon className="h-5 w-5" />
          </div>
        )}
      </div>
    </Card>
  );
};

export const StatusBadge = ({ status, children }) => {
  const normalized = String(status || '').toLowerCase();
  const map = {
    active: 'badge-success',
    activo: 'badge-success',
    enabled: 'badge-success',
    paid: 'badge-success',
    trial: 'badge-info',
    pending: 'badge-warning',
    overdue: 'badge-warning',
    suspended: 'badge-warning',
    inactive: 'badge-neutral',
    disabled: 'badge-neutral',
    not_configured: 'badge-neutral',
    cancelled: 'badge-danger',
    canceled: 'badge-danger',
    revoked: 'badge-danger',
    expired: 'badge-danger',
    error: 'badge-danger',
  };

  return <span className={map[normalized] || 'badge-neutral'}>{children || status || 'Sin configurar'}</span>;
};

export const EmptyState = ({ icon: Icon = Inbox, title, description, action }) => (
  <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50/70 p-8 text-center">
    <Icon className="mx-auto h-10 w-10 text-slate-400" />
    <h3 className="mt-3 text-base font-semibold text-slate-950">{title}</h3>
    {description && <p className="mx-auto mt-1 max-w-lg text-sm text-slate-500">{description}</p>}
    {action && <div className="mt-5 flex justify-center">{action}</div>}
  </div>
);

export const LoadingState = ({ label = 'Cargando...' }) => (
  <div className="rounded-xl border border-slate-200 bg-white p-8 text-center">
    <Loader2 className="mx-auto h-8 w-8 animate-spin text-primary-600" />
    <p className="mt-3 text-sm text-slate-500">{label}</p>
  </div>
);

export const ErrorState = ({ title, description, action }) => (
  <div className="rounded-xl border border-amber-200 bg-amber-50 p-8 text-center">
    <AlertTriangle className="mx-auto h-10 w-10 text-amber-600" />
    <h3 className="mt-3 text-base font-semibold text-slate-950">{title}</h3>
    {description && <p className="mt-1 text-sm text-amber-800">{description}</p>}
    {action && <div className="mt-5 flex justify-center">{action}</div>}
  </div>
);

export const SearchInput = ({ value, onChange, placeholder }) => (
  <div className="relative">
    <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
    <input
      type="text"
      value={value}
      onChange={onChange}
      placeholder={placeholder}
      className="input-glass pl-10"
    />
  </div>
);

export const DataTable = ({ children }) => (
  <div className="overflow-x-auto">
    <table className="table-glass">{children}</table>
  </div>
);
