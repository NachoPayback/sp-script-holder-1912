// Hub Service - Handles all hub-related logic
// Based on vanilla version's hub.js module

import { hubApi, scriptApi, assignmentApi } from './api';
import { authService } from './AuthService';
import type { Hub, HubScript, Assignment } from '../types/Hub';

interface HubState {
  hubs: Hub[];
  selectedHub: Hub | null;
  scripts: HubScript[];
  assignment: Assignment | null;
  friendlyNames: Record<string, { friendly_name: string }>;
  connectedUsers: any[];
  loading: boolean;
}

type HubListener = (state: HubState) => void;

class HubService {
  private state: HubState = {
    hubs: [],
    selectedHub: null,
    scripts: [],
    assignment: null,
    friendlyNames: {},
    connectedUsers: [],
    loading: false
  };
  
  private listeners: HubListener[] = [];
  private autoRefreshInterval: NodeJS.Timeout | null = null;

  constructor() {
    // Start auto-refresh when authenticated
    authService.subscribe((authState) => {
      if (authState.user) {
        this.startAutoRefresh();
        this.discoverHubs();
      } else {
        this.stopAutoRefresh();
        this.reset();
      }
    });
  }

  subscribe(listener: HubListener): () => void {
    this.listeners.push(listener);
    return () => {
      this.listeners = this.listeners.filter(l => l !== listener);
    };
  }

  private notify() {
    this.listeners.forEach(listener => listener({ ...this.state }));
  }

  private setState(updates: Partial<HubState>) {
    this.state = { ...this.state, ...updates };
    this.notify();
  }

  private reset() {
    this.setState({
      hubs: [],
      selectedHub: null,
      scripts: [],
      assignment: null,
      friendlyNames: {},
      connectedUsers: [],
      loading: false
    });
  }

  private startAutoRefresh() {
    this.stopAutoRefresh();
    this.autoRefreshInterval = setInterval(() => {
      if (!this.state.selectedHub) {
        this.discoverHubs();
      } else {
        this.updateConnectedUsers();
      }
    }, 30000); // 30 seconds like vanilla
  }

  private stopAutoRefresh() {
    if (this.autoRefreshInterval) {
      clearInterval(this.autoRefreshInterval);
      this.autoRefreshInterval = null;
    }
  }

  async discoverHubs(): Promise<void> {
    this.setState({ loading: true });
    
    try {
      const response = await hubApi.getHubs();
      if (response.success && response.hubs) {
        this.setState({ 
          hubs: response.hubs,
          loading: false 
        });
      } else {
        this.setState({ 
          hubs: [],
          loading: false 
        });
      }
    } catch (error) {
      console.error('Failed to discover hubs:', error);
      this.setState({ 
        hubs: [],
        loading: false 
      });
    }
  }

  async connectToHub(hub: Hub): Promise<void> {
    this.setState({ selectedHub: hub, loading: true });
    
    try {
      // Load scripts
      const scriptsResponse = await hubApi.getHubScripts(hub.id);
      const scripts = scriptsResponse.success ? scriptsResponse.scripts : [];
      
      // Load assignment if in assigned mode
      let assignment = null;
      const user = authService.getCurrentUser();
      if (hub.mode === 'assigned' && user) {
        const assignmentResponse = await assignmentApi.get(hub.id, user.username);
        assignment = assignmentResponse.assignment || null;
      }

      // Load friendly names
      const scriptNames = scripts.map(s => 
        typeof s === 'string' ? s : s.script_name
      );
      const friendlyResponse = await hubApi.getFriendlyNames(scriptNames);
      const friendlyNames = friendlyResponse.success ? friendlyResponse.friendly_names : {};

      // Load connected users
      await this.updateConnectedUsers(hub.id);

      this.setState({
        scripts,
        assignment,
        friendlyNames,
        loading: false
      });
    } catch (error) {
      console.error('Failed to connect to hub:', error);
      this.setState({ loading: false });
    }
  }

  async updateConnectedUsers(hubId?: string): Promise<void> {
    const currentHub = hubId ? { id: hubId } : this.state.selectedHub;
    const user = authService.getCurrentUser();
    
    if (!currentHub || !user) return;

    try {
      const response = await hubApi.getConnectedUsers(currentHub.id);
      if (response.success && response.users && response.users.length > 0) {
        this.setState({ connectedUsers: response.users });
      } else {
        // Fallback to current user like vanilla version
        this.setState({ 
          connectedUsers: [{ username: user.username, user_id: user.username }] 
        });
      }
    } catch (error) {
      console.error('Error fetching connected users:', error);
      this.setState({ 
        connectedUsers: [{ username: user.username, user_id: user.username }] 
      });
    }
  }

  async executeScript(scriptName: string): Promise<boolean> {
    const { selectedHub } = this.state;
    const user = authService.getCurrentUser();
    
    if (!selectedHub || !user) {
      throw new Error('No hub selected or user not authenticated');
    }

    try {
      const result = await scriptApi.execute(selectedHub.id, scriptName, user.username);
      return result.success || false;
    } catch (error) {
      console.error('Failed to execute script:', error);
      throw error;
    }
  }

  backToHubs(): void {
    this.setState({
      selectedHub: null,
      scripts: [],
      assignment: null,
      connectedUsers: []
    });
  }

  getState(): HubState {
    return { ...this.state };
  }

  getConnectedHub(): Hub | null {
    return this.state.selectedHub;
  }
}

// Export singleton instance
export const hubService = new HubService();