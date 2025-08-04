import type { User } from '../types/User';

/**
 * Check if a user is an admin based on their permissions from Supabase
 * @param user - The user object to check
 * @returns true if user is an admin, false otherwise
 */
export const isUserAdmin = (user: User | null): boolean => {
  if (!user || !user.permissions) {
    return false;
  }
  return user.permissions.admin === true;
};

/**
 * Check if a specific username is an admin
 * @param _username - The username to check (unused - need full user object)
 * @returns false - this function requires the full user object with permissions
 */
export const isUsernameAdmin = (_username: string): boolean => {
  // This would need to be called with actual user data from the database
  // For now, return false as we need the full user object with permissions
  return false;
};