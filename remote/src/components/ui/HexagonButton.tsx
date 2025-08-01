import React from 'react';
import styled from 'styled-components';
import { theme } from '../../styles/theme';

interface HexagonButtonProps {
  scriptName: string;
  color: string;
  friendlyName?: string;
  showName?: boolean;
  onClick: () => void;
  className?: string;
}

const ButtonContainer = styled.div`
  position: relative;
  width: ${theme.button.size}px;
  height: ${theme.button.size}px;
  cursor: pointer;
  transition: all ${theme.animations.normal} ${theme.animations.easing};
  
  &:hover {
    transform: scale(1.08);
  }
  
  &:active {
    transform: scale(0.95);
  }
`;

const HexagonSVG = styled.svg`
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
`;

const HexagonPath = styled.path<{ $color: string }>`
  fill: url(#gradient-${props => props.$color.replace('#', '')});
  stroke: ${props => props.$color};
  stroke-width: ${theme.button.borderWidth};
  filter: drop-shadow(0 0 20px ${props => props.$color}33);
  transition: filter ${theme.animations.normal} ${theme.animations.easing};
  
  ${ButtonContainer}:hover & {
    filter: drop-shadow(0 0 40px ${props => props.$color}66);
  }
`;

const TextContainer = styled.div<{ $color: string }>`
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  color: ${props => props.$color};
  pointer-events: none;
  z-index: 10;
`;

const ExecuteText = styled.div`
  font-size: 1.1rem;
  font-weight: ${theme.fonts.weights.bold};
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-family: ${theme.fonts.family};
`;

const ScriptName = styled.div`
  font-size: 0.75rem;
  font-weight: ${theme.fonts.weights.medium};
  margin-top: ${theme.spacing.sm};
  opacity: 0.9;
  max-width: 140px;
  line-height: 1.2;
  font-family: ${theme.fonts.family};
`;

// Your custom hexagon path from the SVG
const HEXAGON_PATH = "M245.57,681.92c-40.75,0-78.72-21.92-99.1-57.21L15.83,398.42c-20.37-35.29-20.37-79.14,0-114.43L146.48,57.71C166.85,22.42,204.82.5,245.57.5h261.29c40.75,0,78.72,21.92,99.1,57.21l130.65,226.29c20.37,35.29,20.37,79.14,0,114.43l-130.65,226.29c-20.38,35.29-58.35,57.21-99.1,57.21H245.57Z";

export const HexagonButton: React.FC<HexagonButtonProps> = ({
  scriptName,
  color,
  friendlyName,
  showName = false,
  onClick,
  className
}) => {
  const gradientId = `gradient-${color.replace('#', '')}`;
  const displayName = friendlyName || scriptName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());

  return (
    <ButtonContainer onClick={onClick} className={className}>
      <HexagonSVG viewBox="0 0 752.44 682.42">
        <defs>
          <radialGradient id={gradientId} cx="30%" cy="30%">
            <stop offset="0%" stopColor="rgba(255, 255, 255, 0.1)" />
            <stop offset="50%" stopColor="transparent" />
          </radialGradient>
        </defs>
        <HexagonPath 
          d={HEXAGON_PATH} 
          $color={color}
        />
      </HexagonSVG>
      
      <TextContainer $color={color}>
        <ExecuteText>EXECUTE</ExecuteText>
        {showName && (
          <ScriptName>{displayName.toUpperCase()}</ScriptName>
        )}
      </TextContainer>
    </ButtonContainer>
  );
};