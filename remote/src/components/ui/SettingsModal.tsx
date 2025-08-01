import { useState, useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';
import styled from 'styled-components';
import { theme } from '../../styles/theme';
import { isCurrentUserAdmin } from '../../utils/admin';
import type { HubScript } from '../../types/Hub';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  scripts: HubScript[];
  friendlyNames: Record<string, { friendly_name: string; image_url?: string; custom_color?: string; position_x?: number; position_y?: number }>;
  hubMode: 'shared' | 'assigned';
  showScriptNames: boolean;
  onFriendlyNamesUpdate: () => void;
  onHubSettingsUpdate: (mode: 'shared' | 'assigned', showNames: boolean, enableTimer: boolean, timerMinutes: number) => void;
  onShuffleScripts: () => void;
  selectedScript?: string | null;
}

const ModalOverlay = styled.div<{ $isOpen: boolean }>`
  position: fixed !important;
  top: 0 !important;
  left: 0 !important;
  right: 0 !important;
  bottom: 0 !important;
  width: 100vw !important;
  height: 100vh !important;
  background: rgba(0, 0, 0, 0.8) !important;
  backdrop-filter: blur(8px);
  display: ${props => props.$isOpen ? 'flex' : 'none'} !important;
  align-items: center !important;
  justify-content: center !important;
  z-index: 999999 !important;
  pointer-events: ${props => props.$isOpen ? 'auto' : 'none'} !important;
`;

const ModalContainer = styled.div`
  background: ${theme.colors.surface} !important;
  border: 2px solid ${theme.colors.primary} !important;
  border-radius: ${theme.borderRadius.xl} !important;
  padding: ${theme.spacing.xxl} !important;
  max-width: 650px !important;
  width: 90% !important;
  max-height: 80vh !important;
  overflow-y: auto !important;
  backdrop-filter: blur(20px) !important;
  box-shadow: ${theme.shadows.lg}, ${theme.shadows.glow} !important;
  position: relative !important;
  margin: 0 !important;
  transform: none !important;
  z-index: 1000000 !important;
  
  /* Force centered modal on all screen sizes */
  @media (max-width: ${theme.breakpoints.mobile}) {
    width: 95% !important;
    max-height: 90vh !important;
  }
`;

const ModalHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
`;

const ModalTitle = styled.h2`
  font-size: 1.8rem;
  font-weight: ${theme.fonts.weights.black};
  color: ${theme.colors.primary};
  margin: 0;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  text-shadow: 0 0 10px currentColor;
`;

const CloseButton = styled.button`
  background: none;
  border: none;
  color: #94a3b8;
  font-size: 1.5rem;
  cursor: pointer;
  padding: 4px;
  
  &:hover {
    color: #f1f5f9;
  }
`;

const TabContainer = styled.div`
  display: flex;
  margin-bottom: 24px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.2);
`;

const Tab = styled.button<{ $active: boolean }>`
  background: ${props => props.$active ? theme.colors.surfaceLight : 'transparent'};
  border: none;
  color: ${props => props.$active ? theme.colors.primary : theme.colors.textSecondary};
  padding: ${theme.spacing.md} ${theme.spacing.lg};
  cursor: pointer;
  font-family: ${theme.fonts.family};
  font-weight: ${theme.fonts.weights.bold};
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-bottom: 2px solid ${props => props.$active ? theme.colors.primary : 'transparent'};
  transition: all ${theme.animations.fast} ${theme.animations.easing};
  position: relative;
  
  ${props => props.$active && `
    &::before {
      content: '';
      position: absolute;
      top: 50%;
      left: 8px;
      width: 4px;
      height: 60%;
      background: ${theme.gradients.electric};
      transform: translateY(-50%);
      border-radius: 2px;
    }
  `}
  
  &:hover {
    color: ${theme.colors.primary};
    background: ${theme.colors.surfaceHover};
  }
`;

const SettingSection = styled.div`
  margin-bottom: 24px;
`;

const SettingLabel = styled.label`
  display: block;
  color: #f1f5f9;
  font-weight: 600;
  margin-bottom: 8px;
