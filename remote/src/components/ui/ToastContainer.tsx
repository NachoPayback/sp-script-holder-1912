import React, { useState, createContext, useContext } from 'react';
import styled, { keyframes } from 'styled-components';

interface Toast {
  id: string;
  message: string;
  type: 'success' | 'error' | 'info';
}

interface ToastContextType {
  showSuccess: (message: string) => void;
  showError: (message: string) => void;
  showInfo: (message: string) => void;
}

const ToastContext = createContext<ToastContextType | null>(null);

export const useToast = () => {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within ToastProvider');
  }
  return context;
};

const slideIn = keyframes`
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
`;

const ToastContainerWrapper = styled.div`
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 1000;
  display: flex;
  flex-direction: column;
  gap: 10px;
  pointer-events: none;
`;

const Toast = styled.div<{ type: 'success' | 'error' | 'info' }>`
  background: ${props => {
    switch (props.type) {
      case 'success': return 'rgba(16, 185, 129, 0.9)';
      case 'error': return 'rgba(239, 68, 68, 0.9)';
      case 'info': return 'rgba(59, 130, 246, 0.9)';
      default: return 'rgba(75, 85, 99, 0.9)';
    }
  }};
  color: white;
  padding: 12px 16px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  animation: ${slideIn} 0.3s ease-out;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  pointer-events: auto;
  cursor: pointer;
  max-width: 300px;
  word-wrap: break-word;
  
  &:hover {
    opacity: 0.8;
  }
`;

export const ToastProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const addToast = (message: string, type: Toast['type']) => {
    const id = Math.random().toString(36).substr(2, 9);
    setToasts(prev => [...prev, { id, message, type }]);
    
    // Auto-remove after 4 seconds
    setTimeout(() => {
      setToasts(prev => prev.filter(toast => toast.id !== id));
    }, 4000);
  };

  const removeToast = (id: string) => {
    setToasts(prev => prev.filter(toast => toast.id !== id));
  };

  const showSuccess = (message: string) => addToast(message, 'success');
  const showError = (message: string) => addToast(message, 'error');
  const showInfo = (message: string) => addToast(message, 'info');

  return (
    <ToastContext.Provider value={{ showSuccess, showError, showInfo }}>
      {children}
      <ToastContainerWrapper>
        {toasts.map(toast => (
          <Toast
            key={toast.id}
            type={toast.type}
            onClick={() => removeToast(toast.id)}
          >
            {toast.message}
          </Toast>
        ))}
      </ToastContainerWrapper>
    </ToastContext.Provider>
  );
};

export const ToastContainer: React.FC = () => null; // Component is now handled by ToastProvider