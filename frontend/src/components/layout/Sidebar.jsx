import { NavLink, useLocation } from 'react-router-dom';
import {
  BarChart3,
  Bell,
  Building2,
  ChevronLeft,
  ChevronRight,
  CreditCard,
  LayoutDashboard,
  Settings,
  ShieldCheck,
  Users,
  X,
} from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';

const Sidebar = ({ isOpen, onToggle, mobileOpen, onMobileClose }) => {
  const location = useLocation();
  const { user } = useAuth();
  const isEnglish = user?.language === 'en';

  const navigation = [
    { name: isEnglish ? 'Dashboard' : 'Dashboard', href: '/', icon: LayoutDashboard },
    { name: isEnglish ? 'Organizations' : 'Organizaciones', href: '/organizations', icon: Building2 },
    { name: isEnglish ? 'Users' : 'Usuarios', href: '/users', icon: Users },
    { name: isEnglish ? 'Subscriptions' : 'Suscripciones', href: '/subscriptions', icon: CreditCard },
    { name: isEnglish ? 'Finance' : 'Finanzas', href: '/finance', icon: BarChart3 },
    { name: isEnglish ? 'Notifications' : 'Notificaciones', href: '/notifications', icon: Bell },
    { name: isEnglish ? 'Settings' : 'Configuración', href: '/settings', icon: Settings },
  ];

  const initials = `${user?.first_name?.[0] || ''}${user?.last_name?.[0] || ''}` || user?.email?.[0] || 'A';

  const NavItem = ({ item, collapsed }) => {
    const isActive = location.pathname === item.href ||
      (item.href !== '/' && location.pathname.startsWith(item.href));

    return (
      <NavLink
        to={item.href}
        onClick={onMobileClose}
        aria-current={isActive ? 'page' : undefined}
        className={`nav-item group relative ${isActive ? 'active' : ''} ${collapsed ? 'justify-center px-2' : ''}`}
      >
        {isActive && !collapsed && (
          <span className="absolute left-0 top-1/2 h-6 w-1 -translate-y-1/2 rounded-r-full bg-primary-600" />
        )}
        <item.icon className="h-5 w-5 flex-shrink-0" />
        {!collapsed && <span className="truncate">{item.name}</span>}
        {collapsed && (
          <span className="pointer-events-none absolute left-full ml-2 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 opacity-0 shadow-lg group-hover:opacity-100">
            {item.name}
          </span>
        )}
      </NavLink>
    );
  };

  const sidebarContent = (
    <>
      <div className="flex h-16 items-center justify-between border-b border-slate-200 px-4">
        <div className={`flex min-w-0 items-center gap-3 ${!isOpen ? 'lg:justify-center' : ''}`}>
          <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-xl bg-primary-600 text-white shadow-sm">
            <ShieldCheck className="h-5 w-5" />
          </div>
          {isOpen && (
            <div className="min-w-0">
              <h1 className="truncate text-base font-semibold text-slate-950">AdminApps</h1>
              <p className="truncate text-xs text-slate-500">{isEnglish ? 'SaaS Control Plane' : 'Control plane SaaS'}</p>
            </div>
          )}
        </div>

        <button
          type="button"
          onClick={onMobileClose}
          className="rounded-lg p-2 text-slate-500 hover:bg-slate-100 hover:text-slate-900 lg:hidden"
          aria-label={isEnglish ? 'Close navigation menu' : 'Cerrar menú de navegación'}
        >
          <X className="h-5 w-5" />
        </button>
      </div>

      <div className="px-3 pb-3 pt-4">
        {isOpen && (
          <div className="mb-3 rounded-lg border border-blue-100 bg-blue-50 px-3 py-2">
            <p className="text-xs font-semibold uppercase tracking-[0.08em] text-blue-700">
              {isEnglish ? 'Operations' : 'Operaciones'}
            </p>
            <p className="mt-1 text-xs text-slate-600">
              {isEnglish ? 'Customers, products and billing' : 'Clientes, productos y billing'}
            </p>
          </div>
        )}
        <nav className="space-y-1" aria-label={isEnglish ? 'Primary navigation' : 'Navegación principal'}>
          {navigation.map((item) => (
            <NavItem key={item.href} item={item} collapsed={!isOpen} />
          ))}
        </nav>
      </div>

      <div className="mt-auto border-t border-slate-200 p-4">
        <div className={`flex items-center gap-3 rounded-xl border border-slate-200 bg-slate-50 p-2.5 ${!isOpen ? 'justify-center border-0 bg-transparent p-0' : ''}`}>
          <div className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-full bg-slate-900 text-sm font-semibold text-white">
            {initials.toUpperCase()}
          </div>
          {isOpen && (
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold text-slate-900">
                {user?.full_name || user?.email || 'AdminApps'}
              </p>
              <p className="truncate text-xs capitalize text-slate-500">{user?.role || 'admin'}</p>
            </div>
          )}
        </div>
      </div>
    </>
  );

  return (
    <>
      <aside
        className={`hidden lg:fixed lg:left-0 lg:top-0 lg:z-50 lg:flex lg:h-screen lg:flex-col lg:border-r lg:border-slate-200 lg:bg-white/95 lg:shadow-sm lg:backdrop-blur transition-all duration-300 ${isOpen ? 'lg:w-64' : 'lg:w-20'}`}
      >
        {sidebarContent}
        <button
          type="button"
          onClick={onToggle}
          className="absolute -right-3 top-20 flex h-7 w-7 items-center justify-center rounded-full border border-slate-200 bg-white text-slate-500 shadow-sm hover:text-slate-900"
          aria-label={isOpen ? (isEnglish ? 'Collapse sidebar' : 'Colapsar barra lateral') : (isEnglish ? 'Expand sidebar' : 'Expandir barra lateral')}
        >
          {isOpen ? <ChevronLeft className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
        </button>
      </aside>

      <aside
        className={`fixed left-0 top-0 z-50 flex h-screen w-72 flex-col border-r border-slate-200 bg-white shadow-xl transition-transform duration-300 lg:hidden ${mobileOpen ? 'translate-x-0' : '-translate-x-full'}`}
        aria-hidden={!mobileOpen}
        aria-label={isEnglish ? 'Mobile navigation' : 'Navegación móvil'}
      >
        {sidebarContent}
      </aside>
    </>
  );
};

export default Sidebar;