`;

const RadioGroup = styled.div`
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
`;

const RadioLabel = styled.label`
  display: flex;
  align-items: center;
  gap: 8px;
  color: #e2e8f0;
  cursor: pointer;
  
  input[type="radio"] {
    accent-color: #60a5fa;
  }
`;

const CheckboxLabel = styled.label`
  display: flex;
  align-items: center;
  gap: 8px;
  color: #e2e8f0;
  cursor: pointer;
  margin-bottom: 16px;
  
  input[type="checkbox"] {
    accent-color: #60a5fa;
  }
`;

const NumberInput = styled.input`
  background: rgba(30, 41, 59, 0.5);
  border: 1px solid rgba(148, 163, 184, 0.2);
  color: #e2e8f0;
  padding: 8px 12px;
  border-radius: 6px;
  width: 80px;
  font-family: inherit;
  
  &:focus {
    outline: none;
    border-color: rgba(59, 130, 246, 0.5);
  }
`;

const ButtonGroup = styled.div`
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  margin-top: 24px;
`;

const ActionButton = styled.button<{ $variant?: 'primary' | 'danger' | 'secondary' }>`
  padding: ${theme.spacing.md} ${theme.spacing.lg};
  border: 2px solid transparent;
  border-radius: ${theme.borderRadius.md};
  cursor: pointer;
  font-family: ${theme.fonts.family};
  font-weight: ${theme.fonts.weights.bold};
  text-transform: uppercase;
  letter-spacing: 0.05em;
  transition: all ${theme.animations.fast} ${theme.animations.easing};
  position: relative;
  overflow: hidden;
  
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    transition: left ${theme.animations.normal} ${theme.animations.easing};
    z-index: -1;
  }
  
  ${props => props.$variant === 'primary' && `
    background: ${theme.colors.primary};
    color: ${theme.colors.text};
    border-color: ${theme.colors.primary};
    box-shadow: ${theme.shadows.glow};
    
    &::before {
      background: ${theme.gradients.electric};
    }
    
    &:hover {
      background: ${theme.colors.primaryLight};
      transform: translateY(-2px);
      box-shadow: ${theme.shadows.glowStrong};
      
      &::before {
        left: 0;
      }
    }
  `}
  
  ${props => props.$variant === 'danger' && `
    background: ${theme.colors.error};
    color: ${theme.colors.text};
    border-color: ${theme.colors.error};
    
    &:hover {
      background: #dc2626;
      transform: translateY(-2px);
    }
  `}
  
  ${props => (!props.$variant || props.$variant === 'secondary') && `
    background: ${theme.colors.surface};
    border-color: ${theme.colors.border};
    color: ${theme.colors.textSecondary};
    
    &::before {
      background: ${theme.gradients.electric};
    }
    
    &:hover {
      background: ${theme.colors.surfaceLight};
      border-color: ${theme.colors.primary};
      color: ${theme.colors.primary};
      
      &::before {
        left: 0;
      }
    }
  `}
`;

const RefreshButton = styled.button`
  background: rgba(59, 130, 246, 0.2);
  border: 1px solid rgba(59, 130, 246, 0.3);
  color: #60a5fa;
  padding: 8px 16px;
  border-radius: 8px;
  cursor: pointer;
  font-family: inherit;
  font-weight: 600;
  margin-bottom: 20px;
  transition: all 0.2s ease;
  
  &:hover {
    background: rgba(59, 130, 246, 0.3);
    border-color: rgba(59, 130, 246, 0.5);
  }
`;

const ScriptItem = styled.div`
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px;
  margin: 6px 0;
  background: rgba(30, 41, 59, 0.3);
  border: 1px solid rgba(148, 163, 184, 0.2);
  border-radius: 8px;
`;

const ScriptInfo = styled.div`
  flex: 1;
  min-width: 0;
`;

const ScriptName = styled.div`
  font-weight: 600;
  color: #3b82f6;
  margin-bottom: 4px;
`;

const AutoName = styled.div`
  font-size: 0.75rem;
  color: #94a3b8;
