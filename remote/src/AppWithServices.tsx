import { useState } from 'react';
import styled, { ThemeProvider } from 'styled-components';
import { LoginForm } from './components/auth/LoginForm';
import { ScriptGrid } from './components/ui/ScriptGrid';
import { ActivityFeed } from './components/ui/ActivityFeed';
import { ToastContainer } from './components/ui/ToastContainer';
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
  font-size: 4rem;
  font-weight: 900;
  letter-spacing: -0.02em;
  background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 50%, #6366f1 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0;
  text-shadow: 0 0 40px rgba(59, 130, 246, 0.5);
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
  width: 300px;
  background: rgba(30, 41, 59, 0.5);
  border-left: 1px solid rgba(148, 163, 184, 0.1);
  padding: 24px;
  display: ${props => props.$show ? 'block' : 'none'};
  overflow-y: auto;
  backdrop-filter: blur(10px);
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
  
  &:hover {
    background: rgba(59, 130, 246, 0.2);
    border-color: rgba(59, 130, 246, 0.5);
    transform: translateY(-2px);
    box-shadow: 0 4px 20px rgba(59, 130, 246, 0.3);
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
  margin-bottom: 40px;
`;

const BackButton = styled.button`
  background: rgba(30, 41, 59, 0.5);
  border: 1px solid rgba(148, 163, 184, 0.2);
  color: #e2e8f0;
  padding: 8px 16px;
  border-radius: 8px;
  cursor: pointer;
  font-family: inherit;
  font-weight: 600;
  transition: all 0.2s ease;
  
  &:hover {
    background: rgba(59, 130, 246, 0.2);
    border-color: rgba(59, 130, 246, 0.5);
  }
`;

const SectionTitle = styled.h2`
  font-size: 1.2rem;
  font-weight: 700;
  color: #f1f5f9;
  margin: 0 0 24px 0;
  text-align: center;
`;

const LoadingMessage = styled.div`
  text-align: center;
  color: #94a3b8;
  padding: 48px;
  font-size: 1.1rem;
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
    backToHubs 
  } = useHub();
  const { items: activity, addToActivityLog } = useActivity();
  const { showSuccess, showError } = useUI();
  
  const [view, setView] = useState<'hubs' | 'scripts'>('hubs');

  const handleHubSelect = async (hub: Hub) => {
    try {
      await connectToHub(hub);
      setView('scripts');
      showSuccess(`Connected to ${hub.friendly_name}`);
    } catch (error) {
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
    } catch (error) {
      showError(`Failed to execute ${scriptName}`);
      addToActivityLog(`Failed to execute ${scriptName}`, 'error');
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
              <span style={{ color: '#94a3b8' }}>
                {user.username}
              </span>
              <button 
                onClick={logout}
                style={{
                  background: '#ef4444',
                  color: 'white',
                  border: 'none',
                  padding: '8px 16px',
                  borderRadius: '4px',
                  cursor: 'pointer'
                }}
              >
                LOGOUT
              </button>
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
                  <button>⚙ SETTINGS</button>
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
                {connectedUsers.map((user: any, index) => (
                  <div key={index} style={{ padding: '4px 0', color: '#94a3b8' }}>
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
        
        <ToastContainer />
      </AppContainer>
    </ThemeProvider>
  );
}

export default AppWithServices;