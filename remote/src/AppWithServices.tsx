import { useState } from 'react';
import styled, { ThemeProvider } from 'styled-components';
import { LoginForm } from './components/auth/LoginForm';
import { ScriptGrid } from './components/ui/ScriptGrid';
import { ActivityFeed } from './components/ui/ActivityFeed';
import { ToastContainer } from './components/ui/ToastContainer';
import { SettingsModal } from './components/ui/SettingsModal';
import { useAuth, useHub, useActivity, useUI } from './hooks/useServices';
import { theme } from './styles/theme';
import type { Hub } from './types/Hub';

// All the styled components from before...
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
  
  /* Hexagon pattern background */
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-image: 
      radial-gradient(circle at 20% 30%, ${theme.colors.glow} 0%, transparent 50%),
      radial-gradient(circle at 80% 70%, ${theme.colors.glow} 0%, transparent 50%);
    opacity: 0.5;
    z-index: 0;
  }
  
  /* Tech grid overlay */
  &::after {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-image: 
      linear-gradient(${theme.colors.border} 1px, transparent 1px),
      linear-gradient(90deg, ${theme.colors.border} 1px, transparent 1px);
    background-size: 100px 100px;
    opacity: 0.03;
    z-index: 1;
  }
  
  > * {
    position: relative;
    z-index: 2;
  }
`;

const Header = styled.header`
  background: ${theme.colors.surface};
  border-bottom: 1px solid ${theme.colors.border};
  padding: ${theme.spacing.lg} ${theme.spacing.xl};
  backdrop-filter: blur(10px);
  flex-shrink: 0;
  box-shadow: ${theme.shadows.md};
  position: relative;
  
  /* Electric accent line */
  &::after {
    content: '';
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    height: 2px;
    background: ${theme.gradients.electric};
    opacity: 0.8;
  }
`;

const HeaderContent = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
`;

const Title = styled.h1`
  font-size: 3rem;
  font-weight: ${theme.fonts.weights.black};
  letter-spacing: -0.03em;
  background: ${theme.gradients.electric};
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0;
  text-transform: uppercase;
  position: relative;
  
  /* Subtle glow effect */
  &::before {
    content: 'SP CREW CONTROL';
    position: absolute;
    top: 0;
    left: 0;
    z-index: -1;
    background: ${theme.gradients.electric};
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    filter: blur(10px);
    opacity: 0.5;
  }
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
  background: ${theme.colors.surface};
  border-left: 2px solid ${theme.colors.border};
  padding: ${theme.spacing.lg};
  display: ${props => props.$show ? 'block' : 'none'};
  overflow-y: auto;
  backdrop-filter: blur(20px);
  position: relative;
  
  /* Subtle tech grid pattern */
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-image: 
      linear-gradient(${theme.colors.borderLight} 1px, transparent 1px),
      linear-gradient(90deg, ${theme.colors.borderLight} 1px, transparent 1px);
    background-size: 40px 40px;
    opacity: 0.1;
    z-index: 0;
  }
  
  > * {
    position: relative;
    z-index: 1;
  }
`;

const HubListContainer = styled.div`
  text-align: center;
  width: 100%;
  height: 100%;
`;

const HubListHeader = styled.div`
  margin-bottom: 60px;
`;

const RefreshButton = styled.button`
  background: ${theme.colors.surface};
  border: 2px solid ${theme.colors.primary};
  color: ${theme.colors.primary};
  padding: ${theme.spacing.md} ${theme.spacing.xl};
  border-radius: ${theme.borderRadius.md};
  cursor: pointer;
  font-family: ${theme.fonts.family};
  font-size: 0.9rem;
  font-weight: ${theme.fonts.weights.bold};
  text-transform: uppercase;
  letter-spacing: 0.1em;
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
    background: ${theme.gradients.electric};
    transition: left ${theme.animations.normal} ${theme.animations.easing};
    z-index: -1;
  }
  
  &:hover {
    color: ${theme.colors.text};
    transform: translateY(-2px);
    box-shadow: ${theme.shadows.glow};
    
    &::before {
      left: 0;
    }
  }
  
  &:active {
    transform: translateY(0);
  }
`;

const LogoutButton = styled.button`
  background: ${theme.colors.error};
  border: 2px solid ${theme.colors.error};
  color: ${theme.colors.text};
  padding: ${theme.spacing.sm} ${theme.spacing.md};
  border-radius: ${theme.borderRadius.md};
  cursor: pointer;
  font-family: ${theme.fonts.family};
  font-size: 0.85rem;
  font-weight: ${theme.fonts.weights.bold};
  text-transform: uppercase;
  letter-spacing: 0.05em;
  transition: all ${theme.animations.fast} ${theme.animations.easing};
  
  &:hover {
    background: #dc2626;
    border-color: #dc2626;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(239, 68, 68, 0.3);
  }
  
  &:active {
    transform: translateY(0);
  }
`;

const HubGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 24px;
  width: 100%;
  max-width: 900px;
`;

const HubCard = styled.div`
  background: ${theme.colors.surface};
  border: 1px solid ${theme.colors.border};
  border-radius: ${theme.borderRadius.lg};
  padding: ${theme.spacing.lg};
  cursor: pointer;
  transition: all ${theme.animations.normal} ${theme.animations.easing};
  position: relative;
  overflow: hidden;
  
  /* Hexagon corner accent */
  &::before {
    content: '';
    position: absolute;
    top: -1px;
    right: -1px;
    width: 60px;
    height: 60px;
    background: ${theme.gradients.electric};
    clip-path: polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%);
    opacity: 0.1;
    transition: opacity ${theme.animations.fast} ${theme.animations.easing};
  }
  
  &:hover {
    transform: translateY(-4px) scale(1.02);
    border-color: ${theme.colors.primary};
    background: ${theme.colors.surfaceLight};
    box-shadow: ${theme.shadows.glow};
    
    &::before {
      opacity: 0.3;
    }
    
    h3 {
      color: ${theme.colors.primary};
    }
  }
  
  h3 {
    font-size: 1.4rem;
    font-weight: ${theme.fonts.weights.bold};
    color: ${theme.colors.text};
    margin-bottom: ${theme.spacing.sm};
    transition: color ${theme.animations.fast} ${theme.animations.easing};
  }
  
  p {
    font-size: 0.85rem;
    color: ${theme.colors.textSecondary};
    font-weight: ${theme.fonts.weights.medium};
    margin: ${theme.spacing.xs} 0;
    text-transform: uppercase;
    letter-spacing: 0.05em;
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
  margin-bottom: 40px;
`;

const BackButton = styled.button`
  background: ${theme.colors.surface};
  border: 2px solid ${theme.colors.border};
  color: ${theme.colors.textSecondary};
  padding: ${theme.spacing.sm} ${theme.spacing.md};
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
    background: ${theme.gradients.electric};
    transition: left ${theme.animations.normal} ${theme.animations.easing};
    z-index: -1;
  }
  
  &:hover {
    background: ${theme.colors.surfaceLight};
    border-color: ${theme.colors.primary};
    color: ${theme.colors.primary};
    transform: translateY(-1px);
    
    &::before {
      left: 0;
    }
  }
  
  &:active {
    transform: translateY(0);
  }
`;

const SectionTitle = styled.h2`
  font-size: 1.1rem;
  font-weight: ${theme.fonts.weights.bold};
  color: ${theme.colors.primary};
  margin: 0 0 ${theme.spacing.lg} 0;
  text-align: center;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  text-shadow: 0 0 8px currentColor;
`;

const LoadingMessage = styled.div`
  text-align: center;
  color: ${theme.colors.textSecondary};
  padding: ${theme.spacing.xxxl};
  font-size: 1.1rem;
  font-family: ${theme.fonts.mono};
  letter-spacing: 0.05em;
