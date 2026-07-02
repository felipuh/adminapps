import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Menu, 
  Bell, 
  Search, 
  LogOut, 
  User, 
  Settings,
  ChevronDown
} from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { notificationService } from '../../services/api';

const Header = ({ onMenuClick, sidebarOpen }) => {
  const { user, logout } = useAuth();
  const isEnglish = user?.language === 'en';
  const t = {
    search: isEnglish ? 'Search...' : 'Buscar...',
    notifications: isEnglish ? 'Notifications' : 'Notificaciones',
    unreadSuffix: isEnglish ? 'unread' : 'sin leer',
    markAllRead: isEnglish ? 'Mark all as read' : 'Marcar todas leidas',
    loadingNotifications: isEnglish ? 'Loading notifications...' : 'Cargando notificaciones...',
    noNotifications: isEnglish ? 'No recent notifications.' : 'No hay notificaciones recientes.',
    fullHistory: isEnglish ? 'View full history' : 'Ver historial completo',
  };
  const navigate = useNavigate();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [searchFocused, setSearchFocused] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loadingNotifications, setLoadingNotifications] = useState(false);
  const dropdownRef = useRef(null);
  const notificationsRef = useRef(null);

  // Close dropdown when clicking outside
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
    if (nextState) {
      await loadNotifications();
    }
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

  return (
    <header className={`
      fixed top-0 right-0 h-16 z-40
      bg-dark-400/80 backdrop-blur-xl border-b border-gray-700/50
      transition-all duration-300
      ${sidebarOpen ? 'lg:left-64' : 'lg:left-20'} left-0
    `}>
      <div className="h-full px-4 flex items-center justify-between gap-4">
        {/* Left side */}
        <div className="flex items-center gap-4">
          {/* Mobile menu button */}
          <button
            type="button"
            onClick={onMenuClick}
            className="lg:hidden p-2 rounded-lg hover:bg-dark-300 text-gray-400 hover:text-gray-200 transition-colors"
            aria-label={isEnglish ? 'Open navigation menu' : 'Abrir menu de navegacion'}
          >
            <Menu className="w-5 h-5" />
          </button>

          {/* Search bar */}
          <div className={`
            relative hidden sm:flex items-center
            transition-all duration-200
            ${searchFocused ? 'w-80' : 'w-64'}
          `}>
            <Search className="absolute left-3 w-4 h-4 text-gray-500" />
            <input
              type="text"
              placeholder={t.search}
              aria-label={isEnglish ? 'Search in control center' : 'Buscar en el centro de control'}
              className="
                w-full pl-10 pr-4 py-2
                bg-dark-300/50 border border-gray-700/50 rounded-lg
                text-gray-200 placeholder-gray-500 text-sm
                focus:outline-none focus:border-primary-500/50 focus:ring-1 focus:ring-primary-500/20
                transition-all
              "
              onFocus={() => setSearchFocused(true)}
              onBlur={() => setSearchFocused(false)}
            />
          </div>
        </div>

        {/* Right side */}
        <div className="flex items-center gap-2">
          {/* Notifications */}
          <div className="relative" ref={notificationsRef}>
            <button
              type="button"
              onClick={handleToggleNotifications}
              className="
                relative p-2 rounded-lg
                text-gray-400 hover:text-gray-200 hover:bg-dark-300
                transition-colors
              "
              aria-label={t.notifications}
              aria-expanded={notificationsOpen}
              aria-haspopup="menu"
              aria-controls="header-notifications-panel"
            >
              <Bell className="w-5 h-5" />
              {unreadCount > 0 && (
                <span className="
                  absolute -top-1 -right-1 min-w-5 h-5 px-1
                  bg-red-500 text-white text-[10px] font-semibold
                  rounded-full flex items-center justify-center
                ">
                  {unreadCount > 99 ? '99+' : unreadCount}
                </span>
              )}
            </button>

            {notificationsOpen && (
              <div className="
                absolute right-0 mt-2 w-96 max-w-[90vw]
                bg-dark-200 border border-gray-700/50 rounded-xl
                shadow-xl shadow-black/30 overflow-hidden
                animate-fadeIn
              " id="header-notifications-panel" role="menu">
                <div className="p-3 border-b border-gray-700/50 flex items-center justify-between gap-3">
                  <div>
                    <p className="text-sm font-semibold text-gray-100">{t.notifications}</p>
                    <p className="text-xs text-gray-500">{unreadCount} {t.unreadSuffix}</p>
                  </div>
                  <button
                    type="button"
                    onClick={handleMarkAllRead}
                    className="text-xs text-primary-300 hover:text-primary-200 transition-colors"
                  >
                    {t.markAllRead}
                  </button>
                </div>

                <div className="max-h-96 overflow-y-auto">
                  {loadingNotifications && (
                    <div className="p-4 text-sm text-gray-400">{t.loadingNotifications}</div>
                  )}

                  {!loadingNotifications && notifications.length === 0 && (
                    <div className="p-4 text-sm text-gray-500">{t.noNotifications}</div>
                  )}

                  {!loadingNotifications && notifications.map((notification) => (
                    <button
                      type="button"
                      key={notification.id}
                      onClick={() => handleMarkRead(notification.id)}
                      className={`
                        w-full text-left px-4 py-3 border-b border-gray-700/40 last:border-b-0
                        hover:bg-dark-300/60 transition-colors
                        ${notification.is_read ? 'opacity-70' : ''}
                      `}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <p className="text-sm text-gray-100 line-clamp-1">{notification.title}</p>
                        {!notification.is_read && <span className="w-2 h-2 rounded-full bg-primary-400 mt-1.5" />}
                      </div>
                      <p className="text-xs text-gray-400 mt-1 line-clamp-2">{notification.message}</p>
                    </button>
                  ))}
                </div>

                <div className="p-3 border-t border-gray-700/50">
                  <button
                    type="button"
                    onClick={() => {
                      setNotificationsOpen(false);
                      navigate('/notifications');
                    }}
                    className="w-full text-sm text-primary-300 hover:text-primary-200 transition-colors"
                  >
                    {t.fullHistory}
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* User dropdown */}
          <div className="relative" ref={dropdownRef}>
            <button
              type="button"
              onClick={() => setDropdownOpen(!dropdownOpen)}
              className="
                flex items-center gap-2 px-3 py-2 rounded-lg
                hover:bg-dark-300 transition-colors
              "
              aria-label={isEnglish ? 'Open user menu' : 'Abrir menu de usuario'}
              aria-expanded={dropdownOpen}
              aria-haspopup="menu"
              aria-controls="header-user-menu"
            >
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary-400 to-primary-600 flex items-center justify-center text-white text-sm font-semibold">
                {user?.first_name?.[0]}{user?.last_name?.[0]}
              </div>
              <div className="hidden md:block text-left">
                <p className="text-sm font-medium text-gray-200">
                  {user?.first_name} {user?.last_name}
                </p>
                <p className="text-xs text-gray-500 capitalize">{user?.role}</p>
              </div>
              <ChevronDown className={`
                w-4 h-4 text-gray-500 transition-transform
                ${dropdownOpen ? 'rotate-180' : ''}
              `} />
            </button>

            {/* Dropdown menu */}
            {dropdownOpen && (
              <div className="
                absolute right-0 mt-2 w-56
                bg-dark-200 border border-gray-700/50 rounded-xl
                shadow-xl shadow-black/30 overflow-hidden
                animate-fadeIn
              " id="header-user-menu" role="menu">
                <div className="p-3 border-b border-gray-700/50">
                  <p className="text-sm font-medium text-gray-200">
                    {user?.full_name || `${user?.first_name} ${user?.last_name}`}
                  </p>
                  <p className="text-xs text-gray-500">{user?.email}</p>
                </div>

                <div className="p-2">
                  <button
                    type="button"
                    onClick={() => {
                      setDropdownOpen(false);
                      navigate('/settings?tab=profile');
                    }}
                    className="
                      w-full flex items-center gap-3 px-3 py-2 rounded-lg
                      text-gray-400 hover:text-gray-200 hover:bg-dark-300
                      transition-colors text-left
                    "
                  >
                    <User className="w-4 h-4" />
                    <span className="text-sm">{isEnglish ? 'My Profile' : 'Mi Perfil'}</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => {
                      setDropdownOpen(false);
                      navigate('/settings?tab=appearance');
                    }}
                    className="
                      w-full flex items-center gap-3 px-3 py-2 rounded-lg
                      text-gray-400 hover:text-gray-200 hover:bg-dark-300
                      transition-colors text-left
                    "
                  >
                    <Settings className="w-4 h-4" />
                    <span className="text-sm">{isEnglish ? 'Preferences' : 'Configuracion'}</span>
                  </button>
                </div>

                <div className="p-2 border-t border-gray-700/50">
                  <button
                    type="button"
                    onClick={handleLogout}
                    className="
                      w-full flex items-center gap-3 px-3 py-2 rounded-lg
                      text-red-400 hover:text-red-300 hover:bg-red-500/10
                      transition-colors text-left
                    "
                  >
                    <LogOut className="w-4 h-4" />
                    <span className="text-sm">{isEnglish ? 'Sign Out' : 'Cerrar Sesion'}</span>
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
