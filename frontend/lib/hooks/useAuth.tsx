/**
 * React hook for authentication state management
 */

'use client';

import { useState, useEffect, useCallback, createContext, useContext, ReactNode } from 'react';
import type { User, LoginCredentials, RegisterData, AuthState } from '../../types/auth';
import {
  login as authLogin,
  logout as authLogout,
  register as authRegister,
  getCurrentUser,
  getCachedUser,
  isAuthenticated as checkIsAuthenticated,
} from '../auth';
import { clearAuthStorage } from '../utils/storage';

interface AuthContextValue extends AuthState {
  login: (credentials: LoginCredentials) => Promise<User>;
  logout: () => Promise<void>;
  register: (data: RegisterData) => Promise<User>;
  refreshUser: () => Promise<User | null>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [state, setState] = useState<AuthState>({
    user: null,
    isAuthenticated: false,
    isLoading: true,
    error: null,
  });

  // Initialize auth state
  useEffect(() => {
    const initAuth = async () => {
      // Check for cached user first
      const cachedUser = getCachedUser();

      if (checkIsAuthenticated()) {
        try {
          // Verify token is still valid by fetching user
          const user = await getCurrentUser();
          setState({
            user,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          });
        } catch {
          // Token invalid, clear storage
          clearAuthStorage();
          setState({
            user: null,
            isAuthenticated: false,
            isLoading: false,
            error: null,
          });
        }
      } else {
        setState({
          user: cachedUser,
          isAuthenticated: false,
          isLoading: false,
          error: null,
        });
      }
    };

    initAuth();
  }, []);

  const login = useCallback(async (credentials: LoginCredentials): Promise<User> => {
    setState((prev) => ({ ...prev, isLoading: true, error: null }));

    try {
      const response = await authLogin(credentials);
      setState({
        user: response.user,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      });
      return response.user;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Login failed';
      setState((prev) => ({
        ...prev,
        isLoading: false,
        error: message,
      }));
      throw err;
    }
  }, []);

  const logout = useCallback(async (): Promise<void> => {
    setState((prev) => ({ ...prev, isLoading: true }));

    await authLogout();
    setState({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
    });
  }, []);

  const register = useCallback(async (data: RegisterData): Promise<User> => {
    setState((prev) => ({ ...prev, isLoading: true, error: null }));

    try {
      const user = await authRegister(data);
      setState((prev) => ({
        ...prev,
        isLoading: false,
      }));
      return user;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Registration failed';
      setState((prev) => ({
        ...prev,
        isLoading: false,
        error: message,
      }));
      throw err;
    }
  }, []);

  const refreshUser = useCallback(async (): Promise<User | null> => {
    if (!checkIsAuthenticated()) return null;

    try {
      const user = await getCurrentUser();
      setState((prev) => ({
        ...prev,
        user,
        isAuthenticated: true,
      }));
      return user;
    } catch {
      return null;
    }
  }, []);

  const value: AuthContextValue = {
    ...state,
    login,
    logout,
    register,
    refreshUser,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

/**
 * Hook to access auth context
 */
export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

/**
 * Hook to get current user
 */
export function useUser(): User | null {
  const { user } = useAuth();
  return user;
}

/**
 * Hook to check if user is authenticated
 */
export function useIsAuthenticated(): boolean {
  const { isAuthenticated } = useAuth();
  return isAuthenticated;
}

/**
 * Hook to check if auth is loading
 */
export function useAuthLoading(): boolean {
  const { isLoading } = useAuth();
  return isLoading;
}
