/**
 * Generate distinct colors using golden ratio for better variety
 * Returns hex colors for better CSS filter compatibility
 */
export const generateScriptColor = (index: number): string => {
  const goldenRatioConjugate = 0.618033988749895;
  const hue = (index * goldenRatioConjugate * 360) % 360;
  
  // Vary saturation and lightness for better glow visibility
  const saturation = 85 + (index % 3) * 5; // 85%, 90%, 95%
  const lightness = 60 + (index % 2) * 5;  // 60%, 65%
  
  // Convert HSL to RGB then to hex for better filter support
  return hslToHex(hue, saturation, lightness);
};

/**
 * Convert HSL to hex color for better CSS filter compatibility
 */
function hslToHex(h: number, s: number, l: number): string {
  l /= 100;
  const a = s * Math.min(l, 1 - l) / 100;
  const f = (n: number) => {
    const k = (n + h / 30) % 12;
    const color = l - a * Math.max(Math.min(k - 3, 9 - k, 1), -1);
    return Math.round(255 * color).toString(16).padStart(2, '0');
  };
  return `#${f(0)}${f(8)}${f(4)}`;
}

/**
 * Convert color to various formats
 */
export const colorUtils = {
  addAlpha: (color: string, alpha: number): string => {
    // Convert HSL to HSLA
    if (color.startsWith('hsl(')) {
      return color.replace('hsl(', 'hsla(').replace(')', `, ${alpha})`);
    }
    return color;
  },
  
  toRgba: (color: string, alpha: number): string => {
    // Simple helper for common cases
    if (color === '#3b82f6') return `rgba(59, 130, 246, ${alpha})`;
    if (color === '#10b981') return `rgba(16, 185, 129, ${alpha})`;
    if (color === '#ef4444') return `rgba(239, 68, 68, ${alpha})`;
    return colorUtils.addAlpha(color, alpha);
  }
};