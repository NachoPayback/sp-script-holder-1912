export interface User {
  username: string;
  isAuthenticated: boolean;
}

export interface AuthResponse {
  success: boolean;
  user?: {
    username: string;
  };
  token?: string;
  error?: string;
}

export interface ConnectedUser {
  user_id: string;
  hub_id: string;
  last_seen: string;
}