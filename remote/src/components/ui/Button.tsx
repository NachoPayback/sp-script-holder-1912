import styled, { css } from 'styled-components';

interface ButtonProps {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  children: React.ReactNode;
  onClick?: () => void;
  disabled?: boolean;
  className?: string;
}

const buttonVariants = {
  primary: css`
    background: ${props => props.theme.gradients.electric};
    border: 1px solid ${props => props.theme.colors.primary};
    color: ${props => props.theme.colors.text};
    
    &:hover:not(:disabled) {
      box-shadow: ${props => props.theme.shadows.glow};
      transform: translateY(-1px);
    }
  `,
  
  secondary: css`
    background: ${props => props.theme.colors.surface};
    border: 1px solid ${props => props.theme.colors.borderLight};
    color: ${props => props.theme.colors.text};
    
    &:hover:not(:disabled) {
      background: ${props => props.theme.colors.surfaceLight};
      border-color: ${props => props.theme.colors.primary}40;
    }
  `,
  
  danger: css`
    background: ${props => props.theme.colors.error}20;
    border: 1px solid ${props => props.theme.colors.error};
    color: ${props => props.theme.colors.error};
    
    &:hover:not(:disabled) {
      background: ${props => props.theme.colors.error}30;
    }
  `,
  
  ghost: css`
    background: transparent;
    border: 1px solid transparent;
    color: ${props => props.theme.colors.textSecondary};
    
    &:hover:not(:disabled) {
      background: ${props => props.theme.colors.surface};
      color: ${props => props.theme.colors.text};
      border-color: ${props => props.theme.colors.borderLight};
    }
  `,
};

const buttonSizes = {
  sm: css`
    padding: 6px 12px;
    font-size: 0.875rem;
    height: 32px;
  `,
  
  md: css`
    padding: 8px 16px;
    font-size: 0.925rem;
    height: 36px;
  `,
  
  lg: css`
    padding: 12px 20px;
    font-size: 1rem;
    height: 44px;
  `,
};

const StyledButton = styled.button<ButtonProps>`
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  border-radius: ${props => props.theme.borderRadius.lg};
  font-family: ${props => props.theme.fonts.family};
  font-weight: ${props => props.theme.fonts.weights.medium};
  letter-spacing: 0.025em;
  text-transform: uppercase;
  cursor: pointer;
  transition: all ${props => props.theme.animations.fast} ${props => props.theme.animations.easing};
  white-space: nowrap;
  user-select: none;
  
  ${props => buttonVariants[props.variant || 'secondary']}
  ${props => buttonSizes[props.size || 'md']}
  
  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    transform: none !important;
    box-shadow: none !important;
  }
  
  &:active:not(:disabled) {
    transform: translateY(0);
  }
  
  /* Icon styling */
  svg {
    width: 16px;
    height: 16px;
    flex-shrink: 0;
  }
`;

export const Button: React.FC<ButtonProps> = ({ 
  variant = 'secondary', 
  size = 'md', 
  children, 
  ...props 
}) => {
  return (
    <StyledButton variant={variant} size={size} {...props}>
      {children}
    </StyledButton>
  );
};