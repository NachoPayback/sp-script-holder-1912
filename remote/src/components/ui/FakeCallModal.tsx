import React from 'react';
import styled from 'styled-components';
import { theme } from '../../styles/theme';

interface FakeCallModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const ModalOverlay = styled.div<{ $show: boolean }>`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(8px);
  display: ${props => props.$show ? 'flex' : 'none'};
  align-items: center;
  justify-content: center;
  z-index: 9999;
  animation: ${props => props.$show ? 'fadeIn' : 'fadeOut'} 0.3s ease;

  @keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
  }
  
  @keyframes fadeOut {
    from { opacity: 1; }
    to { opacity: 0; }
  }
`;

const ModalContent = styled.div`
  background: linear-gradient(135deg, rgba(30, 41, 59, 0.95) 0%, rgba(15, 23, 42, 0.95) 100%);
  border: 2px solid ${theme.colors.primary}40;
  border-radius: ${theme.borderRadius.xl};
  padding: 40px;
  max-width: 500px;
  width: 90%;
  box-shadow: 
    0 25px 50px rgba(0, 0, 0, 0.5),
    0 0 50px rgba(59, 130, 246, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(20px);
  text-align: center;
  animation: slideIn 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);

  @keyframes slideIn {
    from {
      transform: translateY(-50px) scale(0.9);
      opacity: 0;
    }
    to {
      transform: translateY(0) scale(1);
      opacity: 1;
    }
  }
`;

const ModalTitle = styled.h2`
  font-size: 2.5rem;
  font-weight: ${theme.fonts.weights.black};
  color: #f59e0b;
  margin: 0 0 20px 0;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  text-shadow: 0 0 20px rgba(245, 158, 11, 0.5);
  animation: warning 2s ease-in-out infinite;

  @keyframes warning {
    0%, 100% { color: #f59e0b; text-shadow: 0 0 20px rgba(245, 158, 11, 0.5); }
    50% { color: #ef4444; text-shadow: 0 0 20px rgba(239, 68, 68, 0.5); }
  }
`;

const ModalMessage = styled.p`
  font-size: 1.4rem;
  font-weight: ${theme.fonts.weights.semibold};
  color: ${theme.colors.text};
  margin: 0 0 30px 0;
  line-height: 1.5;
`;

const CloseButton = styled.button`
  background: linear-gradient(135deg, ${theme.colors.primary} 0%, #6366f1 100%);
  border: none;
  color: white;
  padding: 15px 30px;
  border-radius: ${theme.borderRadius.lg};
  font-family: ${theme.fonts.family};
  font-size: 1.1rem;
  font-weight: ${theme.fonts.weights.bold};
  cursor: pointer;
  transition: all 0.3s ease;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4);

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(59, 130, 246, 0.6);
    background: linear-gradient(135deg, #60a5fa 0%, #8b5cf6 100%);
  }

  &:active {
    transform: translateY(0);
  }
`;

export const FakeCallModal: React.FC<FakeCallModalProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  return (
    <ModalOverlay $show={isOpen} onClick={onClose}>
      <ModalContent onClick={(e) => e.stopPropagation()}>
        <ModalTitle>⚠️ NOTICE ⚠️</ModalTitle>
        <ModalMessage>
          The call is not on the computer,<br />
          Go and do it yourself!
        </ModalMessage>
        <CloseButton onClick={onClose}>
          GOT IT
        </CloseButton>
      </ModalContent>
    </ModalOverlay>
  );
};