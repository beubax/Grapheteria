import React from 'react';
import { getToolInitial, getContrastColor } from '@/utils/toolUtils';

interface IconWrapperProps {
  name: string;
  icon?: string;
  color: string;
  size?: 'sm' | 'md' | 'lg';
}

/**
 * IconWrapper component for displaying tool icons consistently
 * Handles both SVG icons and initials fallback with consistent sizing
 */
const IconWrapper: React.FC<IconWrapperProps> = ({ 
  name, 
  icon, 
  color, 
  size = 'md' 
}) => {
  const initial = getToolInitial(name);
  const textColor = getContrastColor(color);
  
  // Size mappings
  const sizeClasses = {
    sm: {
      wrapper: 'w-8 h-8',
      text: 'text-base'
    },
    md: {
      wrapper: 'w-10 h-10',
      text: 'text-lg'
    },
    lg: {
      wrapper: 'w-12 h-12',
      text: 'text-xl'
    }
  };
  
  const { wrapper, text } = sizeClasses[size];
  
  return (
    <>
      {icon ? (
        <div className={`${wrapper} relative flex items-center justify-center`}>
          <img 
            src={icon} 
            alt={`${name} icon`}
            className="max-w-full max-h-full object-contain"
            style={{ width: '70%', height: '70%' }}
          />
        </div>
      ) : (
        <div 
          className={`${wrapper} rounded-full flex items-center justify-center ${text} font-medium`}
          style={{ 
            backgroundColor: color,
            color: textColor
          }}
        >
          {initial}
        </div>
      )}
    </>
  );
};

export default IconWrapper; 