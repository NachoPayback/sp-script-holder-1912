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
  gap: ${theme.spacing.sm};
  flex: 1;
  overflow-y: auto;
  min-height: 300px;
  height: 100%;
  max-height: none;
  
  /* Custom scrollbar */
  &::-webkit-scrollbar {
    width: 8px;
  }
  
  &::-webkit-scrollbar-track {
    background: rgba(15, 23, 42, 0.8);
    border-radius: 4px;
    margin: 4px 0;
  }
  
  &::-webkit-scrollbar-thumb {
    background: linear-gradient(180deg, rgba(59, 130, 246, 0.4) 0%, rgba(99, 102, 241, 0.4) 100%);
    border-radius: 4px;
    border: 1px solid rgba(148, 163, 184, 0.1);
    transition: all 0.2s ease;
  }
  
  &::-webkit-scrollbar-thumb:hover {
    background: linear-gradient(180deg, rgba(59, 130, 246, 0.6) 0%, rgba(99, 102, 241, 0.6) 100%);
    border-color: rgba(148, 163, 184, 0.3);
  }
`;

const ActivityItemElement = styled.div<{ $status: string }>`
  padding: ${theme.spacing.sm} 12px;
  background: rgba(30, 41, 59, 0.3);
  border-radius: ${theme.spacing.sm};
  border-left: 3px solid ${props => {
    switch (props.$status) {
      case 'success': return theme.colors.success;
      case 'error': return theme.colors.error;
      default: return theme.colors.textSecondary;
    }
  }};
  font-size: 0.8rem;
  font-weight: ${theme.fonts.weights.normal};
  color: #cbd5e1;
  font-family: ${theme.fonts.family};
  
  ${props => props.$status === 'success' && `
    background: rgba(16, 185, 129, 0.1);
  `}
  
  ${props => props.$status === 'error' && `
    background: rgba(239, 68, 68, 0.1);
  `}
`;

const ActivityUser = styled.div`
  font-weight: ${theme.fonts.weights.medium};
  color: ${theme.colors.text};
`;

const ActivityAction = styled.div`
  margin: 2px 0;
`;

const ActivityTime = styled.div`
  display: flex;
  align-items: center;
  gap: ${theme.spacing.xs};
  font-size: 0.7rem;
  color: ${theme.colors.textSecondary};
  margin-top: 2px;
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