'use client';

import { createContext, useContext, useEffect, useMemo, useState } from 'react';

import { authApi } from '@/lib/api';
import { AuthUser } from '@/lib/contracts';

interface AuthContextValue {
  user: AuthUser | null;
  loading: boolean;
  refresh: () => Promise<void>;
  login: (payload: { email: string; password: string }) => Promise<AuthUser>;
  register: (payload: { email: string; password: string; display_name: string }) => Promise<AuthUser>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = async () => {
    try {
      const response = await authApi.me();
      setUser(response.user);
    } catch {
      setUser(null);
    }
  };

  useEffect(() => {
    refresh().finally(() => setLoading(false));
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      loading,
      refresh,
      login: async (payload) => {
        const response = await authApi.login(payload);
        setUser(response.user);
        return response.user;
      },
      register: async (payload) => {
        const response = await authApi.register(payload);
        setUser(response.user);
        return response.user;
      },
      logout: async () => {
        await authApi.logout();
        setUser(null);
      },
    }),
    [user, loading],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}
