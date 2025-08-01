// UI Service - Handles toasts, notifications, and UI feedback
// Based on vanilla version's ui.js module

interface Toast {
  id: string;
  message: string;
  type: 'success' | 'error' | 'info';
  duration: number;
}

interface UIState {
  toasts: Toast[];
}

type UIListener = (state: UIState) => void;

class UIService {
  private state: UIState = {
    toasts: []
  };
  
  private listeners: UIListener[] = [];

  subscribe(listener: UIListener): () => void {
    this.listeners.push(listener);
    return () => {
      this.listeners = this.listeners.filter(l => l !== listener);
    };
  }

  private notify() {
    this.listeners.forEach(listener => listener({ ...this.state }));
  }

  private setState(updates: Partial<UIState>) {
    this.state = { ...this.state, ...updates };
    this.notify();
  }

  showToast(message: string, type: 'success' | 'error' | 'info' = 'info', duration: number = 3000): string {
    const id = Date.now().toString();
    const toast: Toast = { id, message, type, duration };
    
    const updatedToasts = [...this.state.toasts, toast];
    this.setState({ toasts: updatedToasts });

    // Auto-remove toast after duration
    setTimeout(() => {
      this.removeToast(id);
    }, duration);

    return id;
  }

  removeToast(id: string): void {
    const updatedToasts = this.state.toasts.filter(toast => toast.id !== id);
    this.setState({ toasts: updatedToasts });
  }

  clearToasts(): void {
    this.setState({ toasts: [] });
  }

  // Convenience methods
  showSuccess(message: string, duration?: number): string {
    return this.showToast(message, 'success', duration);
  }

  showError(message: string, duration?: number): string {
    return this.showToast(message, 'error', duration);
  }

  showInfo(message: string, duration?: number): string {
    return this.showToast(message, 'info', duration);
  }

  getState(): UIState {
    return { ...this.state };
  }
}

// Export singleton instance
export const uiService = new UIService();