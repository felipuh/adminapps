import { AlertTriangle, Inbox } from 'lucide-react';
import {
  S3ActiveFilters,
  S3ActionBar,
  S3Banner,
  S3FilterBar,
  S3FilterChip,
  S3FilterSelect,
  S3LoadingState,
  S3PageContent,
  S3PageLayout,
  S3Panel,
  S3Popover,
  S3ResultsSummary,
  S3SearchInput,
  S3StatusBadge,
  S3Table,
  S3TableContainer,
  S3TableHeader,
  S3Toast,
  S3ToastAction,
  S3ToastViewport,
  S3Tooltip,
} from '@smart3ai/design-system';

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

export const PageLayout = ({ children, size = 'wide', className = '' }) => (
  <S3PageLayout as="div" size={size} className={`enterprise-page ${className}`}>
    {children}
  </S3PageLayout>
);

export const PageContent = ({ children, className = '' }) => (
  <S3PageContent className={className}>{children}</S3PageContent>
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
  <S3Panel className={`enterprise-card ${className}`} bodyClassName="s3-panel__body-reset" padding="none">{children}</S3Panel>
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
    active: 'success',
    activo: 'success',
    enabled: 'success',
    paid: 'success',
    trial: 'info',
    pending: 'warning',
    overdue: 'warning',
    suspended: 'warning',
    inactive: 'neutral',
    disabled: 'neutral',
    not_configured: 'neutral',
    cancelled: 'danger',
    canceled: 'danger',
    revoked: 'danger',
    expired: 'danger',
    error: 'danger',
  };

  return <S3StatusBadge tone={map[normalized] || 'neutral'}>{children || status || 'Sin configurar'}</S3StatusBadge>;
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
  <S3LoadingState variant="section" size="lg" label={label} />
);

export const ErrorState = ({ title, description, action }) => (
  <div className="rounded-xl border border-amber-200 bg-amber-50 p-8 text-center">
    <AlertTriangle className="mx-auto h-10 w-10 text-amber-600" />
    <h3 className="mt-3 text-base font-semibold text-slate-950">{title}</h3>
    {description && <p className="mt-1 text-sm text-amber-800">{description}</p>}
    {action && <div className="mt-5 flex justify-center">{action}</div>}
  </div>
);

export const Banner = ({ tone = 'info', title, description, actions, onDismiss, children }) => (
  <S3Banner tone={tone} title={title} description={description} actions={actions} onDismiss={onDismiss}>
    {children}
  </S3Banner>
);

export const Tooltip = ({ content, children, placement }) => (
  <S3Tooltip content={content} placement={placement}>{children}</S3Tooltip>
);

export const Popover = ({ content, children, open, onOpenChange, placement }) => (
  <S3Popover content={content} open={open} onOpenChange={onOpenChange} placement={placement}>{children}</S3Popover>
);

export const ToastViewport = S3ToastViewport;
export const Toast = S3Toast;
export const ToastAction = S3ToastAction;

export const SearchInput = ({ value, onChange, placeholder, label, clearLabel }) => (
  <S3SearchInput
    value={value}
    onChange={(nextValue) => onChange?.({ target: { value: nextValue }, currentTarget: { value: nextValue } })}
    label={label}
    placeholder={placeholder}
    clearLabel={clearLabel}
  />
);

export const DataTable = ({ children }) => (
  <S3TableContainer>
    <S3Table className="table-glass">{children}</S3Table>
  </S3TableContainer>
);

export const FilterBar = S3FilterBar;
export const ActionBar = S3ActionBar;
export const FilterSelect = S3FilterSelect;
export const ActiveFilters = S3ActiveFilters;
export const FilterChip = S3FilterChip;
export const ResultsSummary = S3ResultsSummary;
export const SortableHeader = S3TableHeader;
