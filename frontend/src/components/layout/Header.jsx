import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Bell,
  ChevronDown,
  LogOut,
  Menu,
  Search,
  Settings,
  User,
} from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { notificationService } from '../../services/api';

const Header = ({ onMenuClick, sidebarOpen }) => {
  const { user, logout } = useAuth();
  const isEnglish = user?.language === 'en';
  const navigate = useNavigate();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [searchFocused, setSearchFocused] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loadingNotifications, setLoadingNotifications] = useState(false);
  const dropdownRef = useRef(null);
  const notificationsRef = useRef(null);

  const t = {
    search: isEnglish ? 'Search customers, users, products...' : 'Buscar clientes, usuarios, productos...',
    notifications: isEnglish ? 'Notifications' : 'Notificaciones',
    unreadSuffix: isEnglish ? 'unread' : 'sin leer',
    markAllRead: isEnglish ? 'Mark all as read' : 'Marcar todas leídas',
    loadingNotifications: isEnglish ? 'Loading notifications...' : 'Cargando notificaciones...',
    noNotifications: isEnglish ? 'No recent notifications.' : 'No hay notificaciones recientes.',
    fullHistory: isEnglish ? 'View full history' : 'Ver historial completo',
  };

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setDropdownOpen(false);
      }
      if (notificationsRef.current && !notificationsRef.current.contains(event.target)) {
        setNotificationsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  useEffect(() => {
    const handleEscape = (event) => {
      if (event.key === 'Escape') {
        setDropdownOpen(false);
        setNotificationsOpen(false);
      }
    };
    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, []);

  useEffect(() => {
    const loadUnreadCount = async () => {
      try {
        const data = await notificationService.getUnreadCount();
        setUnreadCount(data.unread_count || 0);
      } catch {
        setUnreadCount(0);
      }
    };
    loadUnreadCount();
  }, []);

  const loadNotifications = async () => {
    setLoadingNotifications(true);
    try {
      const data = await notificationService.getAll({ limit: 8 });
      setNotifications(data.notifications || []);
      setUnreadCount(data.unread_count || 0);
    } catch {
      setNotifications([]);
    } finally {
      setLoadingNotifications(false);
    }
  };

  const handleToggleNotifications = async () => {
    const nextState = !notificationsOpen;
    setNotificationsOpen(nextState);
    if (nextState) await loadNotifications();
  };

  const handleMarkRead = async (notificationId) => {
    try {
      await notificationService.markRead(notificationId);
      setNotifications((prev) => prev.map((item) => (
        item.id === notificationId ? { ...item, is_read: true } : item
      )));
      setUnreadCount((prev) => Math.max(0, prev - 1));
    } catch {
      // Keep UI stable if API fails.
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await notificationService.markAllRead();
      setNotifications((prev) => prev.map((item) => ({ ...item, is_read: true })));
      setUnreadCount(0);
    } catch {
      // Keep UI stable if API fails.
    }
  };

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const initials = `${user?.first_name?.[0] || ''}${user?.last_name?.[0] || ''}` || user?.email?.[0] || 'A';

  return (
    <header className={`fixed right-0 top-0 z-40 h-16 border-b border-slate-200 bg-white/90 backdrop-blur transition-all duration-300 ${sidebarOpen ? 'lg:left-64' : 'lg:left-20'} left-0`}>
      <div className="flex h-full items-center justify-between gap-4 px-4 lg:px-6">
        <div className="flex min-w-0 flex-1 items-center gap-4">
          <button
            type="button"
            onClick={onMenuClick}
            className="rounded-lg p-2 text-slate-500 hover:bg-slate-100 hover:text-slate-900 lg:hidden"
            aria-label={isEnglish ? 'Open navigation menu' : 'Abrir menú de navegación'}
          >
            <Menu className="h-5 w-5" />
          </button>

          <div className={`relative hidden items-center sm:flex ${searchFocused ? 'w-[28rem]' : 'w-80'} max-w-full transition-all duration-200`}>
            <Search className="absolute left-3 h-4 w-4 text-slate-400" />
            <input
              type="text"
              placeholder={t.search}
              aria-label={isEnglish ? 'Search in control center' : 'Buscar en el centro de control'}
              className="w-full rounded-lg border border-slate-200 bg-slate-50 py-2 pl-10 pr-4 text-sm text-slate-900 placeholder:text-slate-400 hover:border-slate-300 focus:border-primary-500 focus:bg-white focus:outline-none focus:ring-4 focus:ring-blue-100"
              onFocus={() => setSearchFocused(true)}
              onBlur={() => setSearchFocused(false)}
            />
          </div>
        </div>

        <div className="flex items-center gap-2">
          <div className="relative" ref={notificationsRef}>
            <button
              type="button"
              onClick={handleToggleNotifications}
              className="relative rounded-lg border border-transparent p-2 text-slate-500 hover:border-slate-200 hover:bg-slate-50 hover:text-slate-900"
              aria-label={t.notifications}
              aria-expanded={notificationsOpen}
              aria-haspopup="menu"
              aria-controls="header-notifications-panel"
            >
              <Bell className="h-5 w-5" />
              {unreadCount > 0 && (
                <span className="absolute -right-1 -top-1 flex h-5 min-w-5 items-center justify-center rounded-full bg-red-600 px-1 text-[10px] font-bold text-white">
                  {unreadCount > 99 ? '99+' : unreadCount}
                </span>
              )}
            </button>

            {notificationsOpen && (
              <div
                id="header-notifications-panel"
                role="menu"
                className="absolute right-0 mt-2 w-96 max-w-[90vw] overflow-hidden rounded-xl border border-slate-200 bg-white shadow-xl animate-fadeIn"
              >
                <div className="flex items-center justify-between gap-3 border-b border-slate-200 p-4">
                  <div>
                    <p className="text-sm font-semibold text-slate-950">{t.notifications}</p>
                    <p className="text-xs text-slate-500">{unreadCount} {t.unreadSuffix}</p>
                  </div>
                  <button type="button" onClick={handleMarkAllRead} className="text-xs font-semibold text-primary-700 hover:text-primary-900">
                    {t.markAllRead}
                  </button>
                </div>

                <div className="max-h-96 overflow-y-auto">
                  {loadingNotifications && <div className="p-4 text-sm text-slate-500">{t.loadingNotifications}</div>}
                  {!loadingNotifications && notifications.length === 0 && <div className="p-4 text-sm text-slate-500">{t.noNotifications}</div>}
                  {!loadingNotifications && notifications.map((notification) => (
                    <button
                      type="button"
                      key={notification.id}
                      onClick={() => handleMarkRead(notification.id)}
                      className={`w-full border-b border-slate-100 px-4 py-3 text-left last:border-b-0 hover:bg-slate-50 ${notification.is_read ? 'opacity-75' : ''}`}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <p className="line-clamp-1 text-sm font-medium text-slate-900">{notification.title}</p>
                        {!notification.is_read && <span className="mt-1.5 h-2 w-2 rounded-full bg-primary-600" />}
                      </div>
                      <p className="mt-1 line-clamp-2 text-xs text-slate-500">{notification.message}</p>
                    </button>
                  ))}
                </div>

                <div className="border-t border-slate-200 p-3">
                  <button
                    type="button"
                    onClick={() => {
                      setNotificationsOpen(false);
                      navigate('/notifications');
                    }}
                    className="w-full rounded-lg px-3 py-2 text-sm font-semibold text-primary-700 hover:bg-blue-50"
                  >
                    {t.fullHistory}
                  </button>
                </div>
              </div>
            )}
          </div>

          <div className="relative" ref={dropdownRef}>
            <button
              type="button"
              onClick={() => setDropdownOpen(!dropdownOpen)}
              className="flex items-center gap-2 rounded-lg border border-transparent px-2 py-1.5 hover:border-slate-200 hover:bg-slate-50"
              aria-label={isEnglish ? 'Open user menu' : 'Abrir menú de usuario'}
              aria-expanded={dropdownOpen}
              aria-haspopup="menu"
              aria-controls="header-user-menu"
            >
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-900 text-xs font-semibold text-white">
                {initials.toUpperCase()}
              </div>
              <div className="hidden text-left md:block">
                <p className="max-w-40 truncate text-sm font-semibold text-slate-900">
                  {user?.first_name} {user?.last_name}
                </p>
                <p className="text-xs capitalize text-slate-500">{user?.role}</p>
              </div>
              <ChevronDown className={`h-4 w-4 text-slate-400 transition-transform ${dropdownOpen ? 'rotate-180' : ''}`} />
            </button>

            {dropdownOpen && (
              <div id="header-user-menu" role="menu" className="absolute right-0 mt-2 w-60 overflow-hidden rounded-xl border border-slate-200 bg-white shadow-xl animate-fadeIn">
                <div className="border-b border-slate-200 p-4">
                  <p className="truncate text-sm font-semibold text-slate-900">
                    {user?.full_name || `${user?.first_name || ''} ${user?.last_name || ''}`.trim() || user?.email}
                  </p>
                  <p className="truncate text-xs text-slate-500">{user?.email}</p>
                </div>

                <div className="p-2">
                  <button
                    type="button"
                    onClick={() => {
                      setDropdownOpen(false);
                      navigate('/settings?tab=profile');
                    }}
                    className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-left text-sm text-slate-600 hover:bg-slate-50 hover:text-slate-950"
                  >
                    <User className="h-4 w-4" />
                    {isEnglish ? 'My Profile' : 'Mi perfil'}
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setDropdownOpen(false);
                      navigate('/settings?tab=appearance');
                    }}
                    className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-left text-sm text-slate-600 hover:bg-slate-50 hover:text-slate-950"
                  >
                    <Settings className="h-4 w-4" />
                    {isEnglish ? 'Preferences' : 'Preferencias'}
                  </button>
                </div>

                <div className="border-t border-slate-200 p-2">
                  <button
                    type="button"
                    onClick={handleLogout}
                    className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-left text-sm font-medium text-red-700 hover:bg-red-50"
                  >
                    <LogOut className="h-4 w-4" />
                    {isEnglish ? 'Sign Out' : 'Cerrar sesión'}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
