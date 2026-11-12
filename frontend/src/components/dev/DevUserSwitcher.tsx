import React, { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { ChevronUp, ChevronDown, Check, ShieldCheck } from 'lucide-react';

export const DevUserSwitcher: React.FC = () => {
  const { activeDevUser, availableDevUsers, switchDevPersona } = useAuth();
  const [isOpen, setIsOpen] = useState(false);

  const handleSelect = async (email: string) => {
    if (activeDevUser?.email === email) {
      setIsOpen(false);
      return;
    }
    await switchDevPersona(email);
    setIsOpen(false);
  };

  return (
    <div className="fixed bottom-5 right-5 z-50 font-sans">
      {/* Expanded Persona Menu */}
      {isOpen && (
        <div className="mb-2 w-80 sm:w-96 bg-white rounded-2xl shadow-2xl border border-gray-200 overflow-hidden animate-in fade-in slide-in-from-bottom-3 duration-200">
          <div className="bg-gradient-to-r from-emerald-600 to-teal-700 px-4 py-3 text-white flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <ShieldCheck className="w-4 h-4 text-emerald-200" />
              <span className="text-xs font-bold uppercase tracking-wider">Dev Persona Switcher</span>
            </div>
            <span className="text-[10px] bg-white/20 text-white px-2 py-0.5 rounded-full font-medium">
              RBAC v1.0
            </span>
          </div>

          <div className="p-2 max-h-96 overflow-y-auto divide-y divide-gray-100">
            {availableDevUsers.map((user) => {
              const isSelected = activeDevUser?.email.toLowerCase() === user.email.toLowerCase();
              return (
                <button
                  key={user.email}
                  type="button"
                  onClick={() => handleSelect(user.email)}
                  className={`w-full text-left p-3 rounded-xl transition-all flex items-start space-x-3 ${
                    isSelected
                      ? 'bg-emerald-50/80 border border-emerald-200 text-gray-900 shadow-sm'
                      : 'hover:bg-gray-50 text-gray-700'
                  }`}
                >
                  <div className="text-2xl mt-0.5 flex-shrink-0 select-none">
                    {user.avatar_badge}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-gray-900 truncate">
                        {user.full_name}
                      </span>
                      {isSelected && (
                        <span className="inline-flex items-center text-[10px] font-semibold text-emerald-700 bg-emerald-100 px-1.5 py-0.5 rounded">
                          <Check className="w-3 h-3 mr-0.5" /> Active
                        </span>
                      )}
                    </div>
                    <p className="text-[11px] font-medium text-emerald-700 mt-0.5">
                      {user.role_title}
                    </p>
                    <p className="text-[10px] text-gray-500 mt-0.5 leading-snug line-clamp-2">
                      {user.role_description}
                    </p>
                    <p className="text-[10px] font-mono text-gray-400 mt-1 truncate">
                      {user.email}
                    </p>
                  </div>
                </button>
              );
            })}
          </div>

          <div className="bg-gray-50 px-4 py-2 border-t border-gray-100 flex items-center justify-between text-[11px] text-gray-500">
            <span>Instant RBAC Testing</span>
            <span className="font-mono text-[10px] text-gray-400">Zero pass / OTP</span>
          </div>
        </div>
      )}

      {/* Floating Trigger Button */}
      <button
        type="button"
        onClick={() => setIsOpen((prev) => !prev)}
        className="flex items-center space-x-2.5 bg-gray-900 text-white hover:bg-black px-3.5 py-2.5 rounded-full shadow-xl border border-gray-700 hover:scale-[1.02] active:scale-[0.98] transition-all"
        title="Click to switch development user role"
      >
        <span className="text-lg select-none leading-none">
          {activeDevUser?.avatar_badge || '👤'}
        </span>
        <div className="text-left hidden sm:block">
          <div className="flex items-center space-x-1.5">
            <span className="text-xs font-bold tracking-tight">
              {activeDevUser?.role_title || 'Switch Persona'}
            </span>
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
          </div>
          <p className="text-[10px] text-gray-400 truncate max-w-[120px]">
            {activeDevUser?.full_name?.split(' ')[0] || 'Dev User'}
          </p>
        </div>
        {isOpen ? (
          <ChevronDown className="w-4 h-4 text-gray-400" />
        ) : (
          <ChevronUp className="w-4 h-4 text-gray-400" />
        )}
      </button>
    </div>
  );
};
