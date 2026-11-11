import React from 'react';
import {
  LayoutDashboard,
  Users,
  Wallet,
  Coins,
  Scale,
  FileSpreadsheet,
  Settings,
  HelpCircle,
  X,
} from 'lucide-react';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

interface NavItem {
  name: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  active?: boolean;
  badge?: string;
}

const navigation: NavItem[] = [
  { name: 'Dashboard', href: '#', icon: LayoutDashboard, active: true },
  { name: 'Members & Roles', href: '#', icon: Users },
  { name: 'Contributions', href: '#', icon: Wallet },
  { name: 'Loans & FIFO Queue', href: '#', icon: Coins, badge: 'FIFO' },
  { name: 'Double-Entry Ledger', href: '#', icon: Scale },
  { name: 'Reports & Audit', href: '#', icon: FileSpreadsheet },
  { name: 'Settings', href: '#', icon: Settings },
];

export const Sidebar: React.FC<SidebarProps> = ({ isOpen, onClose }) => {
  return (
    <>
      {/* Mobile backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-gray-600 bg-opacity-75 transition-opacity md:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar container */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 w-64 bg-white border-r border-gray-200 transform transition-transform duration-200 ease-in-out md:translate-x-0 md:static md:inset-auto md:z-auto ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="h-full flex flex-col justify-between">
          <div className="flex-1 px-4 py-5 overflow-y-auto">
            {/* Mobile close button */}
            <div className="flex items-center justify-between pb-4 mb-4 border-b border-gray-100 md:hidden">
              <span className="font-semibold text-gray-800">Navigation</span>
              <button
                type="button"
                onClick={onClose}
                className="text-gray-400 hover:text-gray-600 p-1 rounded-md"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Navigation links */}
            <nav className="space-y-1">
              {navigation.map((item) => {
                const Icon = item.icon;
                return (
                  <a
                    key={item.name}
                    href={item.href}
                    className={`group flex items-center justify-between px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
                      item.active
                        ? 'bg-emerald-50 text-emerald-700'
                        : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                    }`}
                  >
                    <div className="flex items-center">
                      <Icon
                        className={`mr-3 h-5 w-5 flex-shrink-0 ${
                          item.active
                            ? 'text-emerald-600'
                            : 'text-gray-400 group-hover:text-gray-500'
                        }`}
                      />
                      <span>{item.name}</span>
                    </div>
                    {item.badge && (
                      <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-semibold bg-emerald-100 text-emerald-800">
                        {item.badge}
                      </span>
                    )}
                  </a>
                );
              })}
            </nav>
          </div>

          {/* Footer inside sidebar */}
          <div className="p-4 border-t border-gray-100 bg-gray-50/50">
            <a
              href="#"
              className="flex items-center text-xs text-gray-500 hover:text-gray-700 transition-colors"
            >
              <HelpCircle className="w-4 h-4 mr-2" />
              <span>Docs & Architecture</span>
            </a>
          </div>
        </div>
      </aside>
    </>
  );
};
