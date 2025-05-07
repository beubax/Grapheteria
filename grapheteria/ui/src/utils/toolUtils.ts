import { Tool } from '../types/types';

// Predefined colors for tool icons
const TOOL_COLORS: Record<string, string> = {
  gmail: '#DB4437',
  slack: '#4A154B',
  github: '#24292e',
  dropbox: '#0061FF',
  twitter: '#1DA1F2',
  zoom: '#2D8CFF',
  google: '#4285F4',
  microsoft: '#00A4EF',
  // Add more tools with their brand colors as needed
};

// Default color for tools without a predefined color
const DEFAULT_COLOR = '#6366F1';

/**
 * Get a list of tool data with names, colors, and icons
 * @param toolNames Array of tool names
 * @returns Array of Tool objects with name, color, and initial
 */
export const getToolsData = (toolNames: string[]): Tool[] => {
  return toolNames.map(name => ({
    name,
    color: TOOL_COLORS[name.toLowerCase()] || DEFAULT_COLOR,
    icon: `/icons/${name.toLowerCase()}.svg`,
  }));
};

/**
 * Get the initial letter of a tool name
 * @param name Tool name
 * @returns The first character of the tool name
 */
export const getToolInitial = (name: string): string => {
  return name.charAt(0).toUpperCase();
};

/**
 * Capitalize the first letter of a tool name
 * @param name Tool name
 * @returns Tool name with first letter capitalized
 */
export const capitalizeToolName = (name: string): string => {
  if (!name || name.length === 0) return '';
  return name.charAt(0).toUpperCase() + name.slice(1);
};

/**
 * Get contrasting text color (black or white) based on background color
 * @param hexColor Hex color code
 * @returns 'white' or 'black' for best contrast
 */
export const getContrastColor = (hexColor: string): string => {
  // Remove the hash if it exists
  const color = hexColor.startsWith('#') ? hexColor.slice(1) : hexColor;
  
  // Convert to RGB
  const r = parseInt(color.slice(0, 2), 16);
  const g = parseInt(color.slice(2, 4), 16);
  const b = parseInt(color.slice(4, 6), 16);
  
  // Calculate luminance - W3C recommendation
  const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
  
  // Return black for bright colors, white for dark colors
  return luminance > 0.5 ? 'black' : 'white';
}; 