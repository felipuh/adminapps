import React, { useEffect, useMemo, useState } from 'react';
import { AlertCircle, AlertTriangle, Bell, CheckCheck, Info } from 'lucide-react';
import { notificationService } from '../services/api';

/* ─── Severity configuration ─────────────────────────────────────── */
const SEVERITY = {
  critical: {
    label: 'Crítico',
    bar: 'bg-red-500',
    badge: 'bg-red-500/10 text-red-300 border border-red-500/20',
    icon: AlertTriangle,
    iconColor: 'text-red-400',
    iconBg: 'bg-red-500/10',
  },
  high: {
    label: 'Alto',
    bar: 'bg-orange-500',
    badge: 'bg-orange-500/10 text-orange-300 border border-orange-500/20',
    icon: AlertCircle,
    iconColor: 'text-orange-400',
    iconBg: 'bg-orange-500/10',
  },
  medium: {
    label: 'Medio',
    bar: 'bg-amber-500',
    badge: 'bg-amber-500/10 text-amber-300 border border-amber-500/20',
    icon: Info,
    iconColor: 'text-amber-400',
    iconBg: 'bg-amber-500/10',
  },
  low: {
    label: 'Bajo',
    bar: 'bg-sky-500',
    badge: 'bg-sky-500/10 text-sky-300 border border-sky-500/20',
    icon: Info,
    iconColor: 'text-sky-400',
    iconBg: 'bg-sky-500/10',
  },
};

const FILTER_TABS = [
  { value: 'all', label: 'Todas' },
  { value: 'unread', label: 'Sin leer' },
  { value: 'critical', label: 'Críticas' },
  { value: 'high', label: 'Urgentes' },
];

