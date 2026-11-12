import React, { createContext, useContext, useEffect, useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { AuthContextType, DevUser, User } from '../types/auth';
import { devLogin, fetchCurrentUser, fetchDevUsers } from '../services/api';

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const queryClient = useQueryClient();
  const [activeEmail, setActiveEmail] = useState<string>(() => {
    return localStorage.getItem('society_dev_user') || 'president@society.local';
  });

  // Query all available dev personas
  const { data: availableDevUsers = [] } = useQuery<DevUser[]>({
    queryKey: ['devUsers'],
    queryFn: fetchDevUsers,
    staleTime: Infinity,
  });

  // Query currently authenticated user
  const {
    data: currentUser = null,
    isLoading,
    refetch: refetchUser,
  } = useQuery<User | null>({
    queryKey: ['currentUser', activeEmail],
    queryFn: fetchCurrentUser,
    retry: 1,
  });

  // Keep activeDevUser in sync with activeEmail
  const activeDevUser =
    availableDevUsers.find((u) => u.email.toLowerCase() === activeEmail.toLowerCase()) || null;

  useEffect(() => {
    localStorage.setItem('society_dev_user', activeEmail);
  }, [activeEmail]);

  const switchDevPersona = async (email: string) => {
    localStorage.setItem('society_dev_user', email);
    setActiveEmail(email);

    try {
      const loginRes = await devLogin(email);
      if (loginRes.access_token) {
        localStorage.setItem('society_auth_token', loginRes.access_token);
      }
      queryClient.setQueryData(['currentUser', email], loginRes.user);
      await queryClient.invalidateQueries();
    } catch (err) {
      console.warn('Direct dev-login call failed, falling back to header auth', err);
      await refetchUser();
    }
  };

  const logout = () => {
    localStorage.removeItem('society_dev_user');
    localStorage.removeItem('society_auth_token');
    setActiveEmail('president@society.local');
    queryClient.clear();
  };

  return (
    <AuthContext.Provider
      value={{
        currentUser,
        activeDevUser,
        availableDevUsers,
        isLoading,
        switchDevPersona,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
