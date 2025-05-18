import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Plus, ArrowRight, Layers, Activity } from 'lucide-react';
import useStore from '../stores/useStore';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../components/ui/dialog';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { useGraphActions } from '../utils/graphActions';
import IntegrationSelector from '@/components/IntegrationSelector';
import IconWrapper from '../components/ui/IconWrapper';
import { getToolsData } from '../utils/toolUtils';

const HomePage = () => {
  const { workflows, setSelectedWorkflow, updateFlowStructure, toggleDebugMode } = useStore();
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

  // Generate a unique but subtle pattern for each workflow
  const getWorkflowPattern = (workflowId: string) => {
    const patterns = [
      'border-l-4 border-gray-900',
      'border-t-4 border-gray-900',
      'border-r-4 border-gray-900',
      'border-b-4 border-gray-900'
    ];
    
    const index = workflowId.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0) % patterns.length;
    return patterns[index];
  };

  const renderStepContent = () => {
    switch (creationStep) {
      case 1:
        return (
          <div className="space-y-4">
            <div>
              <Label htmlFor="workflow-name" className="text-base font-medium">Let's name your workflow</Label>
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
              <Label htmlFor="workflow-description" className="text-base font-medium">Describe what this workflow should do (optional)</Label>
              <Textarea
                id="workflow-description"
                value={workflowDescription}
                onChange={(e) => setWorkflowDescription(e.target.value)}
                placeholder="This workflow connects to Slack and Gmail to automatically send notifications when..."
                className="mt-2 min-h-[120px]"
              />
              <p className="text-sm text-gray-500 mt-1">
                A clear description helps the AI understand your workflow's requirements.
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
              <IntegrationSelector 
                selectedIntegrations={selectedIntegrations}
                onToggleIntegration={toggleIntegration}
                maxHeight="180px"
              />
            </div>
          </div>
        );
      default:
        return null;
    }
  };

  // Render a card for creating a new workflow
  const renderCreateWorkflowCard = () => (
    <Card 
      className="overflow-hidden shadow-sm hover:shadow-md transition-all cursor-pointer border border-dashed border-gray-300 bg-white group hover:border-blue-400"
      onClick={openCreateWorkflowDialog}
    >
      <div className="p-6 h-full flex flex-col items-center justify-center text-center">
        <div className="w-12 h-12 rounded-full bg-blue-50 flex items-center justify-center mb-3 group-hover:bg-blue-100 transition-colors">
          <Plus className="h-6 w-6 text-blue-600" />
        </div>
        <h3 className="font-semibold text-lg text-gray-900 mb-1">Create Workflow</h3>
        <p className="text-sm text-gray-500">Start building a new automated workflow</p>
      </div>
    </Card>
  );

  return (
    <div className="w-full h-full pt-16 px-8 pb-8 overflow-y-auto bg-white">
      <div className="max-w-[1800px] mx-auto mt-6">
        <div className="flex justify-between items-center mb-8 p-4 bg-gray-800 rounded-md">
          <h2 className="text-3xl font-bold text-white">Workflows</h2>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {Object.entries(workflows).length > 0 ? (
            <>
              {Object.entries(workflows).map(([workflowId]) => {
                const pattern = getWorkflowPattern(workflowId);
                const nodeCount = workflows[workflowId].nodes?.length || 0;
                const edgeCount = workflows[workflowId].edges?.length || 0;
                
                return (
                  <Card 
                    key={workflowId} 
                    className={`overflow-hidden shadow-sm hover:shadow-md transition-all cursor-pointer border border-gray-200 bg-white group ${pattern}`}
                    onClick={() => handleWorkflowSelect(workflowId)}
                  >
                    <div className="p-6">
                      <div className="mb-4">
                        <div className="text-xs uppercase text-gray-500 font-medium mb-1">Workflow Name</div>
                        <div className="flex items-center justify-between">
                          <h3 className="font-semibold text-lg text-gray-900">{workflowId}</h3>
                          <div className="text-xs font-medium text-gray-800 bg-gray-100 px-2 py-1 rounded-full">Flow</div>
                        </div>
                      </div>
                      
                      <div className="mb-4">
                        <div className="text-xs uppercase text-gray-500 font-medium mb-1">Structure</div>
                        <div className="flex gap-4 p-3 bg-gray-50 border border-gray-100 rounded-md">
                          <div className="flex items-center text-sm text-gray-700">
                            <Layers className="h-4 w-4 mr-1 text-gray-500" />
                            <span>{nodeCount} node{nodeCount !== 1 ? 's' : ''}</span>
                          </div>
                          <div className="flex items-center text-sm text-gray-700">
                            <Activity className="h-4 w-4 mr-1 text-gray-500" />
                            <span>{edgeCount} connection{edgeCount !== 1 ? 's' : ''}</span>
                          </div>
                        </div>
                      </div>
                      
                      <div>
                        <div className="text-xs uppercase text-gray-500 font-medium mb-1">Integrations</div>
                        {workflows[workflowId].tools && workflows[workflowId].tools.length > 0 ? (
                          <div className="flex flex-wrap gap-2">
                            {getToolsData(workflows[workflowId].tools).map(tool => (
                              <IconWrapper key={tool.name} name={tool.name || ''} icon={tool.icon || ''} color={tool.color || ''} size="sm" />
                            ))}
                          </div>
                        ) : (
                          <div className="text-sm text-gray-500 italic p-2 bg-gray-50 border border-gray-100 rounded-md">
                            No integrations
                          </div>
                        )}
                      </div>
                    </div>
                  </Card>
                );
              })}
              {renderCreateWorkflowCard()}
            </>
          ) : (
            <div className="col-span-full text-center py-20 border border-dashed border-gray-300 rounded-lg bg-gray-50">
              <div className="inline-flex items-center justify-center w-16 h-16 mb-4 rounded-full bg-gray-100 border border-gray-200">
                <Activity className="h-8 w-8 text-gray-600" />
              </div>
              <h3 className="text-2xl font-medium text-gray-800 mb-2">No workflows yet</h3>
              <p className="text-gray-600 mb-6">Create your first workflow to get started</p>
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
        <DialogContent className="bg-white max-w-xl border border-gray-300">
          <DialogHeader className="border-b border-gray-200 pb-2">
            <DialogTitle className="text-xl text-gray-900">
              {isCreating ? 'Creating workflow...' : 'Create New Workflow'}
            </DialogTitle>
          </DialogHeader>
          
          <div className="py-4">
            {isCreating ? (
              <div className="flex flex-col items-center justify-center py-6">
                <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-gray-900 mb-4"></div>
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
                      className="border-gray-300 hover:bg-gray-100"
                    >
                      Back
                    </Button>
                  ) : (
                    <Button 
                      variant="outline" 
                      onClick={() => setNewWorkflowDialogOpen(false)}
                      className="border-gray-300 hover:bg-gray-100"
                    >
                      Cancel
                    </Button>
                  )}
                  
                  <Button 
                    onClick={nextStep}
                    className="bg-gray-900 hover:bg-gray-800 text-white"
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
                            ? 'bg-gray-900' 
                            : step < creationStep 
                              ? 'bg-gray-600'
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