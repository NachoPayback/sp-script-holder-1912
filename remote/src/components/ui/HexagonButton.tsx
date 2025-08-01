import React from 'react';
import styled from 'styled-components';
import { theme } from '../../styles/theme';

interface HexagonButtonProps {
  scriptName: string;
  color: string;
  friendlyName?: string;
  imageUrl?: string;
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
  fill: ${theme.colors.surface};
  stroke: ${theme.colors.primary};
  stroke-width: ${theme.button.borderWidth};
  filter: drop-shadow(0 0 15px ${theme.colors.glow});
  transition: all ${theme.animations.normal} ${theme.animations.easing};
  
  ${ButtonContainer}:hover & {
    fill: ${theme.colors.surfaceLight};
    stroke: ${theme.colors.primaryLight};
    filter: drop-shadow(0 0 25px ${theme.colors.glowStrong});
    stroke-width: 3;
  }
`;

const TextContainer = styled.div`
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  color: ${theme.colors.primary};
  pointer-events: none;
  z-index: 10;
  transition: all ${theme.animations.fast} ${theme.animations.easing};
  
  ${ButtonContainer}:hover & {
    color: ${theme.colors.primaryLight};
    transform: translate(-50%, -50%) scale(1.05);
  }
`;

const ExecuteText = styled.div`
  font-size: 1.1rem;
  font-weight: ${theme.fonts.weights.extraBold};
  text-transform: uppercase;
  letter-spacing: 0.15em;
  font-family: ${theme.fonts.family};
  text-shadow: 0 0 10px currentColor;
`;

const ScriptName = styled.div`
  font-size: 0.7rem;
  font-weight: ${theme.fonts.weights.semibold};
  margin-top: ${theme.spacing.sm};
  opacity: 0.8;
  max-width: 140px;
  line-height: 1.2;
  font-family: ${theme.fonts.mono};
  letter-spacing: 0.05em;
`;

const ImageContainer = styled.div`
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  overflow: hidden;
  z-index: 5;
`;

const HexagonImage = styled.img`
  width: 100%;
  height: 100%;
  object-fit: cover;
  clip-path: polygon(30% 0%, 70% 0%, 100% 50%, 70% 100%, 30% 100%, 0% 50%);
  filter: brightness(0.9) contrast(1.1);
  transition: filter ${theme.animations.fast} ${theme.animations.easing};
  
  ${ButtonContainer}:hover & {
    filter: brightness(1.1) contrast(1.2);
  }
`;

// Your custom hexagon path from the SVG
const HEXAGON_PATH = "M245.57,681.92c-40.75,0-78.72-21.92-99.1-57.21L15.83,398.42c-20.37-35.29-20.37-79.14,0-114.43L146.48,57.71C166.85,22.42,204.82.5,245.57.5h261.29c40.75,0,78.72,21.92,99.1,57.21l130.65,226.29c20.37,35.29,20.37,79.14,0,114.43l-130.65,226.29c-20.38,35.29-58.35,57.21-99.1,57.21H245.57Z";

export const HexagonButton: React.FC<HexagonButtonProps> = ({
  scriptName,
  color,
  friendlyName,
  imageUrl,
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
          <linearGradient id={gradientId} x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor={theme.colors.primary} stopOpacity="0.2" />
            <stop offset="50%" stopColor={theme.colors.primaryLight} stopOpacity="0.1" />
            <stop offset="100%" stopColor={theme.colors.primary} stopOpacity="0.2" />
          </linearGradient>
        </defs>
        <HexagonPath 
          d={HEXAGON_PATH} 
          $color={color}
        />
      </HexagonSVG>
      
      {/* Show image if provided, otherwise show text */}
      {imageUrl ? (
        <ImageContainer>
          <HexagonImage src={imageUrl} alt={displayName} />
        </ImageContainer>
      ) : (
        <TextContainer>
          <ExecuteText>EXECUTE</ExecuteText>
          {showName && (
            <ScriptName>{displayName.toUpperCase()}</ScriptName>
          )}
        </TextContainer>
      )}
    </ButtonContainer>
  );
};