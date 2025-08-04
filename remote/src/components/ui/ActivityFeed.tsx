import React from 'react';
import styled from 'styled-components';
import { theme } from '../../styles/theme';

interface ActivityItem {
  id: string;
  user: string;
  action: string;
  status: 'pending' | 'success' | 'error';
  timestamp: string;
  commandId?: string;
}

interface ActivityFeedProps {
  items: ActivityItem[];
}

const ActivityContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: ${theme.spacing.md};
  flex: 1;
  overflow-y: auto;
  min-height: 0;
  height: 100%;
  
  /* Modern scrollbar */
  &::-webkit-scrollbar {
    width: 6px;
  }
  
  &::-webkit-scrollbar-track {
    background: transparent;
  }
  
  &::-webkit-scrollbar-thumb {
    background: ${theme.colors.primary}60;
    border-radius: 3px;
    transition: all ${theme.animations.fast} ${theme.animations.easing};
  }
  
  &::-webkit-scrollbar-thumb:hover {
    background: ${theme.colors.primary}80;
  }
`;

const ActivityItemElement = styled.div<{ $status: string }>`
  padding: ${theme.spacing.md};
  background: linear-gradient(135deg, rgba(20, 20, 20, 0.8) 0%, rgba(15, 15, 15, 0.9) 100%);
  border: 1px solid ${props => {
    switch (props.$status) {
      case 'success': return theme.colors.success + '40';
      case 'error': return theme.colors.error + '40';
      default: return theme.colors.primary + '30';
    }
  }};
  border-radius: ${theme.borderRadius.md};
  font-size: 0.85rem;
  font-weight: ${theme.fonts.weights.normal};
  color: ${theme.colors.text};
  font-family: ${theme.fonts.mono};
  position: relative;
  transition: all ${theme.animations.fast} ${theme.animations.easing};
  backdrop-filter: blur(10px);
  
  /* Status indicator */
  &::before {
    content: '';
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    width: 4px;
    background: ${props => {
      switch (props.$status) {
        case 'success': return theme.colors.success;
        case 'error': return theme.colors.error;
        default: return theme.colors.primary;
      }
    }};
    border-radius: 0 4px 4px 0;
  }
  
  &:hover {
    background: linear-gradient(135deg, rgba(25, 25, 25, 0.9) 0%, rgba(20, 20, 20, 1) 100%);
    border-color: ${props => {
      switch (props.$status) {
        case 'success': return theme.colors.success + '60';
        case 'error': return theme.colors.error + '60';
        default: return theme.colors.primary + '50';
      }
    }};
    transform: translateX(4px);
  }
  
  ${props => props.$status === 'success' && `
    box-shadow: 0 0 20px ${theme.colors.success}20;
  `}
  
  ${props => props.$status === 'error' && `
    box-shadow: 0 0 20px ${theme.colors.error}20;
  `}
  
  ${props => props.$status === 'pending' && `
    box-shadow: 0 0 20px ${theme.colors.primary}20;
  `}
`;

const ActivityUser = styled.div`
  font-weight: ${theme.fonts.weights.bold};
  color: ${theme.colors.primary};
  font-size: 0.9rem;
  margin-bottom: ${theme.spacing.xs};
`;

const ActivityAction = styled.div`
  margin: ${theme.spacing.xs} 0;
  color: ${theme.colors.text};
  line-height: 1.4;
`;

const ActivityTime = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 0.75rem;
  color: ${theme.colors.textSecondary};
  margin-top: ${theme.spacing.xs};
  font-family: ${theme.fonts.mono};
`;

const getStatusIcon = (status: string) => {
  switch (status) {
    case 'success': return '✅';
    case 'error': return '❌';
    default: return '⏳';
  }
};

export const ActivityFeed: React.FC<ActivityFeedProps> = ({ items }) => {
  return (
    <ActivityContainer>
      {items.map((item) => (
        <ActivityItemElement key={item.id} $status={item.status}>
          <ActivityUser>{item.user}</ActivityUser>
          <ActivityAction>{item.action}</ActivityAction>
          <ActivityTime>
            {item.timestamp} {getStatusIcon(item.status)}
          </ActivityTime>
        </ActivityItemElement>
      ))}
    </ActivityContainer>
  );
};