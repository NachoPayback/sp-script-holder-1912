/**
 * User-specific color coding for SP Crew members
 */

export const getUserColor = (username: string): string => {
  const cleanUsername = username.toLowerCase().trim();
  
  switch (cleanUsername) {
    case 'nachopayback':
      return '#40E0D0'; // Mint/Teal
    case 'danielpayback':
      return '#FFD700'; // Yellow
    case 'cenapayback':
      return '#E5E5E5'; // White/Gray
    case 'brandonpayback':
      return '#FF8C00'; // Orange
    case 'pierogi':
      return '#00BFFF'; // Electric Blue
    case 'sevenpayback':
      return '#8A2BE2'; // Purple
    case 'nightpayback':
      return '#4B0082'; // Indigo
    case 'mazepayback':
      return '#FF1493'; // Hot Pink
    default:
      return '#60a5fa'; // Default blue for unknown users
  }
};

export const getUserDisplayName = (username: string): string => {
  // Return the original username for display
  return username;
};