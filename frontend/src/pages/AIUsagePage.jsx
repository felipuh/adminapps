import { useEffect, useState } from 'react';
import { AlertTriangle, Bot, Coins, Database, RefreshCw, Users } from 'lucide-react';
import { billingService } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import { ErrorState, LoadingState, PageHeader } from '../components/ui/EnterpriseUI';

const number = (value) => new Intl.NumberFormat().format(value || 0);
const money = (value) => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 6 }).format(value || 0);

const AIUsagePage = () => {
  const { user } = useAuth();
  const english = user?.language === 'en';
  const [data, setData] = useState(null);
  const [error, setError] = useState(false);
  const [filters, setFilters] = useState({ start: '', end: '', tenant: '', product: '', model: '' });

  const load = async () => {
    setError(false);
    try { setData(await billingService.getAIUsage(filters)); } catch { setError(true); }
  };
  useEffect(() => { load(); }, []);
  const t = english ? {
    title: 'AI Usage & Costs', subtitle: 'Provider usage observability. This is not customer billing.', calls: 'AI calls', tokens: 'Reported tokens', cost: 'Estimated provider cost', tenants: 'Consuming tenants',
    incomplete: 'Unknown or unpriced records', filter: 'Apply filters', tenant: 'Tenant ID', product: 'Product', model: 'Model', start: 'From', end: 'To', company: 'Tenant / company', requests: 'Requests', input: 'Input', output: 'Output', total: 'Total', completeness: 'Completeness', noData: 'No usage matches the selected filters.',
  } : {
    title: 'Uso y costos de IA', subtitle: 'Observabilidad de uso del proveedor. No es facturación al cliente.', calls: 'Llamadas de IA', tokens: 'Tokens reportados', cost: 'Costo estimado del proveedor', tenants: 'Tenants consumidores',
    incomplete: 'Registros desconocidos o sin precio', filter: 'Aplicar filtros', tenant: 'ID del tenant', product: 'Producto', model: 'Modelo', start: 'Desde', end: 'Hasta', company: 'Tenant / empresa', requests: 'Solicitudes', input: 'Entrada', output: 'Salida', total: 'Total', completeness: 'Integridad', noData: 'No hay uso para los filtros seleccionados.',
  };
  if (!data && !error) return <LoadingState />;
  if (error) return <ErrorState title={english ? 'Unable to load AI usage.' : 'No se pudo cargar el uso de IA.'} actionLabel={english ? 'Retry' : 'Reintentar'} onAction={load} />;
  const overview = data.overview || {};
  const metrics = [
    [t.calls, number(overview.requests), Bot, 'text-blue-700 bg-blue-50'], [t.tokens, number(overview.total_tokens), Database, 'text-indigo-700 bg-indigo-50'],
    [t.cost, money(overview.known_cost), Coins, 'text-emerald-700 bg-emerald-50'], [t.tenants, number(overview.consuming_tenants), Users, 'text-violet-700 bg-violet-50'],
  ];
  return <div className="space-y-6">
    <PageHeader title={t.title} subtitle={t.subtitle} actions={<button className="btn-secondary inline-flex items-center gap-2" onClick={load}><RefreshCw className="h-4 w-4" />{english ? 'Refresh' : 'Actualizar'}</button>} />
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">{metrics.map(([label, value, Icon, tone]) => <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm" key={label}><div className="flex justify-between"><div><p className="text-sm text-slate-500">{label}</p><p className="mt-2 text-2xl font-bold text-slate-900">{value}</p></div><div className={`h-10 w-10 rounded-lg grid place-items-center ${tone}`}><Icon className="h-5 w-5" /></div></div></div>)}</div>
    <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900 flex gap-2"><AlertTriangle className="h-5 w-5 shrink-0" />{t.incomplete}: {number((overview.unknown_usage || 0) + (overview.unpriced_cost || 0))}</div>
    <form className="grid gap-3 rounded-xl border border-slate-200 bg-white p-4 md:grid-cols-6" onSubmit={(event) => { event.preventDefault(); load(); }}>
      {['start', 'end'].map((key) => <input key={key} type="date" className="input" value={filters[key]} onChange={(e) => setFilters({ ...filters, [key]: e.target.value })} aria-label={t[key]} />)}
      {['tenant', 'product', 'model'].map((key) => <input key={key} className="input" placeholder={t[key]} value={filters[key]} onChange={(e) => setFilters({ ...filters, [key]: e.target.value })} />)}
      <button className="btn-primary" type="submit">{t.filter}</button>
    </form>
    <div className="overflow-hidden rounded-xl border border-slate-200 bg-white"><div className="overflow-x-auto"><table className="min-w-full text-sm"><thead className="bg-slate-50 text-left text-slate-500"><tr>{[t.company, t.product, t.requests, t.input, t.output, t.total, t.cost, t.completeness].map((head) => <th className="px-4 py-3 font-medium" key={head}>{head}</th>)}</tr></thead><tbody className="divide-y divide-slate-100">{data.results?.map((row) => <tr key={`${row.organization_id}-${row.product_identifier}`}><td className="px-4 py-3 font-medium text-slate-900">{row.organization__name}</td><td className="px-4 py-3">{row.product_identifier}</td><td className="px-4 py-3">{number(row.requests)}</td><td className="px-4 py-3">{number(row.input_tokens)}</td><td className="px-4 py-3">{number(row.output_tokens)}</td><td className="px-4 py-3">{number(row.total_tokens)}</td><td className="px-4 py-3">{money(row.known_cost)}</td><td className="px-4 py-3">{row.incomplete ? <span className="text-amber-700">{row.incomplete} incomplete</span> : <span className="text-emerald-700">Complete</span>}</td></tr>)}{!data.results?.length && <tr><td colSpan="8" className="px-4 py-10 text-center text-slate-500">{t.noData}</td></tr>}</tbody></table></div></div>
  </div>;
};

export default AIUsagePage;
