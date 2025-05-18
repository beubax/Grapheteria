import React, { useState } from 'react';
import { Button } from './ui/button';
import { Loader2 } from 'lucide-react';
import useStore from '../stores/useStore';
import { authenticateIntegration } from '@/utils/debugActions';
import { getToolsData, capitalizeToolName } from '@/utils/toolUtils';
import IconWrapper from './ui/IconWrapper';
import { Input } from './ui/input';

interface IntegrationSelectorProps {
  selectedIntegrations: string[];
  onToggleIntegration: (integrationId: string) => void;
  showAuthenticated?: boolean;
  showUnauthenticated?: boolean;
  selectionMode?: boolean;
  maxHeight?: string;
}

const IntegrationSelector: React.FC<IntegrationSelectorProps> = ({
  selectedIntegrations,
  onToggleIntegration,
  showAuthenticated = true,
  showUnauthenticated = true,
  selectionMode = true,
  maxHeight = "min(60vh,500px)",
}) => {
  const { tools, authenticatedTools, setAuthenticatedTools } = useStore();
  const [loadingTool, setLoadingTool] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  
  // Get all tools data
  const toolsData = getToolsData(tools);
  
  // Filter tools based on search query
  const filteredTools = toolsData.filter(tool => 
    capitalizeToolName(tool.name || '').toLowerCase().includes(searchQuery.toLowerCase())
  );
  
  // Separate authenticated and unauthenticated tools
  const authenticatedToolsData = filteredTools.filter(tool => 
    authenticatedTools.includes(tool.name || '')
  );
  
  const unauthenticatedToolsData = filteredTools.filter(tool => 
    !authenticatedTools.includes(tool.name || '')
  );

  const handleConnectClick = async (tool: string) => {
    try {
      setLoadingTool(tool);
      const response = await authenticateIntegration(tool);
      if (response.data) {
        setAuthenticatedTools([...authenticatedTools, tool]);
        // Automatically select the newly authenticated tool if in selection mode
        if (selectionMode) {
          onToggleIntegration(tool);
        }
      }
    } finally {
      setLoadingTool(null);
    }
  };

  // Render a single tool item
  const renderToolItem = (tool: any, isAuthenticated: boolean) => {
    const toolName = tool.name || '';
    const displayName = capitalizeToolName(toolName);
    const isSelected = selectedIntegrations.includes(toolName);
    
    return (
      <div 
        key={toolName}
        onClick={() => isAuthenticated && selectionMode && onToggleIntegration(toolName)}
        className={`
          flex flex-col p-2 rounded-md border 
          ${isAuthenticated 
            ? selectionMode 
              ? 'cursor-pointer border-gray-300 hover:border-blue-500' 
              : 'border-gray-300'
            : 'border-gray-200 bg-gray-50 opacity-80 cursor-default'
          }
          ${isSelected && isAuthenticated ? 'border-blue-500 bg-blue-50' : ''}
          ${isAuthenticated ? 'min-h-[60px]' : 'min-h-[75px]'}
        `}
      >
        <div className="flex items-center mb-1">
          <div className="flex-shrink-0 mr-2">
            <IconWrapper 
              name={toolName}
              icon={tool.icon}
              color={tool.color}
              size="sm"
            />
          </div>
          <div className="min-w-0 flex-1">
            <div className="font-medium truncate">{displayName}</div>
            {isAuthenticated && (
              <div className="text-xs text-gray-500">
                Connected
              </div>
            )}
          </div>
          {isAuthenticated && isSelected && selectionMode && (
            <div className="ml-2 text-blue-500 flex-shrink-0">✓</div>
          )}
        </div>
        
        {!isAuthenticated && (
          <div className="mt-auto flex justify-center">
            <Button 
              variant="default"
              size="sm"
              className="bg-blue-600 hover:bg-blue-700 text-white h-6 text-xs py-0 px-10"
              onClick={(e) => {
                e.stopPropagation();
                handleConnectClick(toolName);
              }}
              disabled={loadingTool === toolName}
            >
              {loadingTool === toolName ? (
                <>
                  <Loader2 className="h-3 w-3 animate-spin mr-1" />
                  Connecting...
                </>
              ) : (
                'Connect'
              )}
            </Button>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="space-y-2 w-full">
      <Input
        value={searchQuery}
        onChange={(e) => setSearchQuery(e.target.value)}
        placeholder="Search integrations..."
        className="mb-2 h-8 text-sm"
      />
      
      {/* Show authenticated tools section */}
      {showAuthenticated && authenticatedToolsData.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-gray-700">Connected Integrations</h4>
          <div className="grid grid-cols-2 gap-2 overflow-y-auto overflow-x-hidden pr-3 w-full" style={{ maxHeight: '200px' }}>
            {authenticatedToolsData.map(tool => renderToolItem(tool, true))}
          </div>
        </div>
      )}
      
      {/* Show unauthenticated tools section */}
      {showUnauthenticated && unauthenticatedToolsData.length > 0 && (
        <div className="space-y-2 mt-3">
          <h4 className="text-sm font-medium text-gray-700">Available Integrations</h4>
          <div className="grid grid-cols-2 gap-2 overflow-y-auto overflow-x-hidden pr-3 w-full" style={{ maxHeight }}>
            {unauthenticatedToolsData.map(tool => renderToolItem(tool, false))}
          </div>
        </div>
      )}
      
      {filteredTools.length === 0 && (
        <div className="text-center py-6 text-gray-500">
          No integrations found matching "{searchQuery}"
        </div>
      )}
    </div>
  );
};

export default IntegrationSelector; 