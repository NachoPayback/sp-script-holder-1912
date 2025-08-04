import { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import styled from 'styled-components';
import { theme } from '../../styles/theme';

interface HubSettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  hubName: string;
  currentMode: 'shared' | 'assigned';
  currentShowNames: boolean;
  onSave: (mode: 'shared' | 'assigned', showNames: boolean, enableTimer: boolean, timerMinutes: number) => void;
  onShuffleScripts: () => void;
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
  max-width: 500px;
  width: 90%;
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
  font-size: 1.6rem;
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

const SettingGroup = styled.div`
  margin-bottom: ${theme.spacing.lg};
  padding: ${theme.spacing.lg};
  background: rgba(0, 0, 0, 0.2);
  border-radius: ${theme.borderRadius.md};
  border: 1px solid ${theme.colors.borderLight};
`;

const SettingLabel = styled.label`
  display: block;
  color: ${theme.colors.text};
  font-weight: ${theme.fonts.weights.semibold};
  margin-bottom: ${theme.spacing.sm};
  font-size: 1rem;
`;

const RadioGroup = styled.div`
  display: flex;
  gap: ${theme.spacing.md};
  margin-bottom: ${theme.spacing.md};
`;

const RadioLabel = styled.label`
  display: flex;
  align-items: center;
  gap: ${theme.spacing.sm};
  color: ${theme.colors.textSecondary};
  cursor: pointer;
  font-size: 0.9rem;
  
  &:hover {
    color: ${theme.colors.text};
  }
`;

const RadioInput = styled.input`
  margin: 0;
  accent-color: ${theme.colors.primary};
`;

const CheckboxLabel = styled.label`
  display: flex;
  align-items: center;
  gap: ${theme.spacing.sm};
  color: ${theme.colors.textSecondary};
  cursor: pointer;
  font-size: 0.9rem;
  
  &:hover {
    color: ${theme.colors.text};
  }
`;

const CheckboxInput = styled.input`
  margin: 0;
  accent-color: ${theme.colors.primary};
  transform: scale(1.2);
`;

const NumberInput = styled.input`
  width: 80px;
  padding: ${theme.spacing.sm};
  background: ${theme.colors.surface};
  border: 1px solid ${theme.colors.borderLight};
  border-radius: ${theme.borderRadius.sm};
  color: ${theme.colors.text};
  font-family: ${theme.fonts.family};
  
  &:focus {
    outline: none;
    border-color: ${theme.colors.primary};
  }
`;

const ActionButton = styled.button`
  width: 100%;
  padding: ${theme.spacing.md};
  background: rgba(239, 68, 68, 0.2);
  border: 1px solid #ef4444;
  color: #ef4444;
  border-radius: ${theme.borderRadius.md};
  font-family: ${theme.fonts.family};
  font-weight: ${theme.fonts.weights.bold};
  text-transform: uppercase;
  cursor: pointer;
  transition: all ${theme.animations.fast} ${theme.animations.easing};
  
  &:hover {
    background: rgba(239, 68, 68, 0.3);
    transform: translateY(-2px);
  }
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
`;

export const HubSettingsModal: React.FC<HubSettingsModalProps> = ({
  isOpen,
  onClose,
  hubName,
  currentMode,
  currentShowNames,
  onSave,
  onShuffleScripts
}) => {
  const [mode, setMode] = useState<'shared' | 'assigned'>(currentMode);
  const [showNames, setShowNames] = useState(currentShowNames);
  const [enableTimer, setEnableTimer] = useState(false);
  const [timerMinutes, setTimerMinutes] = useState(5);

  useEffect(() => {
    if (isOpen) {
      setMode(currentMode);
      setShowNames(currentShowNames);
    }
  }, [isOpen, currentMode, currentShowNames]);

  const handleSave = () => {
    onSave(mode, showNames, enableTimer, timerMinutes);
    onClose();
  };

  if (!isOpen) return null;

  return createPortal(
    <ModalOverlay $isOpen={isOpen}>
      <ModalContainer>
        <ModalHeader>
          <ModalTitle>{hubName} Settings</ModalTitle>
          <CloseButton onClick={onClose}>×</CloseButton>
        </ModalHeader>

        <SettingGroup>
          <SettingLabel>Hub Mode</SettingLabel>
          <RadioGroup>
            <RadioLabel>
              <RadioInput
                type="radio"
                name="mode"
                value="shared"
                checked={mode === 'shared'}
                onChange={(e) => setMode(e.target.value as 'shared')}
              />
              Shared - All scripts visible
            </RadioLabel>
            <RadioLabel>
              <RadioInput
                type="radio"
                name="mode"
                value="assigned"
                checked={mode === 'assigned'}
                onChange={(e) => setMode(e.target.value as 'assigned')}
              />
              Assigned - One button per user
            </RadioLabel>
          </RadioGroup>
        </SettingGroup>

        <SettingGroup>
          <SettingLabel>Display Options</SettingLabel>
          <CheckboxLabel>
            <CheckboxInput
              type="checkbox"
              checked={showNames}
              onChange={(e) => setShowNames(e.target.checked)}
            />
            Show script names on buttons
          </CheckboxLabel>
        </SettingGroup>

        <SettingGroup>
          <SettingLabel>Auto-Shuffle Timer</SettingLabel>
          <CheckboxLabel>
            <CheckboxInput
              type="checkbox"
              checked={enableTimer}
              onChange={(e) => setEnableTimer(e.target.checked)}
            />
            Enable auto-shuffle every
            <NumberInput
              type="number"
              min="1"
              max="60"
              value={timerMinutes}
              onChange={(e) => setTimerMinutes(parseInt(e.target.value) || 5)}
              disabled={!enableTimer}
            />
            minutes
          </CheckboxLabel>
        </SettingGroup>

        {mode === 'assigned' && (
          <SettingGroup>
            <SettingLabel>Assignment Actions</SettingLabel>
            <ActionButton onClick={onShuffleScripts}>
              🔀 Shuffle Script Assignments
            </ActionButton>
          </SettingGroup>
        )}

        <ButtonRow>
          <Button onClick={onClose}>Cancel</Button>
          <Button $variant="primary" onClick={handleSave}>
            Save Settings
          </Button>
        </ButtonRow>
      </ModalContainer>
    </ModalOverlay>,
    document.body
  );
};