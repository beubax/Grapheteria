import React, { useState } from 'react';
import { Button } from './ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from './ui/dialog';
import IntegrationSelector from './IntegrationSelector';

interface IntegrationsPanelProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const IntegrationsPanel: React.FC<IntegrationsPanelProps> = ({
  open, 
  onOpenChange,
}) => {
  const [selectedIntegrations, setSelectedIntegrations] = useState<string[]>([]);

  const handleToggleIntegration = (integrationId: string) => {
    setSelectedIntegrations(prev => 
      prev.includes(integrationId) 
        ? prev.filter(id => id !== integrationId)
        : [...prev, integrationId]
    );
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="bg-white max-w-xl">
        <DialogHeader>
          <DialogTitle>Manage Integrations</DialogTitle>
        </DialogHeader>
        <div className="py-4">
          <p className="text-sm text-gray-500 mb-4">
            Connect to third-party services to use them in your workflows.
          </p>
          
          <IntegrationSelector 
            selectedIntegrations={selectedIntegrations}
            onToggleIntegration={handleToggleIntegration}
            selectionMode={false}
          />
        </div>
        <DialogFooter>
          <Button 
            onClick={() => onOpenChange(false)}
            className="bg-blue-600 hover:bg-blue-700 text-white"
          >
            Done
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default IntegrationsPanel; 