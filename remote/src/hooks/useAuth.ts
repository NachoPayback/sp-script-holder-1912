import { useState, useEffect } from 'react';
import type { User } from '../types/User';
import { authApi } from '../services/api';

export const useAuth = () => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    // Check if user is already authenticated via localStorage token
    const checkAuth = async () => {
      try {
        const token = localStorage.getItem('sp_crew_token');
        if (token) {
          const result = await authApi.verify(token);
          if (result.valid && result.user) {
            // Always fetch fresh permissions from database, don't trust token
            const permissionsResult = await authApi.getUserPermissions(result.user.username);
            const freshPermissions = permissionsResult.success ? permissionsResult.permissions : undefined;
            setUser({
              username: result.user.username,
              isAuthenticated: true,
              permissions: freshPermissions
            });
            setLoading(false);
            return;
          }
        }
      } catch (err) {
        console.error('Auth check failed:', err);
        localStorage.removeItem('sp_crew_token');
      }
      setLoading(false);
    };

    checkAuth();
  }, []);

  const login = async (username: string, password: string): Promise<boolean> => {
    setLoading(true);
    setError('');
    
    try {
      const result = await authApi.login(username, password);
      
      if (result.success && result.user && result.token) {
        // Store token in localStorage like vanilla version
        localStorage.setItem('sp_crew_token', result.token);
        setUser({
          username: result.user.username,
          isAuthenticated: true,
          permissions: result.user.permissions
        });
        return true;
      } else {
        setError(result.error || 'Login failed');
        return false;
      }
    } catch {
      setError('Network error during login');
      return false;
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    setUser(null);
    setError('');
    // Clear stored token like vanilla version
    localStorage.removeItem('sp_crew_token');
  };

  return {
    user,
    loading,
    error,
    login,
    logout,
    isAuthenticated: !!user?.isAuthenticated
  };
};