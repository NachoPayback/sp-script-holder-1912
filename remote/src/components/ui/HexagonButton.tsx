import React from 'react';
import styled from 'styled-components';
import { theme } from '../../styles/theme';

interface HexagonButtonProps {
  scriptName: string;
  color: string;
  friendlyName?: string;
  imageUrl?: string;
  imagePositionX?: number; // -50 to 50
  imagePositionY?: number; // -50 to 50
  imageScale?: number; // 50 to 200
  showName?: boolean;
  onClick: () => void;
  className?: string;
  isEditMode?: boolean;
}

const ButtonContainer = styled.div<{ $isEditMode?: boolean }>`
  position: relative;
  width: ${theme.button.size}px;
  height: ${theme.button.size}px;
  cursor: pointer;
  transition: all ${theme.animations.normal} ${theme.animations.easing};
  
  ${props => props.$isEditMode && `
    &::after {
      content: 'EDIT';
      position: absolute;
      top: -8px;
      right: -8px;
      padding: 4px 8px;
      background: ${theme.colors.primary};
      border: 2px solid ${theme.colors.text};
      border-radius: 4px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 10px;
      font-weight: bold;
      color: ${theme.colors.text};
      z-index: 100;
      animation: editModePulse 1.5s ease-in-out infinite;
    }
    
    @keyframes editModePulse {
      0%, 100% { transform: scale(1); opacity: 0.8; }
      50% { transform: scale(1.1); opacity: 1; }
    }
  `}
  
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
  overflow: visible;
`;

const HexagonPath = styled.path<{ $color: string }>`
  fill: ${theme.colors.surface};
  stroke: ${props => props.$color};
  stroke-width: 16;
  filter: drop-shadow(0 0 2px ${props => props.$color}40);
  transition: all ${theme.animations.normal} ${theme.animations.easing};
  
  ${ButtonContainer}:hover & {
    fill: ${theme.colors.surfaceLight};
    stroke-width: 20;
    filter: 
      drop-shadow(0 0 20px ${props => props.$color}) 
      drop-shadow(0 0 40px ${props => props.$color}80);
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
  transition: all ${theme.animations.fast} ${theme.animations.easing};
  
  ${ButtonContainer}:hover & {
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

const HexagonImage = styled.img<{ $color: string; $positionX: number; $positionY: number; $scale: number }>`
  width: ${props => props.$scale}%;
  height: ${props => props.$scale}%;
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  object-fit: cover;
  object-position: ${props => `${50 - props.$positionX}% ${50 - props.$positionY}%`};
  clip-path: polygon(30% 0%, 70% 0%, 100% 50%, 70% 100%, 30% 100%, 0% 50%);
  filter: drop-shadow(0 0 2px ${props => props.$color}30);
  transition: all ${theme.animations.fast} ${theme.animations.easing};
  
  ${ButtonContainer}:hover & {
    filter: 
      drop-shadow(0 0 15px ${props => props.$color}80)
      drop-shadow(0 0 30px ${props => props.$color}60)
      brightness(1.1);
  }
`;

// Your custom hexagon path from the SVG
const HEXAGON_PATH = "M245.57,681.92c-40.75,0-78.72-21.92-99.1-57.21L15.83,398.42c-20.37-35.29-20.37-79.14,0-114.43L146.48,57.71C166.85,22.42,204.82.5,245.57.5h261.29c40.75,0,78.72,21.92,99.1,57.21l130.65,226.29c20.37,35.29,20.37,79.14,0,114.43l-130.65,226.29c-20.38,35.29-58.35,57.21-99.1,57.21H245.57Z";

export const HexagonButton: React.FC<HexagonButtonProps> = ({
  scriptName,
  color,
  friendlyName,
  imageUrl,
  imagePositionX = 0,
  imagePositionY = 0,
  imageScale = 100,
  showName = false,
  onClick,
  className,
  isEditMode = false
}) => {
  const gradientId = `gradient-${color.replace('#', '')}`;
  const displayName = friendlyName || scriptName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());

  return (
    <ButtonContainer onClick={onClick} className={className} $isEditMode={isEditMode}>
      <HexagonSVG viewBox="-20 -20 792.44 722.42">
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
          <HexagonImage 
            src={imageUrl} 
            alt={displayName} 
            $color={color}
            $positionX={imagePositionX}
            $positionY={imagePositionY}
            $scale={imageScale}
          />
        </ImageContainer>
      ) : (
        <TextContainer $color={color}>
          <ExecuteText>EXECUTE</ExecuteText>
          {showName && (
            <ScriptName>{displayName.toUpperCase()}</ScriptName>
          )}
        </TextContainer>
      )}
    </ButtonContainer>
  );
};