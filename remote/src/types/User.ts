export interface User {
  username: string;
  isAuthenticated: boolean;
  permissions?: {
    admin?: boolean;
    all_hubs?: boolean;
  };
}

export interface AuthResponse {
  success: boolean;
  user?: {
    username: string;
    permissions?: {
      admin?: boolean;
      all_hubs?: boolean;
    };
  };
  token?: string;
  error?: string;
}

export interface ConnectedUser {
  user_id: string;
  hub_id: string;
  last_seen: string;
}