/**
 * Generate distinct colors using golden ratio for better variety
 * This replaces the old (index * 137.5) % 360 approach
 */
export const generateScriptColor = (index: number): string => {
  const goldenRatioConjugate = 0.618033988749895;
  const hue = (index * goldenRatioConjugate * 360) % 360;
  
  // Vary saturation and lightness slightly for more visual variety
  const saturation = 65 + (index % 3) * 10; // 65%, 75%, 85%
  const lightness = 45 + (index % 2) * 10;  // 45%, 55%
  
  return `hsl(${hue}, ${saturation}%, ${lightness}%)`;
};

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