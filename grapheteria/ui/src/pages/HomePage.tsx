import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Plus, ArrowRight } from 'lucide-react';
import useStore from '../stores/useStore';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../components/ui/dialog';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { useGraphActions } from '../utils/graphActions';
import { getToolsData, capitalizeToolName } from '@/utils/toolUtils';
import IconWrapper from '@/components/ui/IconWrapper';

const HomePage = () => {
  const { workflows, setSelectedWorkflow, updateFlowStructure, toggleDebugMode, tools, authenticatedTools } = useStore();
  const { onCreateWorkflow } = useGraphActions();
  const navigate = useNavigate();

  const [newWorkflowDialogOpen, setNewWorkflowDialogOpen] = useState(false);
  const [newWorkflowName, setNewWorkflowName] = useState('');
  const [workflowDescription, setWorkflowDescription] = useState('');
  const [nameError, setNameError] = useState('');
  const [selectedIntegrations, setSelectedIntegrations] = useState<string[]>([]);
  const [creationStep, setCreationStep] = useState(1);
  const [isCreating, setIsCreating] = useState(false);

  // Reset selected workflow when HomePage mounts
  useEffect(() => {
    // Clear selected workflow
    setSelectedWorkflow(null);
    // Update flow structure to reflect no selection
    updateFlowStructure();
    // Close any open debug drawer
    toggleDebugMode(false);
  }, [setSelectedWorkflow, updateFlowStructure, toggleDebugMode]);

  // Toggle integration selection
  const toggleIntegration = (integrationId: string) => {
    setSelectedIntegrations(prev => 
      prev.includes(integrationId) 
        ? prev.filter(id => id !== integrationId)
        : [...prev, integrationId]
    );
  };

  const handleWorkflowSelect = (workflowId: string) => {
    // Close debug drawer when switching workflows
    setSelectedWorkflow(workflowId);
    updateFlowStructure();
    navigate(`/flow/${workflowId}`);
  };

  const openCreateWorkflowDialog = () => {
    setNewWorkflowName('');
    setWorkflowDescription('');
    setNameError('');
    setSelectedIntegrations([]);
    setCreationStep(1);
    setIsCreating(false);
    setNewWorkflowDialogOpen(true);
  };

  const validateWorkflowName = () => {
    if (!newWorkflowName.trim()) {
      setNameError('Workflow name cannot be empty');
      return false;
    }
    
    if (newWorkflowName.includes(' ')) {
      setNameError('Workflow name cannot contain spaces');
      return false;
    }
    
    // Check if workflow name already exists
    if (Object.keys(workflows).includes(newWorkflowName)) {
      setNameError('Workflow name already exists');
      return false;
    }

    return true;
  };

  const nextStep = () => {
    if (creationStep === 1) {
      if (!validateWorkflowName()) return;
      setCreationStep(2);
    } else if (creationStep === 2) {
      setCreationStep(3);
    } else {
      handleCreateWorkflow();
    }
  };

  const prevStep = () => {
    if (creationStep > 1) {
      setCreationStep(creationStep - 1);
    }
  };

  const handleCreateWorkflow = () => {
    if (!validateWorkflowName()) return;
    
    // Save workflow name for later use
    const workflowNameToCreate = newWorkflowName;
    const workflowDescriptionToCreate = workflowDescription;
    const selectedIntegrationsToCreate = selectedIntegrations;
    
    // Create the workflow
    onCreateWorkflow(workflowNameToCreate, workflowDescriptionToCreate, selectedIntegrationsToCreate);
    
    // Close dialog
    setNewWorkflowDialogOpen(false);
    
    // Navigate immediately to the flow page without waiting for confirmation
    navigate(`/flow/${workflowNameToCreate.replace(" ", "_").toLowerCase()}`);
  };

  const renderStepContent = () => {
    switch (creationStep) {
      case 1:
        return (
          <div className="space-y-4">
            <div>
              <Label htmlFor="workflow-name" className="text-base font-medium">What flow would you like to create?</Label>
              <Input
                id="workflow-name"
                value={newWorkflowName}
                onChange={(e) => {
                  setNewWorkflowName(e.target.value);
                  setNameError('');
                }}
                placeholder="my_new_workflow"
                className="mt-2"
              />
              {nameError && (
                <p className="text-sm text-red-500 mt-1">{nameError}</p>
              )}
              <p className="text-sm text-gray-500 mt-1">
                Workflow name must not contain spaces.
              </p>
            </div>
          </div>
        );
      case 2:
        return (
          <div className="space-y-4">
            <div>
              <Label htmlFor="workflow-description" className="text-base font-medium">Describe what this workflow should do</Label>
              <Textarea
                id="workflow-description"
                value={workflowDescription}
                onChange={(e) => setWorkflowDescription(e.target.value)}
                placeholder="This workflow connects to Slack and Gmail to automatically send notifications when..."
                className="mt-2 min-h-[120px]"
              />
              <p className="text-sm text-gray-500 mt-1">
                A clear description helps you and others understand the workflow's purpose.
              </p>
            </div>
          </div>
        );
      case 3:
        return (
          <div className="space-y-4">
            <div>
              <Label className="text-base font-medium block mb-2">Select Integrations (Optional)</Label>
              <p className="text-sm text-gray-500 mb-3">
                Connect services that this workflow will interact with. You can add more later.
              </p>
              <div className="grid grid-cols-2 gap-3 mt-2 max-h-[300px] overflow-y-auto pr-2">
                {tools.map((tool) => {
                  const isAuthenticated = authenticatedTools.includes(tool);
                  const isSelected = selectedIntegrations.includes(tool);
                  const toolData = getToolsData([tool])[0];
                  const displayName = capitalizeToolName(tool);
                  
                  return (
                    <div 
                      key={tool}
                      onClick={() => isAuthenticated && toggleIntegration(tool)}
                      className={`
                        flex items-center p-3 rounded-md border cursor-pointer
                        ${isAuthenticated ? 'border-gray-300 hover:border-blue-500' : 'border-gray-200 bg-gray-50 opacity-60 cursor-not-allowed'}
                        ${isSelected ? 'border-blue-500 bg-blue-50' : ''}
                      `}
                    >
                      <div className="mr-2">
                        <IconWrapper 
                          name={tool}
                          icon={toolData.icon}
                          color={toolData.color}
                          size="sm"
                        />
                      </div>
                      <div>
                        <div className="font-medium">{displayName}</div>
                        <div className="text-xs text-gray-500">
                          {isAuthenticated ? 'Authenticated' : 'Not authenticated'}
                        </div>
                      </div>
                      {isSelected && (
                        <div className="ml-auto text-blue-500">✓</div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div className="w-full h-full pt-16 px-8 pb-8 overflow-y-auto bg-gray-50">
      <div className="max-w-[1800px] mx-auto mt-6">
        <div className="flex justify-between items-center mb-8">
          <h2 className="text-3xl font-bold">My Workflows</h2>
          <Button 
            onClick={openCreateWorkflowDialog}
            className="bg-blue-600 hover:bg-blue-700 text-white"
          >
            <Plus className="h-4 w-4 mr-2" />
            Create Workflow
          </Button>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {Object.entries(workflows).length > 0 ? (
            Object.entries(workflows).map(([workflowId]) => (
              <Card 
                key={workflowId} 
                className="p-6 hover:shadow-lg transition-all cursor-pointer border border-gray-200 bg-white"
                onClick={() => handleWorkflowSelect(workflowId)}
              >
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-medium text-lg">{workflowId}</h3>
                  <div className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded-full">Flow</div>
                </div>
                <div className="text-sm text-gray-600 mb-4">
                  {workflows[workflowId].nodes?.length || 0} nodes · {workflows[workflowId].edges?.length || 0} connections
                </div>
                <div className="flex flex-wrap gap-1 mt-auto">
                </div>
              </Card>
            ))
          ) : (
            <div className="col-span-full text-center py-20">
              <div className="text-6xl mb-4">🚀</div>
              <h3 className="text-2xl font-medium text-gray-700 mb-2">No workflows yet</h3>
              <p className="text-gray-500 mb-6">Create your first workflow to get started</p>
              <Button 
                onClick={openCreateWorkflowDialog}
                className="bg-blue-600 hover:bg-blue-700 text-white px-6"
              >
                <Plus className="h-4 w-4 mr-2" />
                Create Your First Workflow
              </Button>
            </div>
          )}
        </div>
      </div>

      {/* New Workflow Dialog */}
      <Dialog 
        open={newWorkflowDialogOpen} 
        onOpenChange={(open) => {
          if (!open && !isCreating) {
            setNewWorkflowDialogOpen(false);
          }
        }}
      >
        <DialogContent className="bg-white max-w-xl">
          <DialogHeader>
            <DialogTitle className="text-xl">
              {isCreating ? 'Creating workflow...' : 'Create New Workflow'}
            </DialogTitle>
          </DialogHeader>
          
          <div className="py-4">
            {isCreating ? (
              <div className="flex flex-col items-center justify-center py-6">
                <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-600 mb-4"></div>
                <p className="text-gray-600">Creating your workflow...</p>
              </div>
            ) : (
              <>
                {renderStepContent()}
                
                <div className="flex justify-between mt-8">
                  {creationStep > 1 ? (
                    <Button 
                      variant="outline" 
                      onClick={prevStep}
                      className="hover:bg-gray-100"
                    >
                      Back
                    </Button>
                  ) : (
                    <Button 
                      variant="outline" 
                      onClick={() => setNewWorkflowDialogOpen(false)}
                      className="hover:bg-gray-100"
                    >
                      Cancel
                    </Button>
                  )}
                  
                  <Button 
                    onClick={nextStep}
                    className="bg-blue-600 hover:bg-blue-700 text-white"
                    disabled={creationStep === 1 && !newWorkflowName.trim()}
                  >
                    {creationStep === 3 ? 'Create Workflow' : 'Next'}
                    {creationStep !== 3 && <ArrowRight className="h-4 w-4 ml-2" />}
                  </Button>
                </div>
                
                <div className="flex justify-center mt-4">
                  <div className="flex gap-2">
                    {[1, 2, 3].map((step) => (
                      <div 
                        key={step}
                        className={`w-2 h-2 rounded-full ${
                          step === creationStep 
                            ? 'bg-blue-600' 
                            : step < creationStep 
                              ? 'bg-blue-300'
                              : 'bg-gray-300'
                        }`}
                      />
                    ))}
                  </div>
                </div>
              </>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default HomePage; 