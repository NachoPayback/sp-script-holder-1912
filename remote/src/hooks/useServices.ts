// React hooks for clean service integration
// Separates UI from business logic

import { useState, useEffect } from 'react';
import { authService } from '../services/AuthService';
import { hubService } from '../services/HubService';
import { activityService } from '../services/ActivityService';
import { uiService } from '../services/UIService';

// Auth hook
export const useAuth = () => {
  const [authState, setAuthState] = useState({
    user: authService.getCurrentUser(),
    loading: false,
    error: ''
  });

  useEffect(() => {
    const unsubscribe = authService.subscribe(setAuthState);
    return unsubscribe;
  }, []);

  return {
    ...authState,
    login: authService.login.bind(authService),
    logout: authService.logout.bind(authService)
  };
};

// Hub hook
export const useHub = () => {
  const [hubState, setHubState] = useState(hubService.getState());

  useEffect(() => {
    const unsubscribe = hubService.subscribe(setHubState);
    return unsubscribe;
  }, []);

  return {
    ...hubState,
    discoverHubs: hubService.discoverHubs.bind(hubService),
    connectToHub: hubService.connectToHub.bind(hubService),
    executeScript: hubService.executeScript.bind(hubService),
    backToHubs: hubService.backToHubs.bind(hubService)
  };
};

// Activity hook
export const useActivity = () => {
  const [activityState, setActivityState] = useState(activityService.getState());

  useEffect(() => {
    const unsubscribe = activityService.subscribe(setActivityState);
    return unsubscribe;
  }, []);

  return {
    ...activityState,
    addToActivityLog: activityService.addToActivityLog.bind(activityService),
    updateActivityLogByCommandId: activityService.updateActivityLogByCommandId.bind(activityService),
    clearActivityLog: activityService.clearActivityLog.bind(activityService)
  };
};

// UI hook
export const useUI = () => {
  const [uiState, setUIState] = useState(uiService.getState());

  useEffect(() => {
    const unsubscribe = uiService.subscribe(setUIState);
    return unsubscribe;
  }, []);

  return {
    ...uiState,
    showToast: uiService.showToast.bind(uiService),
    showSuccess: uiService.showSuccess.bind(uiService),
    showError: uiService.showError.bind(uiService),
    showInfo: uiService.showInfo.bind(uiService),
    removeToast: uiService.removeToast.bind(uiService)
  };
};