/* ─── Page component ──────────────────────────────────────────────── */
const NotificationsPage = () => {
  const [loading, setLoading] = useState(true);
  const [notifications, setNotifications] = useState([]);
  const [activeFilter, setActiveFilter] = useState('all');

  /* Aggregate counts */
  const counts = useMemo(() => ({
    total: notifications.length,
    unread: notifications.filter((n) => !n.is_read).length,
    critical: notifications.filter((n) => n.severity === 'critical').length,
    high: notifications.filter((n) => n.severity === 'high').length,
  }), [notifications]);

  /* Filtered view */
  const filtered = useMemo(() => {
    if (activeFilter === 'unread') return notifications.filter((n) => !n.is_read);
    if (activeFilter === 'critical') return notifications.filter((n) => n.severity === 'critical');
    if (activeFilter === 'high') return notifications.filter((n) => n.severity === 'high');
    return notifications;
  }, [notifications, activeFilter]);

  const loadNotifications = async () => {
    setLoading(true);
    try {
      const data = await notificationService.getAll({ limit: 100 });
      setNotifications(data.notifications || []);
    } catch {
      setNotifications([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadNotifications(); }, []);

  const markRead = async (id) => {
    try {
      await notificationService.markRead(id);
      setNotifications((prev) => prev.map((n) => n.id === id ? { ...n, is_read: true } : n));
    } catch {}
  };

  const markAllRead = async () => {
    try {
      await notificationService.markAllRead();
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
    } catch {}
  };

  return (
    <div className="space-y-6 animate-fadeIn">

      {/* ── Page header ── */}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className="p-3 rounded-xl bg-gradient-to-br from-primary-500 to-primary-600 shadow-lg shadow-primary-500/25">
            <Bell className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-100">Centro de Notificaciones</h1>
            <p className="text-sm text-gray-500 mt-0.5">Historial de alertas y eventos del sistema</p>
          </div>
        </div>
        {counts.unread > 0 && (
          <button
            onClick={markAllRead}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm bg-dark-300 text-gray-200 border border-gray-700/60 hover:bg-dark-200 transition-colors"
          >
            <CheckCheck className="w-4 h-4" />
            Marcar todas leídas
          </button>
        )}
      </div>

      {/* ── Stats cards ── */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="rounded-xl bg-dark-300/60 border border-gray-700/40 px-4 py-3">
          <p className="text-2xl font-bold text-gray-100">{counts.total}</p>
          <p className="text-xs text-gray-500 mt-0.5">Total</p>
        </div>
        <div className="rounded-xl bg-primary-500/10 border border-primary-500/20 px-4 py-3">
          <p className="text-2xl font-bold text-primary-300">{counts.unread}</p>
          <p className="text-xs text-gray-500 mt-0.5">Sin leer</p>
        </div>
        <div className="rounded-xl bg-red-500/10 border border-red-500/20 px-4 py-3">
          <p className="text-2xl font-bold text-red-300">{counts.critical}</p>
          <p className="text-xs text-gray-500 mt-0.5">Críticas</p>
        </div>
        <div className="rounded-xl bg-orange-500/10 border border-orange-500/20 px-4 py-3">
          <p className="text-2xl font-bold text-orange-300">{counts.high}</p>
          <p className="text-xs text-gray-500 mt-0.5">Urgentes</p>
        </div>
      </div>

      {/* ── Filter tabs ── */}
      <div className="flex items-center gap-1 w-fit bg-dark-400/40 p-1 rounded-xl border border-gray-700/40">
        {FILTER_TABS.map((tab) => (
          <button
            key={tab.value}
            onClick={() => setActiveFilter(tab.value)}
            className={`inline-flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              activeFilter === tab.value
                ? 'bg-dark-200 text-gray-100 shadow-sm'
                : 'text-gray-500 hover:text-gray-300'
            }`}
          >
            {tab.label}
            {tab.value === 'unread' && counts.unread > 0 && (
              <span className="inline-flex items-center justify-center min-w-[1.25rem] h-5 px-1 rounded-full bg-primary-500 text-white text-[10px] font-semibold">
                {counts.unread > 99 ? '99+' : counts.unread}
              </span>
            )}
            {tab.value === 'critical' && counts.critical > 0 && (
              <span className="inline-flex items-center justify-center min-w-[1.25rem] h-5 px-1 rounded-full bg-red-500 text-white text-[10px] font-semibold">
                {counts.critical}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* ── Notifications list ── */}
      <div className="glass-card overflow-hidden">

        {/* Loading state */}
        {loading && (
          <div className="flex flex-col items-center gap-3 py-14 text-gray-500">
            <div className="w-6 h-6 border-2 border-gray-600 border-t-primary-400 rounded-full animate-spin" />
            <p className="text-sm">Cargando notificaciones…</p>
          </div>
        )}

        {/* Empty state */}
        {!loading && filtered.length === 0 && (
          <div className="flex flex-col items-center justify-center gap-4 py-16 px-6 text-center">
            <div className="p-5 rounded-2xl bg-gradient-to-br from-dark-300 to-dark-400/60 border border-gray-700/40">
              <Bell className="w-9 h-9 text-gray-600" />
            </div>
            <div>
              <p className="text-sm font-medium text-gray-300">Sin notificaciones</p>
              <p className="text-xs text-gray-500 mt-1">No hay eventos para este filtro.</p>
            </div>
          </div>
        )}

        {/* Items */}
        {!loading && filtered.map((notification) => {
          const cfg = SEVERITY[notification.severity] || SEVERITY.low;
          const Icon = cfg.icon;

          return (
            <div
              key={notification.id}
              className={`relative flex items-start gap-4 px-5 py-4 border-b border-gray-700/40 last:border-b-0 transition-colors hover:bg-dark-300/20 group ${
                notification.is_read ? 'opacity-55' : ''
              }`}
            >
              {/* Left severity accent bar */}
              <div className={`absolute left-0 inset-y-0 w-[3px] rounded-r ${cfg.bar} ${notification.is_read ? 'opacity-30' : ''}`} />

              {/* Icon */}
              <div className={`flex-shrink-0 mt-0.5 p-2 rounded-lg ${cfg.iconBg}`}>
                <Icon className={`w-4 h-4 ${cfg.iconColor}`} />
              </div>

              {/* Content */}
              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-semibold text-gray-100 leading-snug">{notification.title}</p>
                    <p className="text-sm text-gray-400 mt-0.5 line-clamp-2 leading-relaxed">{notification.message}</p>
                  </div>

                  {/* Mark-read button — appears on hover */}
                  {!notification.is_read && (
                    <button
                      onClick={() => markRead(notification.id)}
                      className="flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity text-xs px-2.5 py-1 rounded-md bg-primary-500/20 text-primary-200 hover:bg-primary-500/30 whitespace-nowrap"
                    >
                      Marcar leída
                    </button>
                  )}
                </div>

                {/* Meta row */}
                <div className="flex flex-wrap items-center gap-2 mt-2">
                  <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${cfg.badge}`}>
                    {cfg.label}
                  </span>
                  {notification.module && (
                    <span className="text-xs text-gray-600 bg-dark-400/50 px-2 py-0.5 rounded-md">
                      {notification.module}
                    </span>
                  )}
                  {!notification.is_read && (
                    <span className="flex items-center gap-1 text-xs text-primary-400 font-medium">
                      <span className="w-1.5 h-1.5 rounded-full bg-primary-400 inline-block animate-pulse" />
                      Nueva
                    </span>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default NotificationsPage;
