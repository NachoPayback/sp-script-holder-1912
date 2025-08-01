import React from 'react';
import styled, { keyframes } from 'styled-components';
import { useUI } from '../../hooks/useServices';
import { theme } from '../../styles/theme';

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
      default: return 'rgba(59, 130, 246, 0.9)';
    }
  }};
  color: white;
  padding: 12px 16px;
  border-radius: 8px;
  backdrop-filter: blur(10px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  font-family: ${theme.fonts.family};
  font-weight: 500;
  animation: ${slideIn} 0.3s ease-out;
  pointer-events: auto;
  cursor: pointer;
  max-width: 300px;
  word-wrap: break-word;
  
  &:hover {
    opacity: 0.8;
  }
`;

export const ToastContainer: React.FC = () => {
  const { toasts, removeToast } = useUI();

  return (
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
  );
};