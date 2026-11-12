import React from 'react';
import { Landmark, Bell, Menu } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';

interface NavbarProps {
  onToggleSidebar?: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ onToggleSidebar }) => {
  const { currentUser, activeDevUser, isLoading } = useAuth();

  const displayName = currentUser?.full_name || activeDevUser?.full_name || 'Society Member';
  const displayEmail = currentUser?.email || activeDevUser?.email || '';
  const displayRole = activeDevUser?.role_title || 'Active Member';
  const badgeIcon = activeDevUser?.avatar_badge || '👤';

  return (
    <header className="bg-white border-b border-gray-200 sticky top-0 z-30">
      <div className="px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <button
            type="button"
            onClick={onToggleSidebar}
            className="md:hidden text-gray-500 hover:text-gray-700 p-2 rounded-lg hover:bg-gray-100 focus:outline-none"
            aria-label="Toggle navigation"
          >
            <Menu className="w-5 h-5" />
          </button>
          
          <div className="flex items-center space-x-2.5">
            <div className="w-9 h-9 rounded-lg bg-emerald-600 flex items-center justify-center text-white shadow-sm shadow-emerald-200">
              <Landmark className="w-5 h-5" />
            </div>
            <div>
              <span className="text-lg font-bold tracking-tight text-gray-900">Society</span>
              <span className="hidden sm:inline-block ml-2 text-xs font-medium px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200">
                SaaS v1.0
              </span>
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-4">
          <div className="hidden sm:flex items-center text-xs text-gray-500 bg-gray-50 px-3 py-1.5 rounded-md border border-gray-200">
            <span className="w-2 h-2 rounded-full bg-emerald-500 mr-2 animate-pulse"></span>
            <span>Auth v1.0 (RBAC Active)</span>
          </div>

          <button
            type="button"
            className="relative p-2 text-gray-400 hover:text-gray-600 rounded-full hover:bg-gray-100 transition-colors"
            title="Notifications"
          >
            <Bell className="w-5 h-5" />
          </button>

          <div className="flex items-center pl-2 border-l border-gray-200 space-x-3">
            <div className="w-9 h-9 rounded-full bg-emerald-50 border border-emerald-200 flex items-center justify-center text-lg select-none shadow-sm">
              {badgeIcon}
            </div>
            <div className="hidden md:block text-left">
              <div className="flex items-center space-x-1.5">
                <p className="text-xs font-bold text-gray-800 leading-tight">
                  {isLoading ? 'Loading...' : displayName}
                </p>
                <span className="text-[10px] font-semibold text-emerald-700 bg-emerald-50 px-1.5 py-0.2 rounded border border-emerald-200">
                  {displayRole}
                </span>
              </div>
              <p className="text-[11px] text-gray-500 truncate max-w-[160px]">
                {displayEmail}
              </p>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};
