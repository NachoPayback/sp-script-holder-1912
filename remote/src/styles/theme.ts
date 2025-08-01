export const theme = {
  colors: {
    primary: '#3b82f6',
    background: '#0a0b1e',
    surface: '#1e293b',
    surfaceLight: 'rgba(30, 41, 59, 0.5)',
    text: '#e1e8ed',
    textSecondary: '#94a3b8',
    textDim: 'rgba(148, 163, 184, 0.2)',
    success: '#10b981',
    error: '#ef4444',
    warning: '#f59e0b',
    border: 'rgba(148, 163, 184, 0.1)',
    glow: 'rgba(59, 130, 246, 0.3)',
  },
  spacing: {
    xs: '4px',
    sm: '8px',
    md: '16px',
    lg: '24px',
    xl: '32px',
    xxl: '40px',
  },
  borderRadius: {
    sm: '6px',
    md: '12px',
    lg: '16px',
    xl: '20px',
  },
  button: {
    size: 180,
    borderWidth: 3,
    padding: 20,
  },
  fonts: {
    family: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
    weights: {
      normal: 500,
      medium: 600,
      bold: 700,
      extraBold: 800,
    },
  },
  animations: {
    fast: '0.15s',
    normal: '0.3s',
    slow: '0.5s',
    easing: 'cubic-bezier(0.4, 0, 0.2, 1)',
  },
  breakpoints: {
    mobile: '450px',
    tablet: '650px',
    desktop: '900px',
  },
} as const;

export type Theme = typeof theme;