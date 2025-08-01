// Activity Service - Handles activity log and real-time updates
// Based on vanilla version's activity.js module

import { authService } from './AuthService';

interface ActivityItem {
  id: string;
  user: string;
  action: string;
  status: 'pending' | 'success' | 'error';
  timestamp: string;
  commandId?: string;
}

interface ActivityState {
  items: ActivityItem[];
}

type ActivityListener = (state: ActivityState) => void;

class ActivityService {
  private state: ActivityState = {
    items: []
  };
  
  private listeners: ActivityListener[] = [];

  subscribe(listener: ActivityListener): () => void {
    this.listeners.push(listener);
    return () => {
      this.listeners = this.listeners.filter(l => l !== listener);
    };
  }

  private notify() {
    this.listeners.forEach(listener => listener({ ...this.state }));
  }

  private setState(updates: Partial<ActivityState>) {
    this.state = { ...this.state, ...updates };
    this.notify();
  }

  addToActivityLog(action: string, status: 'pending' | 'success' | 'error' = 'pending', commandId?: string): string {
    const user = authService.getCurrentUser();
    if (!user) return '';

    const activityId = Date.now().toString();
    const newItem: ActivityItem = {
      id: activityId,
      user: user.username,
      action,
      status,
      timestamp: new Date().toLocaleTimeString(),
      commandId
    };

    const updatedItems = [newItem, ...this.state.items.slice(0, 49)]; // Keep last 50 items
    this.setState({ items: updatedItems });
    
    return activityId;
  }

  updateActivityLogByCommandId(commandId: string, status: 'success' | 'error'): void {
    const updatedItems = this.state.items.map(item => 
      item.commandId === commandId ? { ...item, status } : item
    );
    this.setState({ items: updatedItems });
  }

  updateActivityLogById(id: string, status: 'success' | 'error'): void {
    const updatedItems = this.state.items.map(item => 
      item.id === id ? { ...item, status } : item
    );
    this.setState({ items: updatedItems });
  }

  clearActivityLog(): void {
    this.setState({ items: [] });
  }

  getState(): ActivityState {
    return { ...this.state };
  }
}

// Export singleton instance
export const activityService = new ActivityService();