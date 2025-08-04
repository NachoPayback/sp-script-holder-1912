import React, { useState } from 'react';
import styled from 'styled-components';
import { theme } from '../../styles/theme';

interface LoginFormProps {
  onLogin: (username: string, password: string) => Promise<boolean>;
  loading: boolean;
  error: string;
}

const LoginContainer = styled.div`
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, #0A0A0A 0%, #141414 50%, #0A0A0A 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  
  /* Subtle tech pattern */
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-image: 
      radial-gradient(circle at 25% 25%, ${theme.colors.glow} 0%, transparent 50%),
      radial-gradient(circle at 75% 75%, ${theme.colors.glow} 0%, transparent 50%);
    opacity: 0.3;
  }
`;

const LoginBox = styled.div`
  background: ${theme.colors.surface};
  border: 1px solid ${theme.colors.border};
  border-radius: ${theme.borderRadius.lg};
  padding: ${theme.spacing.xxl};
  width: 100%;
  max-width: 400px;
  backdrop-filter: blur(20px);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
`;

const Title = styled.h1`
  font-family: ${theme.fonts.family};
  font-size: 2rem;
  font-weight: ${theme.fonts.weights.extraBold};
  color: ${theme.colors.text};
  text-align: center;
  margin-bottom: ${theme.spacing.sm};
  text-shadow: 0 0 20px ${theme.colors.glow};
`;

const Subtitle = styled.p`
  font-family: ${theme.fonts.family};
  color: ${theme.colors.textSecondary};
  text-align: center;
  margin-bottom: ${theme.spacing.xxl};
  opacity: 0.8;
`;

const Form = styled.form`
  display: flex;
  flex-direction: column;
  gap: ${theme.spacing.md};
`;

const Input = styled.input`
  width: 100%;
  padding: 12px;
  background: ${theme.colors.surfaceLight};
  border: 1px solid ${theme.colors.textDim};
  color: ${theme.colors.text};
  border-radius: ${theme.borderRadius.sm};
  font-size: 16px;
  font-family: ${theme.fonts.family};
  
  &:focus {
    outline: none;
    border-color: ${theme.colors.primary};
    box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
  }
`;

const LoginButton = styled.button`
  width: 100%;
  padding: 12px;
  margin-top: ${theme.spacing.md};
  background: ${theme.colors.primary};
  color: white;
  border: none;
  border-radius: ${theme.borderRadius.sm};
  font-size: 16px;
  font-weight: ${theme.fonts.weights.medium};
  font-family: ${theme.fonts.family};
  cursor: pointer;
  transition: all ${theme.animations.normal} ${theme.animations.easing};
  
  &:hover:not(:disabled) {
    background: #2563eb;
    transform: translateY(-1px);
  }
  
  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
`;

const ErrorMessage = styled.div`
  color: ${theme.colors.error};
  text-align: center;
  margin-top: ${theme.spacing.md};
  font-family: ${theme.fonts.family};
`;

export const LoginForm: React.FC<LoginFormProps> = ({ onLogin, loading, error }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (username && password) {
      await onLogin(username, password);
    }
  };

  return (
    <LoginContainer>
      <LoginBox>
        <Title>SP CREW CONTROL</Title>
        <Subtitle>Remote Command Interface</Subtitle>
        
        <Form onSubmit={handleSubmit}>
          <Input
            type="text"
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
            disabled={loading}
          />
          <Input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            disabled={loading}
          />
          <LoginButton type="submit" disabled={loading || !username || !password}>
            {loading ? 'LOGGING IN...' : 'LOGIN'}
          </LoginButton>
        </Form>
        
        {error && <ErrorMessage>{error}</ErrorMessage>}
      </LoginBox>
    </LoginContainer>
  );
};