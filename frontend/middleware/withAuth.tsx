/**
 * Higher-order component for protected routes
 */

'use client';

import { useEffect, ComponentType } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '../lib/hooks/useAuth';
import type { User } from '../types/auth';

interface WithAuthOptions {
  /** Redirect path for unauthenticated users */
  redirectTo?: string;
  /** Required roles for access */
  requiredRoles?: string[];
  /** Redirect path when user lacks required roles */
  unauthorizedRedirect?: string;
  /** Show loading component while checking auth */
  LoadingComponent?: ComponentType;
}

interface AuthenticatedProps {
  user: User;
}

/**
 * HOC to protect routes that require authentication
 */
export function withAuth<P extends AuthenticatedProps>(
  WrappedComponent: ComponentType<P>,
  options: WithAuthOptions = {}
) {
  const {
    redirectTo = '/login',
    requiredRoles = [],
    unauthorizedRedirect = '/unauthorized',
    LoadingComponent,
  } = options;

  return function AuthenticatedComponent(props: Omit<P, keyof AuthenticatedProps>) {
    const router = useRouter();
    const { user, isAuthenticated, isLoading } = useAuth();

    useEffect(() => {
      if (!isLoading) {
        if (!isAuthenticated) {
          router.replace(redirectTo);
          return;
        }

        // Check required roles
        if (requiredRoles.length > 0 && user) {
          const hasRequiredRole = requiredRoles.some((role) =>
            user.roles.includes(role)
          );
          if (!hasRequiredRole) {
            router.replace(unauthorizedRedirect);
          }
        }
      }
    }, [isLoading, isAuthenticated, user, router]);

    // Show loading state
    if (isLoading) {
      if (LoadingComponent) {
        return <LoadingComponent />;
      }
      return (
        <div className="flex items-center justify-center min-h-screen">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900" />
        </div>
      );
    }

    // Not authenticated
    if (!isAuthenticated || !user) {
      return null;
    }

    // Check roles
    if (requiredRoles.length > 0) {
      const hasRequiredRole = requiredRoles.some((role) =>
        user.roles.includes(role)
      );
      if (!hasRequiredRole) {
        return null;
      }
    }

    // Render protected component
    return <WrappedComponent {...(props as P)} user={user} />;
  };
}

/**
 * HOC for admin-only routes
 */
export function withAdminAuth<P extends AuthenticatedProps>(
  WrappedComponent: ComponentType<P>
) {
  return withAuth(WrappedComponent, {
    requiredRoles: ['admin'],
    unauthorizedRedirect: '/unauthorized',
  });
}

/**
 * HOC for manager-or-above routes
 */
export function withManagerAuth<P extends AuthenticatedProps>(
  WrappedComponent: ComponentType<P>
) {
  return withAuth(WrappedComponent, {
    requiredRoles: ['admin', 'manager'],
    unauthorizedRedirect: '/unauthorized',
  });
}
