import type { Hub, HubScript, Assignment } from '../types/Hub';
import type { AuthResponse, ConnectedUser } from '../types/User';
import type { FriendlyName } from '../types/Script';

const API_BASE = '';  // Relative to current domain

/**
 * Authentication API
 */
export const authApi = {
  login: async (username: string, password: string): Promise<AuthResponse> => {
    const response = await fetch(`${API_BASE}/api/auth`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });
    return response.json();
  },

  verify: async (token: string): Promise<{ valid: boolean; user?: { username: string } }> => {
    const response = await fetch(`${API_BASE}/api/verify`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token })
    });
    return response.json();
  }
};

/**
 * Hub API
 */
export const hubApi = {
  getHubs: async (): Promise<{ success: boolean; hubs: Hub[] }> => {
    const response = await fetch(`${API_BASE}/api/hubs`);
    return response.json();
  },

  getHubScripts: async (hubId: string): Promise<{ success: boolean; scripts: HubScript[] }> => {
    const response = await fetch(`${API_BASE}/api/hub-scripts?hub_id=${hubId}`);
    return response.json();
  },

  getConnectedUsers: async (hubId: string): Promise<{ success: boolean; users: ConnectedUser[] }> => {
    const response = await fetch(`${API_BASE}/api/connected-users?hub_id=${hubId}`);
    return response.json();
  },

  getFriendlyNames: async (scriptNames?: string[]): Promise<{ success: boolean; friendly_names: Record<string, { friendly_name: string }> }> => {
    let url = `${API_BASE}/api/script-friendly-names`;
    if (scriptNames && scriptNames.length > 0) {
      url += `?script_names=${scriptNames.join(',')}`;
    }
    const response = await fetch(url);
    return response.json();
  }
};

/**
 * Script API
 */
export const scriptApi = {
  execute: async (hubId: string, scriptName: string, userId: string): Promise<{ success: boolean; commandId?: string; message?: string }> => {
    const response = await fetch(`${API_BASE}/api/execute`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ hub_id: hubId, script_name: scriptName, user_id: userId })
    });
    return response.json();
  },

  getFriendlyNames: async (scriptNames?: string[]): Promise<{ success: boolean; friendly_names: Record<string, FriendlyName> }> => {
    let url = `${API_BASE}/api/script-friendly-names`;
    if (scriptNames && scriptNames.length > 0) {
      url += `?script_names=${scriptNames.join(',')}`;
    }
    const response = await fetch(url);
    return response.json();
  }
};

/**
 * Assignment API (for 1 Button mode)
 */
export const assignmentApi = {
  request: async (hubId: string, userId: string): Promise<{ success: boolean }> => {
    const response = await fetch(`${API_BASE}/api/remote-assignment`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ hub_id: hubId, user_id: userId })
    });
    return response.json();
  },

  get: async (hubId: string, userId: string): Promise<{ success: boolean; assignment?: Assignment }> => {
    const response = await fetch(`${API_BASE}/api/remote-assignment?hub_id=${hubId}&user_id=${userId}`);
    return response.json();
  }
};