import { useState, useEffect } from 'react';
import styled, { ThemeProvider } from 'styled-components';
import { LoginForm } from './components/auth/LoginForm';
import { ScriptGrid } from './components/ui/ScriptGrid';
import { ActivityFeed } from './components/ui/ActivityFeed';
import { ScriptCustomizationModal } from './components/ui/ScriptCustomizationModal';
import { HubSettingsModal } from './components/ui/HubSettingsModal';
import { FakeCallModal } from './components/ui/FakeCallModal';
import { ToastProvider } from './components/ui/ToastContainer';
import { Button } from './components/ui/Button';
import { useAuth } from './hooks/useAuth';
import { useRealtime } from './hooks/useRealtime';
import { useHubPresence } from './hooks/useHubPresence';
import { theme } from './styles/theme';
import { hubApi, assignmentApi, scriptApi } from './services/api';
import { isUserAdmin } from './utils/admin';
import { getUserColor } from './utils/userColors';
import type { Hub, HubScript, Assignment } from './types/Hub';
import { IoRefresh, IoLogOut, IoSettings, IoPerson, IoShield } from 'react-icons/io5';

const AppContainer = styled.div`
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: ${theme.colors.background};
  color: ${theme.colors.text};
  font-family: ${theme.fonts.family};
  display: flex;
  flex-direction: column;
  overflow: hidden;
  
  /* Animated background like vanilla */
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: 
      radial-gradient(circle at 20% 30%, rgba(56, 189, 248, 0.15) 0%, transparent 40%),
      radial-gradient(circle at 80% 70%, rgba(59, 130, 246, 0.1) 0%, transparent 40%),
      radial-gradient(circle at 50% 50%, rgba(99, 102, 241, 0.08) 0%, transparent 60%);
    animation: backgroundShift 20s ease-in-out infinite;
    z-index: -1;
  }
  
  @keyframes backgroundShift {
    0%, 100% { transform: scale(1) rotate(0deg); }
    50% { transform: scale(1.1) rotate(5deg); }
  }
`;

const Header = styled.header`
  background: rgba(30, 41, 59, 0.3);
  border-bottom: 1px solid rgba(148, 163, 184, 0.1);
  padding: 20px 40px;
  backdrop-filter: blur(20px);
  flex-shrink: 0;
`;

const HeaderContent = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
`;

const Title = styled.h1`
  font-family: ${theme.fonts.display};
  font-size: 3.5rem;
  font-weight: ${theme.fonts.weights.bold};
  letter-spacing: -0.01em;
  background: ${theme.gradients.electric};
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0;
  text-shadow: 0 0 40px ${theme.colors.glow};
  user-select: none;
`;

const UserSection = styled.div`
  display: flex;
  align-items: center;
  gap: 16px;
`;

const UserInfo = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: ${theme.colors.surface};
  border-radius: ${theme.borderRadius.lg};
  border: 1px solid ${theme.colors.borderLight};
`;

const Username = styled.span`
  font-family: ${theme.fonts.family};
  font-weight: ${theme.fonts.weights.medium};
  color: ${theme.colors.text};
  font-size: 0.925rem;
`;

const AdminBadge = styled.span`
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  background: ${theme.colors.primary}20;
  border: 1px solid ${theme.colors.primary}40;
  border-radius: ${theme.borderRadius.sm};
  color: ${theme.colors.primary};
  font-size: 0.75rem;
  font-weight: ${theme.fonts.weights.semibold};
  text-transform: uppercase;
  letter-spacing: 0.05em;
`;


const MainContent = styled.main`
  flex: 1;
  display: flex;
  overflow: hidden;
`;

const ContentArea = styled.div`
  flex: 1;
  padding: 40px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-start;
`;

const Sidebar = styled.aside<{ $show: boolean }>`
  width: 320px;
  background: rgba(30, 41, 59, 0.3);
  border-left: 1px solid rgba(148, 163, 184, 0.1);
  padding: ${theme.spacing.lg};
  display: ${props => props.$show ? 'flex' : 'none'};
  flex-direction: column;
  overflow: hidden;
  backdrop-filter: blur(20px);
  border-radius: 0;
  box-shadow: inset 1px 0 0 rgba(148, 163, 184, 0.1);
`;

