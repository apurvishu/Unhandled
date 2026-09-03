'use client';

import React, { createContext, useContext, useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { User, UserRole } from '@/types';
import { DEMO_USERS } from '@/config/constants';

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  isDemoMode: boolean;
  login: (email: string, passwordOrRole?: string | UserRole) => Promise<void>;
  register: (name: string, email: string, password?: string, role?: UserRole, organization?: string) => Promise<void>;
  quickLogin: (role: UserRole) => void;
  logout: () => void;
  toggleDemoMode: (val?: boolean) => void;
  getDashboardPathForRole: (role: UserRole) => string;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function getDashboardPathForRole(role: UserRole): string {
  switch (role) {
    case 'PROCUREMENT_OFFICER':
      return '/dashboard/procurement';
    case 'SHIP_OWNER':
      return '/dashboard/ship-owner';
    case 'PORT_OWNER':
      return '/dashboard/port-owner';
    case 'ADMIN':
      return '/dashboard/admin';
    default:
      return '/dashboard/procurement';
  }
}

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isDemoMode, setIsDemoMode] = useState<boolean>(true);
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    // Check saved session in localStorage
    const savedUser = localStorage.getItem('maritime_user');
    const savedDemo = localStorage.getItem('maritime_demo_mode');
    
    if (savedDemo !== null) {
      setIsDemoMode(savedDemo === 'true');
    }

    if (savedUser) {
      try {
        const parsed = JSON.parse(savedUser) as User;
        setUser(parsed);
      } catch {
        localStorage.removeItem('maritime_user');
      }
    } else {
      // Default to Procurement Officer for effortless testing
      const defaultUser = DEMO_USERS.PROCUREMENT_OFFICER;
      setUser(defaultUser);
      localStorage.setItem('maritime_user', JSON.stringify(defaultUser));
    }
    setIsLoading(false);
  }, []);

  const login = async (email: string, passwordOrRole: string | UserRole = 'PROCUREMENT_OFFICER') => {
    setIsLoading(true);
    const role: UserRole = ['PROCUREMENT_OFFICER', 'SHIP_OWNER', 'PORT_OWNER', 'ADMIN'].includes(passwordOrRole as string)
      ? (passwordOrRole as UserRole)
      : 'PROCUREMENT_OFFICER';

    // Find demo user matching role or default
    const matchedUser = Object.values(DEMO_USERS).find((u) => u.email === email || u.role === role) || {
      id: 'usr-custom-' + Date.now(),
      name: email.split('@')[0],
      email,
      role,
      companyName: 'Maritime Enterprise Corp',
      createdAt: new Date().toISOString(),
    };

    setUser(matchedUser);
    localStorage.setItem('maritime_user', JSON.stringify(matchedUser));
    localStorage.setItem('maritime_access_token', 'demo_jwt_access_token_' + Date.now());
    setIsLoading(false);

    const target = getDashboardPathForRole(matchedUser.role);
    router.push(target);
  };

  const register = async (name: string, email: string, password?: string, role: UserRole = 'PROCUREMENT_OFFICER', organization?: string) => {
    setIsLoading(true);
    const newUser: User = {
      id: 'usr-new-' + Date.now(),
      name,
      email,
      role,
      companyName: organization || 'Bulk Logistics Corp',
      createdAt: new Date().toISOString(),
    };

    setUser(newUser);
    localStorage.setItem('maritime_user', JSON.stringify(newUser));
    localStorage.setItem('maritime_access_token', 'demo_jwt_access_token_' + Date.now());
    setIsLoading(false);

    const target = getDashboardPathForRole(role);
    router.push(target);
  };

  const quickLogin = (role: UserRole) => {
    const demoUser = DEMO_USERS[role];
    setUser(demoUser);
    localStorage.setItem('maritime_user', JSON.stringify(demoUser));
    localStorage.setItem('maritime_access_token', 'demo_jwt_access_token_' + role);
    const target = getDashboardPathForRole(role);
    router.push(target);
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('maritime_user');
    localStorage.removeItem('maritime_access_token');
    localStorage.removeItem('maritime_refresh_token');
    router.push('/login');
  };

  const toggleDemoMode = (val?: boolean) => {
    const nextVal = val !== undefined ? val : !isDemoMode;
    setIsDemoMode(nextVal);
    localStorage.setItem('maritime_demo_mode', String(nextVal));
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: !!user,
        isDemoMode,
        login,
        register,
        quickLogin,
        logout,
        toggleDemoMode,
        getDashboardPathForRole,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
