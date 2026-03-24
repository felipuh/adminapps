import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { 
  LayoutDashboard, 
  Building2, 
  Users, 
  CreditCard, 
  BarChart3,
  Settings,
  ChevronLeft,
  ChevronRight,
  Shield,
  X
} from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Organizaciones', href: '/organizations', icon: Building2 },
  { name: 'Usuarios', href: '/users', icon: Users },
  { name: 'Suscripciones', href: '/subscriptions', icon: CreditCard },
  { name: 'Finanzas', href: '/finance', icon: BarChart3 },
  { name: 'Configuración', href: '/settings', icon: Settings },
];

const Sidebar = ({ isOpen, onToggle, mobileOpen, onMobileClose }) => {
  const location = useLocation();
  const { user } = useAuth();

  const NavItem = ({ item, collapsed }) => {
    const isActive = location.pathname === item.href || 
                     (item.href !== '/' && location.pathname.startsWith(item.href));

    return (
      <NavLink
        to={item.href}
        onClick={onMobileClose}
        className={`
          flex items-center gap-3 px-4 py-3 rounded-lg
          transition-all duration-200 group relative
          ${isActive 
            ? 'text-primary-400 bg-primary-500/10' 
            : 'text-gray-400 hover:text-gray-100 hover:bg-dark-200/50'
          }
        `}
      >
        {/* Active indicator */}
        {isActive && (
          <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 bg-primary-500 rounded-r-full" />
        )}
        
        <item.icon className={`w-5 h-5 flex-shrink-0 ${isActive ? 'text-primary-400' : ''}`} />
        
        {!collapsed && (
          <span className="font-medium whitespace-nowrap">{item.name}</span>
        )}

        {/* Tooltip for collapsed state */}
        {collapsed && (
          <div className="
            absolute left-full ml-2 px-3 py-1.5 
            bg-dark-200 text-gray-100 text-sm rounded-lg
            opacity-0 group-hover:opacity-100
            pointer-events-none transition-opacity
            whitespace-nowrap z-50 shadow-lg
          ">
            {item.name}
          </div>
        )}
      </NavLink>
    );
  };

  const sidebarContent = (
    <>
      {/* Logo */}
      <div className="flex items-center justify-between h-16 px-4 border-b border-gray-700/50">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-primary-600 flex items-center justify-center shadow-lg shadow-primary-500/30">
            <Shield className="w-6 h-6 text-white" />
          </div>
          {isOpen && (
            <div className="animate-fadeIn">
              <h1 className="text-lg font-bold text-gray-100">Admin Apps</h1>
              <p className="text-xs text-gray-500">Smart3AI Control Center</p>
            </div>
          )}
        </div>
        
        {/* Mobile close button */}
        <button
          onClick={onMobileClose}
          className="lg:hidden p-2 rounded-lg hover:bg-dark-200 text-gray-400"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {navigation.map((item) => (
          <NavItem key={item.name} item={item} collapsed={!isOpen} />
        ))}
      </nav>

      {/* User info */}
      <div className="p-4 border-t border-gray-700/50">
        <div className={`flex items-center gap-3 ${!isOpen && 'justify-center'}`}>
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary-400 to-primary-600 flex items-center justify-center text-white font-semibold">
            {user?.first_name?.[0]}{user?.last_name?.[0]}
          </div>
          {isOpen && (
            <div className="flex-1 min-w-0 animate-fadeIn">
              <p className="text-sm font-medium text-gray-200 truncate">
                {user?.full_name || user?.email}
              </p>
              <p className="text-xs text-gray-500 capitalize">{user?.role}</p>
            </div>
          )}
        </div>
      </div>
    </>
  );

  return (
    <>
      {/* Desktop sidebar */}
      <aside className={`
        hidden lg:flex lg:flex-col fixed left-0 top-0 h-screen
        bg-dark-300/80 backdrop-blur-xl border-r border-gray-700/50
        transition-all duration-300 z-50
        ${isOpen ? 'w-64' : 'w-20'}
      `}>
        {sidebarContent}

        {/* Toggle button */}
        <button
          onClick={onToggle}
          className="
            absolute -right-3 top-20 w-6 h-6
            bg-dark-200 border border-gray-700/50 rounded-full
            flex items-center justify-center
            text-gray-400 hover:text-gray-200
            transition-colors shadow-lg
          "
        >
          {isOpen ? <ChevronLeft className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
        </button>
      </aside>

      {/* Mobile sidebar */}
      <aside className={`
        lg:hidden fixed left-0 top-0 h-screen w-64
        bg-dark-300/95 backdrop-blur-xl border-r border-gray-700/50
        transition-transform duration-300 z-50
        ${mobileOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
        {sidebarContent}
      </aside>
    </>
  );
};

export default Sidebar;
