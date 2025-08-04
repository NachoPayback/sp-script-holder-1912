import { useState, useRef, useEffect } from 'react';
import { createPortal } from 'react-dom';
import styled from 'styled-components';
import { theme } from '../../styles/theme';
import { HexagonButton } from './HexagonButton';
import { hubApi } from '../../services/api';
import { useToast } from './ToastContainer';

interface ScriptCustomizationModalProps {
  isOpen: boolean;
  onClose: () => void;
  scriptName: string;
  currentFriendlyName?: string;
  currentImageUrl?: string;
  currentColor?: string;
  currentPositionX?: number;
  currentPositionY?: number;
  currentImageScale?: number;
  onSave: () => void;
}

const ModalOverlay = styled.div<{ $isOpen: boolean }>`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(8px);
  display: ${props => props.$isOpen ? 'flex' : 'none'};
  align-items: center;
  justify-content: center;
  z-index: 999999;
`;

const ModalContainer = styled.div`
  background: ${theme.colors.surface};
  border: 2px solid ${theme.colors.primary};
  border-radius: ${theme.borderRadius.xl};
  padding: ${theme.spacing.xxl};
  max-width: 900px;
  width: 90%;
  max-height: 85vh;
  overflow-y: auto;
  backdrop-filter: blur(20px);
  box-shadow: ${theme.shadows.lg}, ${theme.shadows.glow};
`;

const ModalHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: ${theme.spacing.xl};
`;

const ModalTitle = styled.h2`
  font-size: 1.8rem;
  font-weight: ${theme.fonts.weights.black};
  color: ${theme.colors.primary};
  margin: 0;
  text-transform: uppercase;
  letter-spacing: 0.1em;
`;

const CloseButton = styled.button`
  background: none;
  border: none;
  color: ${theme.colors.textSecondary};
  font-size: 1.5rem;
  cursor: pointer;
  padding: 4px;
  
  &:hover {
    color: ${theme.colors.text};
  }
`;

const ContentLayout = styled.div`
  display: grid;
  grid-template-columns: 1fr 300px;
  gap: ${theme.spacing.xxl};
  
  @media (max-width: ${theme.breakpoints.tablet}) {
    grid-template-columns: 1fr;
  }
`;

const PreviewSection = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: ${theme.spacing.xxl};
  background: rgba(0, 0, 0, 0.3);
  border-radius: ${theme.borderRadius.lg};
  border: 1px solid ${theme.colors.borderLight};
`;

const PreviewTitle = styled.h3`
  color: ${theme.colors.text};
  margin-bottom: ${theme.spacing.lg};
  font-size: 1.2rem;
  font-weight: ${theme.fonts.weights.bold};
`;

const SettingsPanel = styled.div`
  display: flex;
  flex-direction: column;
  gap: ${theme.spacing.lg};
`;

const SettingGroup = styled.div`
  background: rgba(0, 0, 0, 0.2);
  padding: ${theme.spacing.lg};
  border-radius: ${theme.borderRadius.md};
  border: 1px solid ${theme.colors.borderLight};
`;

const SettingLabel = styled.label`
  display: block;
  color: ${theme.colors.text};
  font-weight: ${theme.fonts.weights.semibold};
  margin-bottom: ${theme.spacing.sm};
  font-size: 0.95rem;
`;

const TextInput = styled.input`
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
  padding: ${theme.spacing.md};
  background: ${theme.colors.surface};
  border: 1px solid ${theme.colors.borderLight};
  border-radius: ${theme.borderRadius.sm};
  color: ${theme.colors.text};
  font-family: ${theme.fonts.family};
  font-size: 0.95rem;
  
  &:focus {
    outline: none;
    border-color: ${theme.colors.primary};
    box-shadow: 0 0 0 2px ${theme.colors.primary}20;
  }
`;

const ColorInput = styled.input`
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
  height: 50px;
  padding: 4px;
  background: ${theme.colors.surface};
  border: 1px solid ${theme.colors.borderLight};
  border-radius: ${theme.borderRadius.sm};
  cursor: pointer;
  
  &:focus {
    outline: none;
    border-color: ${theme.colors.primary};
  }
`;

const ImagePositionCanvas = styled.div`
  position: relative;
  width: 200px;
  height: 200px;
  margin: 0 auto;
  background: rgba(0, 0, 0, 0.8);
  border: 2px solid ${theme.colors.borderLight};
  border-radius: ${theme.borderRadius.md};
  display: flex;
  align-items: center;
  justify-content: center;
`;

const HexagonClipContainer = styled.div<{ $positionX: number; $positionY: number }>`
  width: 150px;
  height: 150px;
  position: relative;
  background: ${theme.colors.surface};
  clip-path: polygon(30% 0%, 70% 0%, 100% 50%, 70% 100%, 30% 100%, 0% 50%);
  overflow: hidden;
`;

const PositionedImage = styled.img<{ $positionX: number; $positionY: number; $scale: number }>`
  width: ${props => props.$scale}%;
  height: ${props => props.$scale}%;
  object-fit: cover;
  object-position: ${props => `${50 - props.$positionX}% ${50 - props.$positionY}%`};
  transform: translate(-50%, -50%);
  position: absolute;
  top: 50%;
  left: 50%;
`;

