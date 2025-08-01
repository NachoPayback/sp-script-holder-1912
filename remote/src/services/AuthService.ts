// Authentication Service - Handles all auth logic
// Based on vanilla version's auth.js module

import { authApi } from './api';
import type { User } from '../types/User';

interface AuthState {
  user: User | null;
  loading: boolean;
  error: string;
}

type AuthListener = (state: AuthState) => void;

class AuthService {
  private state: AuthState = {
    user: null,
    loading: true,
    error: ''
  };
  
  private listeners: AuthListener[] = [];

  constructor() {
    this.checkAuthentication();
  }

  // Subscribe to auth state changes
  subscribe(listener: AuthListener): () => void {
    this.listeners.push(listener);
    // Return unsubscribe function
    return () => {
      this.listeners = this.listeners.filter(l => l !== listener);
    };
  }

  private notify() {
    this.listeners.forEach(listener => listener({ ...this.state }));
  }

  private setState(updates: Partial<AuthState>) {
    this.state = { ...this.state, ...updates };
    this.notify();
  }

  async checkAuthentication(): Promise<void> {
    try {
      const token = localStorage.getItem('sp_crew_token');
      if (token) {
        const result = await authApi.verify(token);
        if (result.valid && result.user) {
          this.setState({
            user: {
              username: result.user.username,
              isAuthenticated: true
            },
            loading: false
          });
          return;
        }
      }
    } catch (error) {
      console.error('Auth check failed:', error);
      localStorage.removeItem('sp_crew_token');
    }
    
    this.setState({ loading: false });
  }

  async login(username: string, password: string): Promise<boolean> {
    this.setState({ loading: true, error: '' });
    
    try {
      const result = await authApi.login(username, password);
      
      if (result.success && result.user && result.token) {
        localStorage.setItem('sp_crew_token', result.token);
        this.setState({
          user: {
            username: result.user.username,
            isAuthenticated: true
          },
          loading: false
        });
        return true;
      } else {
        this.setState({ 
          error: result.error || 'Login failed',
          loading: false 
        });
        return false;
      }
    } catch {
      this.setState({ 
        error: 'Network error during login',
        loading: false 
      });
      return false;
    }
  }

  logout(): void {
    localStorage.removeItem('sp_crew_token');
    this.setState({
      user: null,
      error: ''
    });
  }

  getCurrentUser(): User | null {
    return this.state.user;
  }
}

// Export singleton instance
export const authService = new AuthService();