`;

function AppWithServices() {
  const { user, loading: authLoading, error: authError, login, logout } = useAuth();
  const { 
    hubs, 
    selectedHub, 
    scripts, 
    assignment, 
    friendlyNames, 
    connectedUsers, 
    loading: hubLoading,
    discoverHubs, 
    connectToHub, 
    executeScript, 
    backToHubs,
    reloadFriendlyNames
  } = useHub();
  const { items: activity, addToActivityLog } = useActivity();
  const { showSuccess, showError } = useUI();
  
  const [view, setView] = useState<'hubs' | 'scripts'>('hubs');
  const [showSettings, setShowSettings] = useState(false);

  const handleHubSelect = async (hub: Hub) => {
    try {
      await connectToHub(hub);
      setView('scripts');
      showSuccess(`Connected to ${hub.friendly_name}`);
    } catch {
      showError(`Failed to connect to ${hub.friendly_name}`);
    }
  };

  const handleBackToHubs = () => {
    backToHubs();
    setView('hubs');
  };

  const handleScriptExecute = async (scriptName: string) => {
    try {
      addToActivityLog(`Executed ${scriptName}`, 'pending');
      await executeScript(scriptName);
      showSuccess(`Script ${scriptName} executed successfully`);
    } catch {
      showError(`Failed to execute ${scriptName}`);
      addToActivityLog(`Failed to execute ${scriptName}`, 'error');
    }
  };

  const handleSettingsClick = () => {
    setShowSettings(true);
  };

  const handleCloseSettings = () => {
    setShowSettings(false);
  };

  const handleFriendlyNamesUpdate = async () => {
    await reloadFriendlyNames();
    // Don't show success toast here - let the settings modal handle it
  };

  const handleHubSettingsUpdate = async (mode: 'shared' | 'assigned', showNames: boolean, enableTimer: boolean, timerMinutes: number) => {
    if (selectedHub) {
      // Update hub settings locally (in a real app this would save to database)
      selectedHub.mode = mode;
      selectedHub.show_script_names = showNames;
      
      // For now, just show success message
      showSuccess(`Settings updated: ${mode === 'assigned' ? '1 Button' : 'All Buttons'} mode`);
      
      // TODO: Implement timer functionality
      if (mode === 'assigned' && enableTimer) {
        showSuccess(`Timer enabled: ${timerMinutes} minutes`);
      }
    }
  };

  const handleShuffleScripts = () => {
    if (selectedHub?.mode === 'assigned') {
      showSuccess('Button shuffled');
      // TODO: Implement actual shuffle functionality
    }
  };

  if (!user) {
    return (
      <ThemeProvider theme={theme}>
        <AppContainer>
          <LoginForm 
            onLogin={login}
            loading={authLoading}
            error={authError}
          />
          <ToastContainer />
        </AppContainer>
      </ThemeProvider>
    );
  }

  return (
    <ThemeProvider theme={theme}>
      <AppContainer>
        <Header>
          <HeaderContent>
            <Title>SP CREW CONTROL</Title>
            <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
              <span style={{ color: theme.colors.textSecondary, fontFamily: theme.fonts.mono, letterSpacing: '0.05em' }}>
                {user.username}
              </span>
              <LogoutButton onClick={logout}>
                LOGOUT
              </LogoutButton>
            </div>
          </HeaderContent>
        </Header>

        <MainContent>
          <ContentArea>
            {view === 'hubs' ? (
              <HubListContainer>
                <HubListHeader>
                  <RefreshButton onClick={discoverHubs}>
                    🔄 REFRESH HUBS
                  </RefreshButton>
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
                {hubs.length === 0 && !hubLoading && (
                  <LoadingMessage>No hubs found. Click refresh to discover hubs.</LoadingMessage>
                )}
                {hubLoading && (
                  <LoadingMessage>Searching for hubs...</LoadingMessage>
                )}
              </HubListContainer>
            ) : (
              <ScriptsContainer>
                <BackHeader>
                  <BackButton onClick={handleBackToHubs}>← BACK</BackButton>
                  <h2>{selectedHub?.friendly_name}</h2>
                  <BackButton onClick={handleSettingsClick}>⚙ SETTINGS</BackButton>
                </BackHeader>
                <ScriptGrid
                  scripts={scripts}
                  assignment={assignment || undefined}
                  mode={selectedHub?.mode || 'shared'}
                  showScriptNames={selectedHub?.show_script_names || false}
                  friendlyNames={friendlyNames}
                  onScriptExecute={handleScriptExecute}
                />
              </ScriptsContainer>
            )}
          </ContentArea>

          <Sidebar $show={view === 'scripts'}>
            <div style={{ marginBottom: '24px' }}>
              <SectionTitle>Connected Users</SectionTitle>
              <div>
                {connectedUsers.map((user: { username?: string; user_id?: string }, index) => (
                  <div key={index} style={{ 
                    padding: `${theme.spacing.xs} 0`, 
                    color: theme.colors.textSecondary,
                    fontFamily: theme.fonts.mono,
                    fontSize: '0.9rem',
                    letterSpacing: '0.02em'
                  }}>
                    {user.username || user.user_id}
                  </div>
                ))}
              </div>
            </div>
            
            <div>
              <SectionTitle>Activity Feed</SectionTitle>
              <ActivityFeed items={activity} />
            </div>
          </Sidebar>
        </MainContent>
        
        <SettingsModal
          isOpen={showSettings}
          onClose={handleCloseSettings}
          scripts={scripts}
          friendlyNames={friendlyNames}
          hubMode={selectedHub?.mode || 'shared'}
          showScriptNames={selectedHub?.show_script_names || false}
          onFriendlyNamesUpdate={handleFriendlyNamesUpdate}
          onHubSettingsUpdate={handleHubSettingsUpdate}
          onShuffleScripts={handleShuffleScripts}
        />
        
        <ToastContainer />
      </AppContainer>
    </ThemeProvider>
  );
}

export default AppWithServices;