`;

const FriendlyInput = styled.input`
  flex: 1;
  padding: 8px 12px;
  background: rgba(30, 41, 59, 0.5);
  border: 1px solid rgba(148, 163, 184, 0.2);
  color: #e2e8f0;
  border-radius: 6px;
  font-family: inherit;
  
  &::placeholder {
    color: #64748b;
  }
  
  &:focus {
    outline: none;
    border-color: rgba(59, 130, 246, 0.5);
  }
`;

const SaveButton = styled.button`
  padding: 8px 12px;
  background: #10b981;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-family: inherit;
  font-weight: 600;
  transition: background 0.2s ease;
  
  &:hover {
    background: #059669;
  }
  
  &:disabled {
    background: #6b7280;
    cursor: not-allowed;
  }
`;

const DeleteButton = styled.button`
  padding: 8px 12px;
  background: #ef4444;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-family: inherit;
  font-weight: 600;
  transition: background 0.2s ease;
  
  &:hover {
    background: #dc2626;
  }
`;

const EmptyState = styled.div`
  text-align: center;
  color: #94a3b8;
  padding: 32px;
  font-size: 1.1rem;
`;

const ImageDropZone = styled.div<{ $isDragging: boolean }>`
  border: 2px dashed ${props => props.$isDragging ? theme.colors.primary : theme.colors.borderLight};
  border-radius: ${theme.borderRadius.md};
  padding: ${theme.spacing.md};
  margin: ${theme.spacing.xs} 0;
  text-align: center;
  cursor: pointer;
  transition: all ${theme.animations.fast} ${theme.animations.easing};
  background: ${props => props.$isDragging ? theme.colors.primary + '10' : 'transparent'};
  
  &:hover {
    border-color: ${theme.colors.primary};
    background: ${theme.colors.primary}05;
  }
  
  p {
    margin: 0;
    color: ${theme.colors.textSecondary};
    font-size: 0.8rem;
    line-height: 1.2;
  }
  
  .upload-icon {
    font-size: 1.5rem;
    margin-bottom: ${theme.spacing.xs};
    opacity: 0.6;
  }
`;

const HiddenFileInput = styled.input`
  display: none;
`;

const ColorInput = styled.input`
  width: 40px;
  height: 40px;
  border: 2px solid ${theme.colors.borderLight};
  border-radius: ${theme.borderRadius.md};
  cursor: pointer;
  background: transparent;
  
  &::-webkit-color-swatch-wrapper {
    padding: 0;
  }
  
  &::-webkit-color-swatch {
    border: none;
    border-radius: ${theme.borderRadius.sm};
  }
  
  &:hover {
    border-color: ${theme.colors.primary};
  }
`;

const PositionSlider = styled.input`
  width: 100px;
  height: 4px;
  border-radius: 2px;
  background: ${theme.colors.surface};
  outline: none;
  cursor: pointer;
  
  &::-webkit-slider-thumb {
    appearance: none;
    width: 16px;
    height: 16px;
    border-radius: 50%;
    background: ${theme.colors.primary};
    cursor: pointer;
    border: 2px solid ${theme.colors.text};
  }
  
  &::-moz-range-thumb {
    width: 16px;
    height: 16px;
    border-radius: 50%;
    background: ${theme.colors.primary};
    cursor: pointer;
    border: 2px solid ${theme.colors.text};
  }
`;

const SliderGroup = styled.div`
  display: flex;
  flex-direction: column;
  gap: 4px;
  align-items: center;
`;

const SliderLabel = styled.span`
  font-size: 0.7rem;
  color: ${theme.colors.textSecondary};
  text-align: center;
`;

const PreviewContainer = styled.div`
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: rgba(20, 20, 20, 0.5);
  border-radius: ${theme.borderRadius.md};
  border: 1px solid ${theme.colors.borderLight};
`;

const PreviewButton = styled.div<{ $color: string }>`
  position: relative;
  width: 80px;
  height: 80px;
  cursor: default;
