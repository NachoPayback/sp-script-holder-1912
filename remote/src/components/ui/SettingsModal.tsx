import { useState, useEffect } from 'react';
import styled from 'styled-components';
import { theme } from '../../styles/theme';
import { authService } from '../../services/AuthService';
import type { HubScript } from '../../types/Hub';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  scripts: HubScript[];
  friendlyNames: Record<string, { friendly_name: string; image_url?: string }>;
  hubMode: 'shared' | 'assigned';
  showScriptNames: boolean;
  onFriendlyNamesUpdate: () => void;
  onHubSettingsUpdate: (mode: 'shared' | 'assigned', showNames: boolean, enableTimer: boolean, timerMinutes: number) => void;
  onShuffleScripts: () => void;
}

const ModalOverlay = styled.div<{ $isOpen: boolean }>`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(8px);
  display: ${props => props.$isOpen ? 'flex' : 'none'};
  align-items: center;
  justify-content: center;
  z-index: 1000;
`;

const ModalContainer = styled.div`
  background: ${theme.colors.surface};
  border: 2px solid ${theme.colors.primary};
  border-radius: ${theme.borderRadius.xl};
  padding: ${theme.spacing.xxl};
  max-width: 650px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
  backdrop-filter: blur(20px);
  box-shadow: ${theme.shadows.lg}, ${theme.shadows.glow};
  position: relative;
  
  /* Tech corner accent */
  &::before {
    content: '';
    position: absolute;
    top: -2px;
    right: -2px;
    width: 80px;
    height: 80px;
    background: ${theme.gradients.electric};
    clip-path: polygon(30% 0%, 100% 0%, 100% 70%, 70% 100%, 0% 100%, 0% 30%);
    opacity: 0.3;
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
  align-items: center;
  gap: 12px;
  padding: 16px;
  margin: 8px 0;
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

export function SettingsModal({ 
  isOpen, 
  onClose, 
  scripts, 
  friendlyNames,
  hubMode,
  showScriptNames,
  onFriendlyNamesUpdate,
  onHubSettingsUpdate,
  onShuffleScripts
}: SettingsModalProps) {
  const [activeTab, setActiveTab] = useState<'hub' | 'names'>('hub');
  const [inputValues, setInputValues] = useState<Record<string, string>>({});
  const [imageValues, setImageValues] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState<Record<string, boolean>>({});
  const [tempMode, setTempMode] = useState<'shared' | 'assigned'>(hubMode);
  const [tempShowNames, setTempShowNames] = useState(showScriptNames);
  const [tempEnableTimer, setTempEnableTimer] = useState(false);
  const [tempTimerMinutes, setTempTimerMinutes] = useState(5);
  
  // Check if current user is admin
  const currentUser = authService.getCurrentUser();
  const isAdmin = currentUser?.username === 'NachoPayback';

  // Initialize values when modal opens
  useEffect(() => {
    if (isOpen) {
      // Initialize script name input values
      const values: Record<string, string> = {};
      const images: Record<string, string> = {};
      scripts.forEach(script => {
        const scriptName = typeof script === 'string' ? script : script.script_name;
        values[scriptName] = friendlyNames[scriptName]?.friendly_name || '';
        images[scriptName] = friendlyNames[scriptName]?.image_url || '';
      });
      setInputValues(values);
      setImageValues(images);
      
      // Initialize hub settings
      setTempMode(hubMode);
      setTempShowNames(showScriptNames);
      setActiveTab(isAdmin ? 'hub' : 'names'); // Default to hub settings for admin, names for non-admin
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

  const handleSave = async (scriptName: string) => {
    const friendlyName = inputValues[scriptName]?.trim();
    const imageUrl = imageValues[scriptName]?.trim();
    
    if (!friendlyName && !imageUrl) {
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
          image_url: imageUrl || null
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

  return (
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
            {!isAdmin && (
              <div style={{ marginBottom: '16px', padding: '12px', background: 'rgba(59, 130, 246, 0.1)', borderRadius: '8px', color: '#94a3b8' }}>
                <strong>Note:</strong> Only administrators can modify hub settings. You can view script names here.
              </div>
            )}
            
            <RefreshButton onClick={onFriendlyNamesUpdate}>
              🔄 Refresh Script Names
            </RefreshButton>

            {scripts.length === 0 ? (
              <EmptyState>No scripts found</EmptyState>
            ) : (
              scripts.map(script => {
                const scriptName = typeof script === 'string' ? script : script.script_name;
                const currentFriendlyName = friendlyNames[scriptName]?.friendly_name || '';
                const isSaving = saving[scriptName];
                
                return (
                  <ScriptItem key={scriptName}>
                    <ScriptInfo>
                      <ScriptName>{scriptName}</ScriptName>
                      <AutoName>Auto: {getAutoName(scriptName)}</AutoName>
                      {friendlyNames[scriptName]?.image_url && (
                        <div style={{ fontSize: '0.7rem', color: '#10b981', marginTop: '4px' }}>
                          🖼️ Has custom image
                        </div>
                      )}
                    </ScriptInfo>
                    {isAdmin ? (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', flex: '1' }}>
                        <FriendlyInput
                          type="text"
                          value={inputValues[scriptName] || ''}
                          onChange={e => handleInputChange(scriptName, e.target.value)}
                          placeholder="Custom friendly name..."
                          disabled={isSaving}
                        />
                        <FriendlyInput
                          type="url"
                          value={imageValues[scriptName] || ''}
                          onChange={e => handleImageChange(scriptName, e.target.value)}
                          placeholder="Image URL (replaces all text)..."
                          disabled={isSaving}
                        />
                        {imageValues[scriptName] && (
                          <div style={{ 
                            display: 'flex', 
                            alignItems: 'center', 
                            gap: '12px',
                            padding: '8px',
                            background: 'rgba(30, 41, 59, 0.3)',
                            borderRadius: '6px'
                          }}>
                            <img 
                              src={imageValues[scriptName]} 
                              alt="Preview"
                              style={{ 
                                width: '60px', 
                                height: '60px', 
                                objectFit: 'cover',
                                borderRadius: '4px',
                                border: '1px solid rgba(148, 163, 184, 0.2)'
                              }}
                              onError={e => {
                                e.currentTarget.style.display = 'none';
                              }}
                            />
                            <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
                              Preview (hexagon crop will be applied on button)
                            </div>
                          </div>
                        )}
                        <div style={{ display: 'flex', gap: '8px' }}>
                          <SaveButton 
                            onClick={() => handleSave(scriptName)}
                            disabled={isSaving || (!inputValues[scriptName]?.trim() && !imageValues[scriptName]?.trim())}
                          >
                            {isSaving ? '...' : 'SAVE'}
                          </SaveButton>
                          {(currentFriendlyName || friendlyNames[scriptName]?.image_url) && (
                            <DeleteButton 
                              onClick={() => handleDelete(scriptName)}
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
    </ModalOverlay>
  );
}