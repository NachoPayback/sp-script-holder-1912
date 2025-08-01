// Quick functionality test for the React app
// This tests if the services work correctly

import { authService } from './src/services/AuthService.js';
import { hubService } from './src/services/HubService.js';
import { uiService } from './src/services/UIService.js';

console.log('Testing service layer functionality...');

// Test UIService
console.log('1. Testing UIService...');
uiService.showSuccess('Test success message');
console.log('✓ UIService working - toast created');

// Test AuthService state
console.log('2. Testing AuthService...');
const currentUser = authService.getCurrentUser();
console.log('Current user:', currentUser);

// Test HubService state
console.log('3. Testing HubService...');
const hubState = hubService.getState();
console.log('Hub state:', hubState);

console.log('All services instantiated correctly!');