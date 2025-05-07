import React, { useState } from 'react';
import { Button } from './ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from './ui/dialog';
import useStore from '../stores/useStore';
import { authenticateIntegration } from '@/utils/debugActions';
import { Loader2 } from 'lucide-react';
import { getToolsData, capitalizeToolName } from '@/utils/toolUtils';
import IconWrapper from './ui/IconWrapper';

interface IntegrationsPanelProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const IntegrationsPanel: React.FC<IntegrationsPanelProps> = ({
  open, 
  onOpenChange,
}) => {
  const { tools, authenticatedTools, setAuthenticatedTools } = useStore();
  const [loadingTool, setLoadingTool] = useState<string | null>(null);
  const toolsData = getToolsData(tools);

  const handleIntegrationClick = async (tool: string) => {
    try {
      setLoadingTool(tool);
      const response = await authenticateIntegration(tool);
      if (response.data) {
        setAuthenticatedTools([...authenticatedTools, tool]);
      }
    } finally {
      setLoadingTool(null);
    }
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
          
          <div className="grid grid-cols-1 gap-3 mt-2">
            {toolsData.map((tool) => {
              const toolName = tool.name || '';
              const displayName = capitalizeToolName(toolName);
              const isAuthenticated = authenticatedTools.includes(toolName);
              
              return (
                <div 
                  key={toolName}
                  className="flex items-center justify-between p-4 rounded-md border border-gray-300"
                >
                  <div className="flex items-center">
                    <div className="mr-3">
                      <IconWrapper 
                        name={toolName}
                        icon={tool.icon}
                        color={tool.color}
                        size="md"
                      />
                    </div>
                    <div>
                      <div className="font-medium">{displayName}</div>
                      <div className="text-xs text-gray-500">
                        {isAuthenticated ? 'Connected' : 'Not connected'}
                      </div>
                    </div>
                  </div>
                  
                  <Button 
                    variant={isAuthenticated ? "outline" : "default"}
                    className={isAuthenticated ? "border-gray-300" : "bg-blue-600 hover:bg-blue-700 text-white"}
                    onClick={() => handleIntegrationClick(toolName)}
                    disabled={loadingTool === toolName || isAuthenticated}
                  >
                    {loadingTool === toolName ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin" />
                        {isAuthenticated ? 'Processing...' : 'Connecting...'}
                      </>
                    ) : (
                      isAuthenticated ? 'Connected' : 'Connect'
                    )}
                  </Button>
                </div>
              );
            })}
          </div>
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