export const theme = {
  colors: {
    // SP Crew signature electric blue theme
    primary: '#0080FF',        // SP electric blue
    primaryDark: '#0066CC',    // Deeper electric blue
    primaryLight: '#00A2FF',   // Lighter electric blue
    background: '#000000',     // Pure black
    surface: '#0A0A0A',        // Near black surface
    surfaceLight: '#141414',   // Slightly elevated surface
    surfaceHover: '#1A1A1A',   // Hover state surface
    text: '#FFFFFF',           // Pure white text
    textSecondary: '#B0B0B0',  // Secondary gray text
    textDim: '#666666',        // Dimmed text
    border: '#1A1A1A',         // Subtle borders
    borderLight: '#2A2A2A',    // More visible borders
    borderHover: '#0080FF20',  // Blue tinted border on hover
    success: '#00D67A',        // Tech green
    error: '#FF3366',          // Tech red
    warning: '#FFB800',        // Tech amber
    glow: 'rgba(0, 128, 255, 0.15)', // Subtle blue glow
    glowStrong: 'rgba(0, 128, 255, 0.3)', // Stronger glow for active states
  },
  gradients: {
    electric: 'linear-gradient(135deg, #0080FF 0%, #00A2FF 100%)',
    electricReverse: 'linear-gradient(135deg, #00A2FF 0%, #0080FF 100%)',
    dark: 'linear-gradient(180deg, #0A0A0A 0%, #000000 100%)',
    surface: 'linear-gradient(135deg, #141414 0%, #0A0A0A 100%)',
  },
  shadows: {
    sm: '0 2px 8px rgba(0, 0, 0, 0.8)',
    md: '0 4px 16px rgba(0, 0, 0, 0.8)',
    lg: '0 8px 32px rgba(0, 0, 0, 0.8)',
    glow: '0 0 20px rgba(0, 128, 255, 0.2)',
    glowStrong: '0 0 40px rgba(0, 128, 255, 0.4)',
  },
  spacing: {
    xs: '4px',
    sm: '8px',
    md: '16px',
    lg: '24px',
    xl: '32px',
    xxl: '48px',
    xxxl: '64px',
  },
  borderRadius: {
    sm: '4px',
    md: '8px',
    lg: '12px',
    xl: '16px',
    xxl: '24px',
    hex: '20%', // For hexagon-inspired corners
  },
  button: {
    size: 180,  // Reduced from 220
    borderWidth: 8,
    padding: 20,
  },
  fonts: {
    // Headers and display text
    display: "'Gridnik', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
    // Body and UI text
    family: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
    // Code and monospace
    mono: "'JetBrains Mono', 'SF Mono', 'Monaco', 'Consolas', monospace",
    weights: {
      light: 300,
      normal: 400,
      medium: 500,
      semibold: 600,
      bold: 700,
      extraBold: 800,
      black: 900,
    },
  },
  animations: {
    instant: '0.1s',
    fast: '0.2s',
    normal: '0.3s',
    slow: '0.5s',
    verySlow: '0.8s',
    easing: 'cubic-bezier(0.4, 0, 0.2, 1)',
    bounce: 'cubic-bezier(0.68, -0.55, 0.265, 1.55)',
  },
  breakpoints: {
    mobile: '450px',
    tablet: '650px',
    desktop: '900px',
    wide: '1200px',
  },
} as const;

export type Theme = typeof theme;