`;

const PreviewHexagonSVG = styled.svg<{ $color: string }>`
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  
  path {
    fill: ${theme.colors.surface};
    stroke: ${props => props.$color};
    stroke-width: 6;
    filter: drop-shadow(0 0 8px ${props => props.$color}60);
  }
`;

const PreviewImage = styled.img<{ $color: string; $positionX: number; $positionY: number }>`
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: ${props => `${50 + props.$positionX}% ${50 + props.$positionY}%`};
  clip-path: polygon(30% 0%, 70% 0%, 100% 50%, 70% 100%, 30% 100%, 0% 50%);
  filter: 
    drop-shadow(0 0 4px ${props => props.$color}60)
    drop-shadow(0 0 8px ${props => props.$color}40);
`;

const PreviewText = styled.div`
  font-size: 0.8rem;
  color: ${theme.colors.textSecondary};
  line-height: 1.3;
`;

export function SettingsModal({ 
  isOpen, 
  onClose, 
  scripts, 
  friendlyNames,
  hubMode,
  showScriptNames,
  onFriendlyNamesUpdate,
  onHubSettingsUpdate,
  onShuffleScripts,
  selectedScript
}: SettingsModalProps) {
  const [activeTab, setActiveTab] = useState<'hub' | 'names'>('hub');
  const [inputValues, setInputValues] = useState<Record<string, string>>({});
  const [imageValues, setImageValues] = useState<Record<string, string>>({});
  const [colorValues, setColorValues] = useState<Record<string, string>>({});
  const [positionXValues, setPositionXValues] = useState<Record<string, number>>({});
  const [positionYValues, setPositionYValues] = useState<Record<string, number>>({});
  const [saving, setSaving] = useState<Record<string, boolean>>({});
  const [tempMode, setTempMode] = useState<'shared' | 'assigned'>(hubMode);
  const [tempShowNames, setTempShowNames] = useState(showScriptNames);
  const [tempEnableTimer, setTempEnableTimer] = useState(false);
  const [tempTimerMinutes, setTempTimerMinutes] = useState(5);
  const [draggedScript, setDraggedScript] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRefs = useRef<Record<string, HTMLInputElement | null>>({});
  
  // Check if current user is admin
  const isAdmin = isCurrentUserAdmin();

  // Initialize values when modal opens
  useEffect(() => {
    if (isOpen) {
      // Initialize script name input values
      const values: Record<string, string> = {};
      const images: Record<string, string> = {};
      const colors: Record<string, string> = {};
      const positionsX: Record<string, number> = {};
      const positionsY: Record<string, number> = {};
      scripts.forEach(script => {
        const scriptName = typeof script === 'string' ? script : script.script_name;
        values[scriptName] = friendlyNames[scriptName]?.friendly_name || '';
        images[scriptName] = friendlyNames[scriptName]?.image_url || '';
        colors[scriptName] = friendlyNames[scriptName]?.custom_color || '';
        positionsX[scriptName] = friendlyNames[scriptName]?.position_x || 0;
        positionsY[scriptName] = friendlyNames[scriptName]?.position_y || 0;
      });
      setInputValues(values);
      setImageValues(images);
      setColorValues(colors);
      setPositionXValues(positionsX);
      setPositionYValues(positionsY);
      
      // Initialize hub settings
      setTempMode(hubMode);
      setTempShowNames(showScriptNames);
      
      // If a specific script is selected (edit mode), go directly to names tab
      if (selectedScript) {
        setActiveTab('names');
      } else {
        setActiveTab(isAdmin ? 'hub' : 'names'); // Default to hub settings for admin, names for non-admin
      }
    }
  }, [isOpen, scripts, friendlyNames, hubMode, showScriptNames, isAdmin]);

  const handleInputChange = (scriptName: string, value: string) => {
    setInputValues(prev => ({
      ...prev,
      [scriptName]: value
    }));
  };

  const handleImageChange = (scriptName: string, value: string) => {
    setImageValues(prev => ({
      ...prev,
      [scriptName]: value
    }));
  };

  const handleColorChange = (scriptName: string, value: string) => {
    setColorValues(prev => ({
      ...prev,
      [scriptName]: value
    }));
  };

  const convertToBase64 = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = () => resolve(reader.result as string);
      reader.onerror = error => reject(error);
    });
  };

  const handleImageUpload = async (scriptName: string, file: File) => {
    if (!file.type.startsWith('image/')) {
      alert('Please select an image file');
      return;
    }

    if (file.size > 2 * 1024 * 1024) { // 2MB limit
      alert('Image size must be less than 2MB');
      return;
    }

    try {
      const base64 = await convertToBase64(file);
      handleImageChange(scriptName, base64);
    } catch (error) {
      console.error('Error converting image:', error);
      alert('Failed to process image');
    }
  };

  const handleDragOver = (e: React.DragEvent, scriptName: string) => {
    e.preventDefault();
    setDraggedScript(scriptName);
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    setDraggedScript(null);
  };

  const handleDrop = async (e: React.DragEvent, scriptName: string) => {
    e.preventDefault();
    setIsDragging(false);
    setDraggedScript(null);

    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      await handleImageUpload(scriptName, files[0]);
    }
  };

  const handleFileSelect = async (scriptName: string, e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      await handleImageUpload(scriptName, files[0]);
    }
  };

  const handleSave = async (scriptName: string) => {
    const friendlyName = inputValues[scriptName]?.trim();
    const imageUrl = imageValues[scriptName]?.trim();
    const customColor = colorValues[scriptName]?.trim();
    const positionX = positionXValues[scriptName] || 0;
    const positionY = positionYValues[scriptName] || 0;
    
    if (!friendlyName && !imageUrl && !customColor && positionX === 0 && positionY === 0) {
      // Need at least one value
      return;
    }

    setSaving(prev => ({ ...prev, [scriptName]: true }));

    try {
      const response = await fetch('/api/script-friendly-names', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          script_name: scriptName,
          friendly_name: friendlyName || scriptName, // Fallback to script name if empty
          image_url: imageUrl || null,
          custom_color: customColor || null,
          position_x: positionX,
          position_y: positionY
        })
      });

      const data = await response.json();

      if (data.success) {
        await onFriendlyNamesUpdate();
        // Force update of the input values to reflect the save
        setInputValues(prev => ({
          ...prev,
          [scriptName]: friendlyName || scriptName
        }));
        setImageValues(prev => ({
          ...prev,
          [scriptName]: imageUrl || ''
        }));
        setColorValues(prev => ({
          ...prev,
          [scriptName]: customColor || ''
        }));
        setPositionXValues(prev => ({
          ...prev,
          [scriptName]: positionX
        }));
        setPositionYValues(prev => ({
          ...prev,
          [scriptName]: positionY
        }));
        // Show success feedback
        console.log(`✅ Saved settings for ${scriptName}: name="${friendlyName}" image="${imageUrl}"`);
      }
    } catch (error) {
      console.error('Failed to save script settings:', error);
    } finally {
      setSaving(prev => ({ ...prev, [scriptName]: false }));
    }
  };

  const handleDelete = async (scriptName: string) => {
    setSaving(prev => ({ ...prev, [scriptName]: true }));

    try {
      const response = await fetch('/api/script-friendly-names', {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ script_name: scriptName })
      });

      const data = await response.json();

      if (data.success) {
        setInputValues(prev => ({ ...prev, [scriptName]: '' }));
        setImageValues(prev => ({ ...prev, [scriptName]: '' }));
        setColorValues(prev => ({ ...prev, [scriptName]: '' }));
        setPositionXValues(prev => ({ ...prev, [scriptName]: 0 }));
        setPositionYValues(prev => ({ ...prev, [scriptName]: 0 }));
        onFriendlyNamesUpdate();
      }
    } catch (error) {
      console.error('Failed to delete friendly name:', error);
    } finally {
      setSaving(prev => ({ ...prev, [scriptName]: false }));
    }
  };

  const handleSaveHubSettings = () => {
    onHubSettingsUpdate(tempMode, tempShowNames, tempEnableTimer, tempTimerMinutes);
    onClose();
  };

  const handleShuffle = () => {
    onShuffleScripts();
  };

  const getAutoName = (scriptName: string) => {
    return scriptName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  if (!isOpen) return null;

  return createPortal(
    <ModalOverlay $isOpen={isOpen} onClick={onClose}>
      <ModalContainer onClick={e => e.stopPropagation()}>
        <ModalHeader>
          <ModalTitle>HUB CONFIGURATION</ModalTitle>
          <CloseButton onClick={onClose}>×</CloseButton>
        </ModalHeader>

        {/* Tabs - only show if admin */}
        {isAdmin && (
          <TabContainer>
            <Tab $active={activeTab === 'hub'} onClick={() => setActiveTab('hub')}>
              Hub Settings
            </Tab>
            <Tab $active={activeTab === 'names'} onClick={() => setActiveTab('names')}>
              Script Names
            </Tab>
          </TabContainer>
        )}

        {/* Hub Settings Tab - admin only */}
        {(isAdmin && activeTab === 'hub') && (
          <>
            <SettingSection>
              <SettingLabel>MODE:</SettingLabel>
              <RadioGroup>
                <RadioLabel>
                  <input 
                    type="radio" 
                    name="mode" 
                    value="assigned" 
                    checked={tempMode === 'assigned'}
                    onChange={e => setTempMode(e.target.value as 'assigned' | 'shared')}
                  />
                  1 BUTTON
                </RadioLabel>
                <RadioLabel>
                  <input 
                    type="radio" 
                    name="mode" 
                    value="shared" 
                    checked={tempMode === 'shared'}
                    onChange={e => setTempMode(e.target.value as 'assigned' | 'shared')}
                  />
                  ALL BUTTONS
                </RadioLabel>
              </RadioGroup>
            </SettingSection>

            {tempMode === 'assigned' && (
              <>
                <SettingSection>
                  <CheckboxLabel>
                    <input 
                      type="checkbox" 
                      checked={tempShowNames}
                      onChange={e => setTempShowNames(e.target.checked)}
                    />
                    Show Script Names
                  </CheckboxLabel>
                </SettingSection>

                <SettingSection>
                  <CheckboxLabel>
                    <input 
                      type="checkbox" 
                      checked={tempEnableTimer}
                      onChange={e => setTempEnableTimer(e.target.checked)}
                    />
                    Enable Timer
                  </CheckboxLabel>
                  {tempEnableTimer && (
                    <div style={{ marginTop: '12px' }}>
                      <SettingLabel>TIMER (MINUTES):</SettingLabel>
                      <NumberInput
                        type="number"
                        min="1"
                        max="60"
                        value={tempTimerMinutes}
                        onChange={e => setTempTimerMinutes(parseInt(e.target.value) || 5)}
                      />
                    </div>
                  )}
                </SettingSection>
              </>
            )}

            <ButtonGroup>
              <ActionButton onClick={onClose}>CLOSE</ActionButton>
              <ActionButton $variant="primary" onClick={handleSaveHubSettings}>
                SAVE SETTINGS
              </ActionButton>
              {tempMode === 'assigned' && (
                <ActionButton $variant="secondary" onClick={handleShuffle}>
                  SHUFFLE BUTTONS
                </ActionButton>
              )}
            </ButtonGroup>
          </>
        )}

        {/* Script Names Tab - available to all but restricted based on admin status */}
        {((isAdmin && activeTab === 'names') || !isAdmin) && (
          <>
            {!isAdmin && !selectedScript && (
              <div style={{ marginBottom: '16px', padding: '12px', background: 'rgba(59, 130, 246, 0.1)', borderRadius: '8px', color: '#94a3b8' }}>
                <strong>Note:</strong> Only administrators can modify hub settings. You can view script names here.
              </div>
            )}
            
            {selectedScript && (
              <div style={{ 
                marginBottom: '16px', 
                padding: '12px', 
                background: theme.colors.primary + '20', 
                borderRadius: '8px', 
                border: `1px solid ${theme.colors.primary}40`,
                color: theme.colors.primary 
              }}>
                <strong>🎨 Editing: {selectedScript}</strong><br />
                <span style={{ fontSize: '0.85rem', opacity: 0.8 }}>Make your changes below and click SAVE to apply them.</span>
              </div>
            )}
            
            <RefreshButton onClick={onFriendlyNamesUpdate}>
              🔄 Refresh Script Names
            </RefreshButton>
            
            {isAdmin && (
              <div style={{ 
                marginBottom: '16px', 
                padding: '12px', 
                background: theme.colors.surfaceLight, 
                borderRadius: '8px', 
                border: `1px solid ${theme.colors.borderLight}`,
                color: theme.colors.textSecondary 
              }}>
                <strong style={{ color: theme.colors.primary }}>🚀 Ultra-Easy Image Upload:</strong>
                <br />• Just <strong>drag & drop</strong> your image onto the upload zone below
                <br />• Or <strong>click</strong> the upload zone to select a file
                <br />• Recommended size: 400x400px for best hexagon fit
                <br />• Images completely replace button text when set
                <br />• <em>No URLs needed - works instantly!</em>
              </div>
            )}

            {scripts.length === 0 ? (
              <EmptyState>No scripts found</EmptyState>
            ) : (
              scripts
                .filter(script => {
                  // If a specific script is selected, only show that one
                  if (selectedScript) {
                    const scriptName = typeof script === 'string' ? script : script.script_name;
                    return scriptName === selectedScript;
                  }
                  return true;
                })
                .map(script => {
                const scriptName = typeof script === 'string' ? script : script.script_name;
                const currentFriendlyName = friendlyNames[scriptName]?.friendly_name || '';
                const isSaving = saving[scriptName];
                const isHighlighted = selectedScript === scriptName;
                
                return (
                  <ScriptItem key={scriptName} style={{
                    ...(isHighlighted && {
                      border: `2px solid ${theme.colors.primary}`,
                      background: theme.colors.primary + '10',
                      boxShadow: `0 0 20px ${theme.colors.primary}40`
                    })
                  }}>
                    <ScriptInfo>
                      <ScriptName style={{
                        ...(isHighlighted && { color: theme.colors.primary })
                      }}>{scriptName}</ScriptName>
                      <AutoName>Auto: {getAutoName(scriptName)}</AutoName>
                      {friendlyNames[scriptName]?.image_url && (
                        <div style={{ fontSize: '0.7rem', color: '#10b981', marginTop: '4px' }}>
                          🖼️ Has custom image
                        </div>
                      )}
                    </ScriptInfo>
                    {isAdmin ? (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', flex: '1' }}>
                        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                          <FriendlyInput
                            type="text"
                            value={inputValues[scriptName] || ''}
                            onChange={e => handleInputChange(scriptName, e.target.value)}
                            placeholder="Custom friendly name..."
                            disabled={isSaving}
                            style={{ flex: 1 }}
                          />
                          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '4px' }}>
                            <ColorInput
                              type="color"
                              value={colorValues[scriptName] || '#0080FF'}
                              onChange={e => handleColorChange(scriptName, e.target.value)}
                              disabled={isSaving}
                              title="Custom button color"
                            />
                            <span style={{ fontSize: '0.7rem', color: theme.colors.textSecondary }}>Color</span>
                          </div>
                        </div>
                        {imageValues[scriptName] && (
                          <div style={{ display: 'flex', gap: '12px', alignItems: 'center', marginTop: '8px' }}>
                            <SliderGroup>
                              <PositionSlider
                                type="range"
                                min="-50"
                                max="50"
                                value={positionXValues[scriptName] || 0}
                                onChange={e => setPositionXValues(prev => ({ ...prev, [scriptName]: parseInt(e.target.value) }))}
                                disabled={isSaving}
                              />
                              <SliderLabel>X Position</SliderLabel>
                            </SliderGroup>
                            <SliderGroup>
                              <PositionSlider
                                type="range"
                                min="-50"
                                max="50"
                                value={positionYValues[scriptName] || 0}
                                onChange={e => setPositionYValues(prev => ({ ...prev, [scriptName]: parseInt(e.target.value) }))}
                                disabled={isSaving}
                              />
                              <SliderLabel>Y Position</SliderLabel>
                            </SliderGroup>
                          </div>
                        )}
                        <ImageDropZone
                          $isDragging={isDragging && draggedScript === scriptName}
                          onDragOver={e => handleDragOver(e, scriptName)}
                          onDragLeave={handleDragLeave}
                          onDrop={e => handleDrop(e, scriptName)}
                          onClick={() => fileInputRefs.current[scriptName]?.click()}
                        >
                          <div className="upload-icon">📸</div>
                          <p>
                            {imageValues[scriptName] ? 'Click or drag to replace image' : 'Drag & drop image here or click to select'}
                          </p>
                          <p style={{ fontSize: '0.75rem', opacity: 0.7 }}>
                            Max 2MB • PNG, JPG, GIF, WebP
                          </p>
                        </ImageDropZone>
                        <HiddenFileInput
                          ref={el => {
                            fileInputRefs.current[scriptName] = el;
                          }}
                          type="file"
                          accept=".png,.jpg,.jpeg,.gif,.webp,image/*"
                          onChange={e => handleFileSelect(scriptName, e)}
                        />
                        {imageValues[scriptName] && (
                          <PreviewContainer>
                            <PreviewButton $color={colorValues[scriptName] || '#0080FF'}>
                              <PreviewHexagonSVG 
                                $color={colorValues[scriptName] || '#0080FF'}
                                viewBox="-20 -20 792.44 722.42"
                              >
                                <path d="M245.57,681.92c-40.75,0-78.72-21.92-99.1-57.21L15.83,398.42c-20.37-35.29-20.37-79.14,0-114.43L146.48,57.71C166.85,22.42,204.82.5,245.57.5h261.29c40.75,0,78.72,21.92,99.1,57.21l130.65,226.29c20.37,35.29,20.37,79.14,0,114.43l-130.65,226.29c-20.38,35.29-58.35,57.21-99.1,57.21H245.57Z" />
                              </PreviewHexagonSVG>
                              <PreviewImage 
                                src={imageValues[scriptName]} 
                                alt="Preview"
                                $color={colorValues[scriptName] || '#0080FF'}
                                $positionX={positionXValues[scriptName] || 0}
                                $positionY={positionYValues[scriptName] || 0}
                                onError={e => {
                                  e.currentTarget.style.display = 'none';
                                }}
                              />
                            </PreviewButton>
                            <PreviewText>
                              <strong>Live Preview</strong><br />
                              This is exactly how your button will look.<br />
                              Adjust sliders to reposition the image.
                            </PreviewText>
                          </PreviewContainer>
                        )}
                        <div style={{ display: 'flex', gap: '8px' }}>
                          <SaveButton 
                            onClick={() => handleSave(scriptName)}
                            disabled={isSaving || (!inputValues[scriptName]?.trim() && !imageValues[scriptName]?.trim() && !colorValues[scriptName]?.trim())}
                          >
                            {isSaving ? '...' : 'SAVE'}
                          </SaveButton>
                          {(currentFriendlyName || friendlyNames[scriptName]?.image_url) && (
                            <DeleteButton 
                              onClick={(e) => {
                                e.preventDefault();
                                e.stopPropagation();
                                handleDelete(scriptName);
                              }}
                              disabled={isSaving}
                            >
                              DELETE
                            </DeleteButton>
                          )}
                        </div>
                      </div>
                    ) : (
                      <div style={{ color: '#94a3b8', fontStyle: 'italic' }}>
                        {currentFriendlyName || 'No custom name set'}
                        {friendlyNames[scriptName]?.image_url && (
                          <div style={{ fontSize: '0.8rem', color: '#10b981' }}>🖼️ Custom image</div>
                        )}
                      </div>
                    )}
                  </ScriptItem>
                );
              })
            )}

            {!isAdmin && (
              <ButtonGroup>
                <ActionButton onClick={onClose}>CLOSE</ActionButton>
              </ButtonGroup>
            )}
          </>
        )}
      </ModalContainer>
    </ModalOverlay>,
    document.body
  );
}