const PositionControls = styled.div`
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  grid-template-rows: 1fr auto 1fr;
  gap: ${theme.spacing.sm};
  margin-top: ${theme.spacing.md};
  max-width: 150px;
  margin-left: auto;
  margin-right: auto;
`;

const PositionButton = styled.button`
  width: 40px;
  height: 40px;
  background: ${theme.colors.surface};
  border: 1px solid ${theme.colors.borderLight};
  border-radius: ${theme.borderRadius.sm};
  color: ${theme.colors.text};
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
  
  &:hover {
    background: ${theme.colors.surfaceLight};
    border-color: ${theme.colors.primary};
  }
  
  &:active {
    transform: scale(0.95);
  }
`;

const ResetButton = styled.button`
  background: ${theme.colors.surface};
  border: 1px solid ${theme.colors.borderLight};
  color: ${theme.colors.textSecondary};
  padding: ${theme.spacing.sm};
  border-radius: ${theme.borderRadius.sm};
  cursor: pointer;
  font-size: 0.8rem;
  
  &:hover {
    background: ${theme.colors.surfaceLight};
    color: ${theme.colors.text};
  }
`;

const ScaleSlider = styled.input`
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
  margin: ${theme.spacing.sm} 0;
  accent-color: ${theme.colors.primary};
`;

const PlaceholderText = styled.div`
  color: ${theme.colors.textSecondary};
  font-size: 0.9rem;
  text-align: center;
  padding: ${theme.spacing.lg};
`;

const ButtonRow = styled.div`
  display: flex;
  gap: ${theme.spacing.md};
  justify-content: flex-end;
  margin-top: ${theme.spacing.xl};
  padding-top: ${theme.spacing.lg};
  border-top: 1px solid ${theme.colors.borderLight};
`;

const Button = styled.button<{ $variant?: 'primary' | 'secondary' }>`
  padding: ${theme.spacing.md} ${theme.spacing.lg};
  border: 2px solid ${props => props.$variant === 'primary' ? theme.colors.primary : theme.colors.borderLight};
  background: ${props => props.$variant === 'primary' ? theme.colors.primary : theme.colors.surface};
  color: ${props => props.$variant === 'primary' ? theme.colors.background : theme.colors.text};
  border-radius: ${theme.borderRadius.md};
  font-family: ${theme.fonts.family};
  font-weight: ${theme.fonts.weights.bold};
  font-size: 0.9rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  cursor: pointer;
  transition: all ${theme.animations.fast} ${theme.animations.easing};
  
  &:hover {
    background: ${props => props.$variant === 'primary' ? theme.colors.primaryLight : theme.colors.surfaceLight};
    transform: translateY(-2px);
  }
  
  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    transform: none;
  }
`;

