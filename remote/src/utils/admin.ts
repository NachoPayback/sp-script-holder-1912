import { authService } from '../services/AuthService';

/**
 * List of admin usernames who have full access to the system
 */
const ADMIN_USERNAMES = ['NachoPayback', 'DanielPayback'];

/**
 * Check if the current user is an admin
 * @returns true if current user is an admin, false otherwise
 */
export const isCurrentUserAdmin = (): boolean => {
  const currentUser = authService.getCurrentUser();
  return currentUser ? ADMIN_USERNAMES.includes(currentUser.username) : false;
};

/**
 * Check if a specific username is an admin
 * @param username - The username to check
 * @returns true if the username is an admin, false otherwise
 */
export const isUserAdmin = (username: string): boolean => {
  return ADMIN_USERNAMES.includes(username);
};