const HubListContainer = styled.div`
  text-align: center;
  width: 100%;
  height: 100%;
`;

const HubListHeader = styled.div`
  margin-bottom: 60px;
`;


const HubGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 24px;
  width: 100%;
  max-width: 900px;
`;

const HubCard = styled.div`
  background: rgba(30, 41, 59, 0.5);
  border: 1px solid rgba(148, 163, 184, 0.1);
  border-radius: 16px;
  padding: 24px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  backdrop-filter: blur(10px);
  position: relative;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  
  &:hover {
    transform: translateY(-4px);
    border-color: rgba(59, 130, 246, 0.3);
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
  }
  
  h3 {
    font-size: 1.5rem;
    font-weight: 700;
    color: #f1f5f9;
    margin-bottom: 8px;
  }
  
  p {
    font-size: 0.9rem;
    color: #94a3b8;
    font-weight: 500;
    margin: 4px 0;
  }
`;

const ScriptsContainer = styled.div`
  display: flex;
  flex-direction: column;
  height: 100%;
`;

const BackHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: ${theme.spacing.lg};
`;

const BackButton = styled.button`
  background: rgba(30, 41, 59, 0.5);
  border: 1px solid rgba(148, 163, 184, 0.2);
  color: #e2e8f0;
  padding: 12px 24px;
  border-radius: 12px;
  cursor: pointer;
  font-family: inherit;
  font-size: 0.95rem;
  font-weight: 600;
  transition: all 0.2s ease;
  backdrop-filter: blur(10px);
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  
  &:hover {
    background: rgba(59, 130, 246, 0.2);
    border-color: rgba(59, 130, 246, 0.5);
    transform: translateY(-2px);
    box-shadow: 0 4px 20px rgba(59, 130, 246, 0.3);
  }
`;

const HubName = styled.h2`
  font-size: 2.2rem;
  font-weight: ${theme.fonts.weights.black};
  color: ${theme.colors.text};
  margin: 0;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 50%, #6366f1 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  text-shadow: 0 0 30px rgba(59, 130, 246, 0.4);
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.3));
`;

const EditModeToggle = styled.button<{ $isActive: boolean }>`
  background: ${props => props.$isActive ? 'rgba(59, 130, 246, 0.3)' : 'rgba(30, 41, 59, 0.5)'};
  border: 1px solid ${props => props.$isActive ? '#3b82f6' : 'rgba(148, 163, 184, 0.2)'};
  color: ${props => props.$isActive ? '#60a5fa' : '#e2e8f0'};
  padding: 12px 20px;
  border-radius: 12px;
  cursor: pointer;
  font-family: inherit;
  font-size: 0.9rem;
  font-weight: 700;
  transition: all 0.2s ease;
  backdrop-filter: blur(10px);
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  text-transform: uppercase;
  letter-spacing: 0.1em;
  
  &:hover {
    background: ${props => props.$isActive ? 'rgba(59, 130, 246, 0.4)' : 'rgba(59, 130, 246, 0.2)'};
    border-color: rgba(59, 130, 246, 0.5);
    transform: translateY(-2px);
    box-shadow: 0 4px 20px rgba(59, 130, 246, 0.3);
  }
  
  ${props => props.$isActive && `
    box-shadow: 0 0 20px rgba(59, 130, 246, 0.6), 0 2px 10px rgba(0, 0, 0, 0.1);
    animation: editModePulse 2s ease-in-out infinite;
    
    @keyframes editModePulse {
      0%, 100% { box-shadow: 0 0 20px rgba(59, 130, 246, 0.6), 0 2px 10px rgba(0, 0, 0, 0.1); }
      50% { box-shadow: 0 0 30px rgba(59, 130, 246, 0.8), 0 4px 20px rgba(59, 130, 246, 0.3); }
    }
  `}
`;


const SectionTitle = styled.h2`
  font-size: 1.3rem;
  font-weight: ${theme.fonts.weights.black};
  color: #f1f5f9;
  margin: 0 0 ${theme.spacing.lg} 0;
  text-align: center;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  background: linear-gradient(135deg, #60a5fa 0%, #a5b4fc 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  padding-bottom: ${theme.spacing.sm};
  border-bottom: 1px solid rgba(148, 163, 184, 0.2);
`;