export const ScriptCustomizationModal: React.FC<ScriptCustomizationModalProps> = ({
  isOpen,
  onClose,
  scriptName,
  currentFriendlyName = '',
  currentImageUrl = '',
  currentColor = theme.colors.primary,
  currentPositionX = 0,
  currentPositionY = 0,
  currentImageScale = 100,
  onSave
}) => {
  const [friendlyName, setFriendlyName] = useState(currentFriendlyName || scriptName);
  const [imageUrl, setImageUrl] = useState(currentImageUrl);
  const [color, setColor] = useState(currentColor);
  const [positionX, setPositionX] = useState(currentPositionX);
  const [positionY, setPositionY] = useState(currentPositionY);
  const [imageScale, setImageScale] = useState(currentImageScale); // Scale percentage
  const [isSaving, setIsSaving] = useState(false);
  const canvasRef = useRef<HTMLDivElement>(null);
  const { showSuccess, showError } = useToast();

  // Reset form when modal opens with new script
  useEffect(() => {
    if (isOpen) {
      setFriendlyName(currentFriendlyName || scriptName);
      setImageUrl(currentImageUrl || '');
      setColor(currentColor || theme.colors.primary);
      setPositionX(currentPositionX || 0);
      setPositionY(currentPositionY || 0);
      setImageScale(currentImageScale || 100);
    }
  }, [isOpen, scriptName, currentFriendlyName, currentImageUrl, currentColor, currentPositionX, currentPositionY, currentImageScale]);

  const adjustPosition = (direction: 'up' | 'down' | 'left' | 'right') => {
    const step = 10;
    switch (direction) {
      case 'up':
        setPositionY(Math.max(-50, positionY - step));
        break;
      case 'down':
        setPositionY(Math.min(50, positionY + step));
        break;
      case 'left':
        setPositionX(Math.max(-50, positionX - step));
        break;
      case 'right':
        setPositionX(Math.min(50, positionX + step));
        break;
    }
  };

  const resetPosition = () => {
    setPositionX(0);
    setPositionY(0);
    setImageScale(100);
  };

  const handleImageUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Check file size (max 2MB)
    if (file.size > 2 * 1024 * 1024) {
      showError('Image too large. Please choose an image under 2MB.');
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      const base64 = e.target?.result as string;
      setImageUrl(base64);
    };
    reader.readAsDataURL(file);
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      console.log('Saving script customization:', {
        scriptName,
        friendlyName,
        imageUrl: imageUrl ? `${imageUrl.substring(0, 50)}...` : 'none',
        color,
        positionX: Math.round(positionX),
        positionY: Math.round(positionY)
      });
      
      const result = await hubApi.saveFriendlyName(
        scriptName,
        friendlyName,
        '', // description
        imageUrl || undefined,
        color,
        Math.round(positionX),
        Math.round(positionY),
        imageScale
      );
      
      console.log('Save result:', result);
      
      if (result.success) {
        showSuccess('Script customization saved successfully');
        onSave(); // This should refresh the friendly names
        onClose();
      } else {
        showError(`Failed to save: ${result.message || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Save error:', error);
      showError(`Save failed: ${error instanceof Error ? error.message : 'Network error'}`);
    } finally {
      setIsSaving(false);
    }
  };

  if (!isOpen) return null;

  return createPortal(
    <ModalOverlay $isOpen={isOpen}>
      <ModalContainer>
        <ModalHeader>
          <ModalTitle>Customize {scriptName}</ModalTitle>
          <CloseButton onClick={onClose}>×</CloseButton>
        </ModalHeader>

        <ContentLayout>
          <PreviewSection>
            <PreviewTitle>Live Preview</PreviewTitle>
            <HexagonButton
              scriptName={scriptName}
              color={color}
              friendlyName={friendlyName}
              imageUrl={imageUrl || undefined}
              imagePositionX={positionX}
              imagePositionY={positionY}
              showName={true}
              onClick={() => {}}
            />
          </PreviewSection>

          <SettingsPanel>
            <SettingGroup>
              <SettingLabel>Friendly Name</SettingLabel>
              <TextInput
                type="text"
                value={friendlyName}
                onChange={(e) => setFriendlyName(e.target.value)}
                placeholder="Enter friendly name..."
              />
            </SettingGroup>

            <SettingGroup>
              <SettingLabel>Button Color</SettingLabel>
              <ColorInput
                type="color"
                value={color}
                onChange={(e) => setColor(e.target.value)}
              />
            </SettingGroup>

            <SettingGroup>
              <SettingLabel>Icon/Image Upload</SettingLabel>
              <input
                type="file"
                accept="image/*"
                onChange={handleImageUpload}
                style={{
                  padding: `${theme.spacing.sm}`,
                  background: theme.colors.surface,
                  border: `1px solid ${theme.colors.borderLight}`,
                  borderRadius: theme.borderRadius.sm,
                  color: theme.colors.text,
                  fontFamily: theme.fonts.family,
                  fontSize: '0.85rem',
                  width: '100%',
                  maxWidth: '100%',
                  boxSizing: 'border-box',
                  cursor: 'pointer'
                }}
              />
              {imageUrl && (
                <div style={{ marginTop: theme.spacing.sm, fontSize: '0.8rem', color: theme.colors.textSecondary }}>
                  Image uploaded: {Math.round(imageUrl.length / 1024)}KB
                </div>
              )}
            </SettingGroup>

            <SettingGroup>
              <SettingLabel>Image Position</SettingLabel>
              <ImagePositionCanvas ref={canvasRef}>
                {imageUrl ? (
                  <HexagonClipContainer $positionX={positionX} $positionY={positionY}>
                    <PositionedImage
                      src={imageUrl}
                      alt="Preview"
                      $positionX={positionX}
                      $positionY={positionY}
                      $scale={imageScale}
                    />
                  </HexagonClipContainer>
                ) : (
                  <PlaceholderText>Upload an image to position it</PlaceholderText>
                )}
              </ImagePositionCanvas>
              {imageUrl && (
                <>
                  <div style={{ marginTop: theme.spacing.md }}>
                    <SettingLabel>Image Scale: {imageScale}%</SettingLabel>
                    <ScaleSlider
                      type="range"
                      min="50"
                      max="200"
                      value={imageScale}
                      onChange={(e) => setImageScale(parseInt(e.target.value))}
                    />
                  </div>
                  <PositionControls>
                    <div></div>
                    <PositionButton onClick={() => adjustPosition('up')}>↑</PositionButton>
                    <div></div>
                    <PositionButton onClick={() => adjustPosition('left')}>←</PositionButton>
                    <ResetButton onClick={resetPosition}>Reset</ResetButton>
                    <PositionButton onClick={() => adjustPosition('right')}>→</PositionButton>
                    <div></div>
                    <PositionButton onClick={() => adjustPosition('down')}>↓</PositionButton>
                    <div></div>
                  </PositionControls>
                </>
              )}
            </SettingGroup>
          </SettingsPanel>
        </ContentLayout>

        <ButtonRow>
          <Button onClick={onClose}>Cancel</Button>
          <Button 
            $variant="primary" 
            onClick={handleSave}
            disabled={isSaving}
          >
            {isSaving ? 'Saving...' : 'Save Changes'}
          </Button>
        </ButtonRow>
      </ModalContainer>
    </ModalOverlay>,
    document.body
  );
};