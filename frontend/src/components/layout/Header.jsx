import React, { useState, useRef, useEffect } from 'react';
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

const Header = ({ onMenuClick, sidebarOpen }) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [searchFocused, setSearchFocused] = useState(false);
  const dropdownRef = useRef(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

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
            onClick={onMenuClick}
            className="lg:hidden p-2 rounded-lg hover:bg-dark-300 text-gray-400 hover:text-gray-200 transition-colors"
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
              placeholder="Buscar..."
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
          <button className="
            relative p-2 rounded-lg
            text-gray-400 hover:text-gray-200 hover:bg-dark-300
            transition-colors
          ">
            <Bell className="w-5 h-5" />
            <span className="absolute top-1 right-1 w-2 h-2 bg-primary-500 rounded-full" />
          </button>

          {/* User dropdown */}
          <div className="relative" ref={dropdownRef}>
            <button
              onClick={() => setDropdownOpen(!dropdownOpen)}
              className="
                flex items-center gap-2 px-3 py-2 rounded-lg
                hover:bg-dark-300 transition-colors
              "
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
              ">
                <div className="p-3 border-b border-gray-700/50">
                  <p className="text-sm font-medium text-gray-200">
                    {user?.full_name || `${user?.first_name} ${user?.last_name}`}
                  </p>
                  <p className="text-xs text-gray-500">{user?.email}</p>
                </div>

                <div className="p-2">
                  <button
                    onClick={() => {
                      setDropdownOpen(false);
                      navigate('/settings');
                    }}
                    className="
                      w-full flex items-center gap-3 px-3 py-2 rounded-lg
                      text-gray-400 hover:text-gray-200 hover:bg-dark-300
                      transition-colors text-left
                    "
                  >
                    <User className="w-4 h-4" />
                    <span className="text-sm">Mi Perfil</span>
                  </button>

                  <button
                    onClick={() => {
                      setDropdownOpen(false);
                      navigate('/settings');
                    }}
                    className="
                      w-full flex items-center gap-3 px-3 py-2 rounded-lg
                      text-gray-400 hover:text-gray-200 hover:bg-dark-300
                      transition-colors text-left
                    "
                  >
                    <Settings className="w-4 h-4" />
                    <span className="text-sm">Configuración</span>
                  </button>
                </div>

                <div className="p-2 border-t border-gray-700/50">
                  <button
                    onClick={handleLogout}
                    className="
                      w-full flex items-center gap-3 px-3 py-2 rounded-lg
                      text-red-400 hover:text-red-300 hover:bg-red-500/10
                      transition-colors text-left
                    "
                  >
                    <LogOut className="w-4 h-4" />
                    <span className="text-sm">Cerrar Sesión</span>
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