const LoadingMessage = styled.div`
  text-align: center;
  color: ${theme.colors.textSecondary};
  padding: ${theme.spacing.xxl};
  font-size: 1.1rem;
`;

const SidebarSection = styled.div`
  margin-bottom: ${theme.spacing.xl};
  background: rgba(0, 0, 0, 0.2);
  border-radius: ${theme.borderRadius.lg};
  padding: ${theme.spacing.lg};
  border: 1px solid rgba(148, 163, 184, 0.1);
`;

const UserBubbleContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: ${theme.spacing.sm};
`;

const UserBubble = styled.div<{ $userColor: string }>`
  display: flex;
  align-items: center;
  justify-content: center;
  background: ${props => props.$userColor}20;
  border: 2px solid ${props => props.$userColor};
  border-radius: ${theme.borderRadius.lg};
  padding: ${theme.spacing.md} ${theme.spacing.lg};
  transition: all 0.2s ease;
  
  &:hover {
    background: ${props => props.$userColor}30;
    transform: translateX(4px);
    box-shadow: 0 4px 12px ${props => props.$userColor}40;
  }
`;

const UserName = styled.span<{ $userColor: string }>`
  color: ${props => props.$userColor};
  font-weight: ${theme.fonts.weights.bold};
  font-size: 1rem;
  text-shadow: 0 0 8px ${props => props.$userColor}60;
`;

const ActivityFeedContainer = styled.div`
  background: rgba(0, 0, 0, 0.3);
  border-radius: ${theme.borderRadius.md};
  padding: ${theme.spacing.md};
  border: 1px solid rgba(148, 163, 184, 0.1);
  flex: 1;
  overflow: hidden;
  min-height: 200px;
  max-height: 400px;
  display: flex;
  flex-direction: column;
