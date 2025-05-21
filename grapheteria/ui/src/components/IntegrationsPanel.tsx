import React from 'react';
import { MCPConnectionManager } from './MCPConnectionManager';

interface IntegrationsPanelProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const IntegrationsPanel: React.FC<IntegrationsPanelProps> = ({
  open, 
  onOpenChange,
}) => {
  return (
    <MCPConnectionManager open={open} onOpenChange={onOpenChange} />
  );
};

export default IntegrationsPanel; 