`;

function App() {
  const { user, loading: authLoading, error: authError, login, logout } = useAuth();
  const [view, setView] = useState<'hubs' | 'scripts'>('hubs');
  const [hubs, setHubs] = useState<Hub[]>([]);
  const [selectedHub, setSelectedHub] = useState<Hub | null>(null);
  const [scripts, setScripts] = useState<HubScript[]>([]);
  const [assignment, setAssignment] = useState<Assignment | null>(null);
  const [friendlyNames, setFriendlyNames] = useState<Record<string, { friendly_name: string; image_url?: string; custom_color?: string; position_x?: number; position_y?: number; image_scale?: number }>>({});
  const [activity, setActivity] = useState<any[]>([]);
  const [connectedUsers, setConnectedUsers] = useState<any[]>([]);
  const [isEditMode, setIsEditMode] = useState(false);
  const [hubSettingsModalOpen, setHubSettingsModalOpen] = useState(false);
  const [scriptCustomizationModalOpen, setScriptCustomizationModalOpen] = useState(false);
  const [selectedScriptForEdit, setSelectedScriptForEdit] = useState<string | null>(null);
  const [fakeCallModalOpen, setFakeCallModalOpen] = useState(false);
  
  const { scriptCommands } = useRealtime(selectedHub?.id || '');
  const { hubs: presenceHubs, isConnected: presenceConnected } = useHubPresence(!!user);

  // Update hubs state when presence changes
  useEffect(() => {
    if (presenceConnected && presenceHubs.length > 0) {
      setHubs(presenceHubs);
    } else if (user) {
      // Fallback to API polling if presence fails
      loadHubs();
    }
  }, [presenceHubs, presenceConnected, user]);

  // Auto-refresh functionality like vanilla version
  useEffect(() => {
    if (!user) return;
    
    const interval = setInterval(() => {
      if (!selectedHub) {
        // If no hub connected, discover hubs
        loadHubs();
      } else {
        // If hub connected, update connected users
        updateConnectedUsers();
      }
    }, 30000); // 30 seconds like vanilla

    return () => clearInterval(interval);
  }, [user, selectedHub]);


  // Update activity feed from real-time script commands
  useEffect(() => {
    console.log('Activity feed update - scriptCommands:', scriptCommands);
    const newActivity = scriptCommands.map((cmd: any) => ({
      id: cmd.id,
      user: cmd.user_id || 'Unknown',
      action: `Executed ${cmd.script_name || 'Unknown Script'}`,
      status: cmd.status === 'completed' ? 'success' : cmd.status === 'failed' ? 'error' : 'pending' as const,
      timestamp: cmd.created_at ? new Date(cmd.created_at).toLocaleTimeString() : new Date().toLocaleTimeString(),
      commandId: cmd.id
    }));
    setActivity(newActivity.slice(0, 50)); // Keep last 50 items
  }, [scriptCommands]);

  const loadHubs = async () => {
    try {
      const response = await hubApi.getHubs();
      if (response.success && response.hubs) {
        setHubs(response.hubs);
      } else {
        setHubs([]);
      }
    } catch (error) {
      console.error('Failed to load hubs:', error);
      setHubs([]);
    }
  };


  const handleScriptExecute = async (scriptName: string) => {
    if (!selectedHub || !user) return;

    // Check if we're in edit mode and user is admin first
    if (isEditMode && isUserAdmin(user)) {
      // Open customization for ALL scripts including mute_call
      setSelectedScriptForEdit(scriptName);
      setScriptCustomizationModalOpen(true);
      return;
    }

    // Handle fake "mute_call" script
    if (scriptName === 'mute_call') {
      setFakeCallModalOpen(true);
      return;
    }

    try {
      await scriptApi.execute(selectedHub.id, scriptName, user.username);
      
      // Add immediate feedback to activity
      setActivity(prev => [{
        id: Date.now().toString(),
        user: user.username,
        action: `Executed ${scriptName}`,
        status: 'pending' as const,
        timestamp: new Date().toLocaleTimeString()
      }, ...prev.slice(0, 49)]);
    } catch (error) {
      console.error('Failed to execute script:', error);
      setActivity(prev => [{
        id: Date.now().toString(),
        user: user.username,
        action: `Failed to execute ${scriptName}`,
        status: 'error' as const,
        timestamp: new Date().toLocaleTimeString()
      }, ...prev.slice(0, 49)]);
    }
  };

  const handleHubSelect = (hub: Hub) => {
    setSelectedHub(hub);
    setView('scripts');
    loadHubData(hub);
  };

  const handleBackToHubs = () => {
    setView('hubs');
    setSelectedHub(null);
    setScripts([]);
    setAssignment(null);
  };

  const loadHubData = async (hub: Hub) => {
    try {
      // Load scripts
      const scriptsResponse = await hubApi.getHubScripts(hub.id);
      if (scriptsResponse.success && scriptsResponse.scripts) {
        // Add fake "Mute the Call" script to the list
        const fakeScript: HubScript = {
          id: 'fake_mute_call',
          hub_id: hub.id,
          script_name: 'mute_call',
          friendly_name: 'Mute the Call'
        };
        const scriptsWithFake = [...scriptsResponse.scripts, fakeScript];
        setScripts(scriptsWithFake);
      } else {
        // Always include fake script even if no real scripts
        const fakeScript: HubScript = {
          id: 'fake_mute_call',
          hub_id: hub.id,
          script_name: 'mute_call',
          friendly_name: 'Mute the Call'
        };
        setScripts([fakeScript]);
      }

      // Load assignment if in assigned mode
      if (hub.mode === 'assigned') {
        const assignmentResponse = await assignmentApi.get(hub.id, user!.username);
        setAssignment(assignmentResponse.assignment || null);
      } else {
        setAssignment(null);
      }

      // Load connected users like vanilla version
      await updateConnectedUsers(hub.id);

      // Load friendly names
      const scriptNames = scriptsResponse.success ? scriptsResponse.scripts.map(s => 
        typeof s === 'string' ? s : s.script_name
      ) : [];
      // Include mute_call in the scripts to load so its customization is retrieved
      const scriptNamesWithMute = [...scriptNames, 'mute_call'];
      const friendlyResponse = await hubApi.getFriendlyNames(scriptNamesWithMute);
      if (friendlyResponse.success) {
        // Use loaded friendly names, including any customization for mute_call
        const friendlyNamesWithDefaults = {
          ...friendlyResponse.friendly_names,
          // Only set default if mute_call wasn't already customized
          'mute_call': friendlyResponse.friendly_names['mute_call'] || { 
            friendly_name: 'Mute the Call', 
            custom_color: '#ef4444' 
          }
        };
        setFriendlyNames(friendlyNamesWithDefaults);
      } else {
        // Fallback if no friendly names loaded
        setFriendlyNames({
          'mute_call': { friendly_name: 'Mute the Call', custom_color: '#ef4444' }
        });
      }
    } catch (error) {
      console.error('Failed to load hub data:', error);
    }
  };

  const updateConnectedUsers = async (hubId?: string) => {
    const currentHub = hubId ? { id: hubId } : selectedHub;
    if (!currentHub || !user) return;

    try {
      const response = await hubApi.getConnectedUsers(currentHub.id);
      if (response.success && response.users && response.users.length > 0) {
        setConnectedUsers(response.users);
      } else {
        // Fallback to current user like vanilla version
        setConnectedUsers([{ username: user.username, user_id: user.username }]);
      }
    } catch (error) {
      console.error('Error fetching connected users:', error);
      setConnectedUsers([{ username: user.username, user_id: user.username }]);
    }
  };

  const handleFriendlyNamesUpdate = async () => {
    if (!selectedHub) return;
    const scriptNames = scripts.map(s => 
      typeof s === 'string' ? s : s.script_name
    );
    // Include mute_call so its customization is loaded
    const scriptNamesWithMute = [...scriptNames, 'mute_call'];
    const response = await hubApi.getFriendlyNames(scriptNamesWithMute);
    if (response.success) {
      // Preserve existing friendly names and only update what was loaded
      setFriendlyNames(prev => ({
        ...prev,
        ...response.friendly_names
      }));
    }
  };

  const handleHubSettingsUpdate = async (mode: 'shared' | 'assigned', showNames: boolean, enableTimer: boolean, timerMinutes: number) => {
    // This would normally update hub settings via API
    console.log('Hub settings update:', { mode, showNames, enableTimer, timerMinutes });
  };

  const handleShuffleScripts = () => {
    // This would normally shuffle script assignments via API
    console.log('Shuffle scripts requested');
  };

  const handleRefreshScripts = () => {
    if (selectedHub) {
      loadHubData(selectedHub);
    }
  };

  if (!user) {
    return (
      <ThemeProvider theme={theme}>
        <ToastProvider>
          <AppContainer>
            <LoginForm 
              onLogin={login}
              loading={authLoading}
              error={authError}
            />
          </AppContainer>
        </ToastProvider>
      </ThemeProvider>
    );
  }

  return (
    <ThemeProvider theme={theme}>
      <ToastProvider>
        <AppContainer>
        <Header>
          <HeaderContent>
            <Title>SP CREW CONTROL</Title>
            {user && (
              <UserSection>
                <UserInfo>
                  <IoPerson size={16} />
                  <Username>{user.username}</Username>
                  {isUserAdmin(user) && (
                    <AdminBadge>
                      <IoShield size={12} />
                      Admin
                    </AdminBadge>
                  )}
                </UserInfo>
                <Button variant="danger" size="sm" onClick={logout}>
                  <IoLogOut />
                  Logout
                </Button>
              </UserSection>
            )}
          </HeaderContent>
        </Header>

        <MainContent>
          <ContentArea>
            {view === 'hubs' ? (
              <HubListContainer>
                <HubListHeader>
                  <Button variant="secondary" onClick={loadHubs}>
                    <IoRefresh />
                    Refresh Hubs
                  </Button>
                </HubListHeader>
                <HubGrid>
                  {hubs.map(hub => (
                    <HubCard key={hub.id} onClick={() => handleHubSelect(hub)}>
                      <h3>{hub.friendly_name}</h3>
                      <p>Mode: {hub.mode}</p>
                      <p>ID: {hub.machine_id}</p>
                    </HubCard>
                  ))}
                </HubGrid>
                {hubs.length === 0 && (
                  <LoadingMessage>Searching for hubs...</LoadingMessage>
                )}
              </HubListContainer>
            ) : (
              <ScriptsContainer>
                <BackHeader>
                  <BackButton onClick={handleBackToHubs}>← BACK</BackButton>
                  <HubName>{selectedHub?.friendly_name}</HubName>
                  <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                    {/* Edit mode toggle - only show for admin */}
                    {isUserAdmin(user) && (
                      <EditModeToggle 
                        $isActive={isEditMode}
                        onClick={() => setIsEditMode(!isEditMode)}
                        title={isEditMode ? 'Exit edit mode' : 'Enter edit mode - click buttons to customize them'}
                      >
                        {isEditMode ? 'EXIT EDIT' : 'EDIT MODE'}
                      </EditModeToggle>
                    )}
                    <Button variant="ghost" onClick={() => {
                      setHubSettingsModalOpen(true);
                    }}>
                      <IoSettings />
                      Hub Settings
                    </Button>
                  </div>
                </BackHeader>
                {isEditMode && isUserAdmin(user) && (
                  <div style={{
                    padding: '12px 16px',
                    margin: '0 0 20px 0',
                    background: 'rgba(59, 130, 246, 0.1)',
                    border: `1px solid ${theme.colors.primary}40`,
                    borderRadius: theme.borderRadius.md,
                    color: theme.colors.primary,
                    textAlign: 'center',
                    fontSize: '0.9rem',
                    fontWeight: theme.fonts.weights.semibold
                  }}>
                    <strong>Edit Mode Active:</strong> Click any button to customize its appearance, colors, and position
                  </div>
                )}
                <ScriptGrid
                  scripts={scripts}
                  assignment={assignment || undefined}
                  mode={selectedHub?.mode || 'shared'}
                  showScriptNames={selectedHub?.show_script_names || false}
                  friendlyNames={friendlyNames}
                  onScriptExecute={handleScriptExecute}
                  isEditMode={isEditMode}
                />
              </ScriptsContainer>
            )}
          </ContentArea>

          <Sidebar $show={view === 'scripts'}>
            <SidebarSection>
              <SectionTitle>Connected Users</SectionTitle>
              <UserBubbleContainer>
                {connectedUsers.map((user: any, index) => {
                  const username = user.username || user.user_id;
                  const userColor = getUserColor(username);
                  
                  return (
                    <UserBubble key={index} $userColor={userColor}>
                      <UserName $userColor={userColor}>{username}</UserName>
                    </UserBubble>
                  );
                })}
              </UserBubbleContainer>
            </SidebarSection>
            
            <SidebarSection style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
              <SectionTitle>Activity Feed</SectionTitle>
              <ActivityFeedContainer>
                <ActivityFeed items={activity} />
              </ActivityFeedContainer>
            </SidebarSection>
          </Sidebar>
        </MainContent>
        
        <HubSettingsModal
          isOpen={hubSettingsModalOpen}
          onClose={() => setHubSettingsModalOpen(false)}
          hubName={selectedHub?.friendly_name || 'Hub'}
          currentMode={selectedHub?.mode || 'shared'}
          currentShowNames={selectedHub?.show_script_names || false}
          onSave={handleHubSettingsUpdate}
          onShuffleScripts={handleShuffleScripts}
          onRefreshScripts={handleRefreshScripts}
        />
        
        <ScriptCustomizationModal
          isOpen={scriptCustomizationModalOpen}
          onClose={() => {
            setScriptCustomizationModalOpen(false);
            setSelectedScriptForEdit(null);
          }}
          scriptName={selectedScriptForEdit || ''}
          currentFriendlyName={selectedScriptForEdit ? friendlyNames[selectedScriptForEdit]?.friendly_name : ''}
          currentImageUrl={selectedScriptForEdit ? friendlyNames[selectedScriptForEdit]?.image_url : ''}
          currentColor={selectedScriptForEdit ? friendlyNames[selectedScriptForEdit]?.custom_color : ''}
          currentPositionX={selectedScriptForEdit ? friendlyNames[selectedScriptForEdit]?.position_x : 0}
          currentPositionY={selectedScriptForEdit ? friendlyNames[selectedScriptForEdit]?.position_y : 0}
          currentImageScale={selectedScriptForEdit ? friendlyNames[selectedScriptForEdit]?.image_scale : 100}
          onSave={handleFriendlyNamesUpdate}
        />
        
        <FakeCallModal
          isOpen={fakeCallModalOpen}
          onClose={() => setFakeCallModalOpen(false)}
        />
        </AppContainer>
      </ToastProvider>
    </ThemeProvider>
  );
}

export default App;
