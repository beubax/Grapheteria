"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardHeader, CardTitle, CardFooter } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Trash2, RefreshCw, Edit, Plus, Server, Globe, CheckCircle2, AlertCircle, Loader2, MoreHorizontal } from "lucide-react"
import { Alert, AlertDescription } from "../components/ui/alert"
import { useGraphActions } from '../utils/graphActions'
import useStore from '../stores/useStore'
import { ScrollArea } from "./ui/scroll-area"

interface MCPConnectionManagerProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

interface FormattedMCP {
  name: string
  url: string
  tools: Array<{
    name: string
    description?: string
    icon?: string
  }>
}

export function MCPConnectionManager({ open, onOpenChange }: MCPConnectionManagerProps) {
  const { mcpTools, notificationFlag, setNotificationFlag } = useStore()
  const { onMCPAdd, onMCPRemove, onMCPUpdateURL, onMCPRefresh } = useGraphActions()
  
  const [formattedMCPs, setFormattedMCPs] = useState<FormattedMCP[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [activeDialog, setActiveDialog] = useState<'add' | 'edit' | null>(null)
  const [activeEditMCP, setActiveEditMCP] = useState<FormattedMCP | null>(null)
  const [refreshingMCP, setRefreshingMCP] = useState<string | null>(null)
  const [deletingMCP, setDeletingMCP] = useState<string | null>(null)
  const [waitingForResponse, setWaitingForResponse] = useState(false)
  const [currentOperation, setCurrentOperation] = useState<'add' | 'edit' | 'refresh' | 'delete' | null>(null)
  
  // Form states
  const [newMCPName, setNewMCPName] = useState('')
  const [newMCPUrl, setNewMCPUrl] = useState('')
  const [formError, setFormError] = useState<string | null>(null)

  const [activeToolsMCP, setActiveToolsMCP] = useState<FormattedMCP | null>(null)
  const [showToolsDialog, setShowToolsDialog] = useState(false)

  // Watch for notification flag changes to detect completed operations
  useEffect(() => {
    if (waitingForResponse && notificationFlag) {
      setWaitingForResponse(false)
      setCurrentOperation(null)
      
      // Close dialog only after operation completes successfully
      setActiveDialog(null)
      setNewMCPName('')
      setNewMCPUrl('')
      
      loadMCPs()
    }
  }, [notificationFlag, waitingForResponse])

  useEffect(() => {
    if (open) {
      loadMCPs()
    }
  }, [open, mcpTools])

  const loadMCPs = () => {
    setIsLoading(true)
    setError(null)
    
    try {
      const formatted: FormattedMCP[] = Object.entries(mcpTools).map(([mcpName, [url, toolsList]]) => {
        // Create tool objects from the tool names
        const tools = toolsList.map(toolName => ({
          name: toolName,
          description: "",
          icon: ""
        }))
        
        return {
          name: mcpName,
          url,
          tools
        }
      })
      
      setFormattedMCPs(formatted)
    } catch (err) {
      setError('Failed to load MCP connections')
      console.error('Error formatting MCPs:', err)
    } finally {
      setIsLoading(false)
    }
  }

  const handleAddMCP = () => {
    if (!newMCPName.trim()) {
      setFormError("MCP name is required")
      return
    }
    
    if (!newMCPUrl.trim()) {
      setFormError("MCP URL is required")
      return
    }
    
    setFormError(null)
    setWaitingForResponse(true)
    setCurrentOperation('add')
    setNotificationFlag(false)
    
    try {
      onMCPAdd(newMCPName.trim(), newMCPUrl.trim())
      
      // Don't close dialog until we get response
      setActiveDialog(null)
    } catch (err) {
      setFormError('Failed to add MCP connection')
      console.error('Error adding MCP:', err)
      setWaitingForResponse(false)
      setCurrentOperation(null)
    }
  }

  const handleUpdateMCP = () => {
    if (!activeEditMCP) return
    
    if (!activeEditMCP.name.trim()) {
      setFormError("MCP name is required")
      return
    }
    
    if (!activeEditMCP.url.trim()) {
      setFormError("MCP URL is required")
      return
    }
    
    setFormError(null)
    setWaitingForResponse(true)
    setCurrentOperation('edit')
    setNotificationFlag(false)
    
    try {
      onMCPUpdateURL(activeEditMCP.name, activeEditMCP.url)
      
      setActiveDialog(null)
      setActiveEditMCP(null)
    } catch (err) {
      setFormError('Failed to update MCP URL')
      console.error('Error updating MCP URL:', err)
      setWaitingForResponse(false)
      setCurrentOperation(null)
    }
  }

  const handleRefreshMCP = (mcpName: string) => {
    setRefreshingMCP(mcpName)
    setWaitingForResponse(true)
    setCurrentOperation('refresh')
    setNotificationFlag(false)
    
    try {
      onMCPRefresh(mcpName)
    } catch (err) {
      setError('Failed to refresh MCP tools')
      console.error('Error refreshing MCP tools:', err)
      setWaitingForResponse(false)
      setCurrentOperation(null)
      setRefreshingMCP(null)
    }
  }

  const handleDeleteMCP = (mcpName: string) => {
    setDeletingMCP(mcpName)
    setWaitingForResponse(true)
    setCurrentOperation('delete')
    setNotificationFlag(false)
    
    try {
      onMCPRemove(mcpName)
    } catch (err) {
      setError('Failed to remove MCP connection')
      console.error('Error removing MCP:', err)
      setWaitingForResponse(false)
      setCurrentOperation(null)
      setDeletingMCP(null)
    }
  }

  const handleEditMCP = (mcp: FormattedMCP) => {
    setActiveEditMCP({ ...mcp })
    setActiveDialog('edit')
  }

  const openAddDialog = () => {
    setNewMCPName('')
    setNewMCPUrl('')
    setFormError(null)
    setActiveDialog('add')
  }

  const closeDialog = () => {
    setActiveDialog(null)
    setActiveEditMCP(null)
    setFormError(null)
  }

  const openToolsDialog = (mcp: FormattedMCP) => {
    setActiveToolsMCP(mcp)
    setShowToolsDialog(true)
  }
  
  const closeToolsDialog = () => {
    setShowToolsDialog(false)
    setActiveToolsMCP(null)
  }

  const renderAddEditDialog = () => {
    const isEdit = activeDialog === 'edit'
    const title = isEdit ? 'Edit MCP Connection' : 'Add MCP Connection'
    const buttonText = isEdit ? 'Update' : 'Add'
    const buttonAction = isEdit ? handleUpdateMCP : handleAddMCP
    
    return (
      <Dialog open={activeDialog !== null} onOpenChange={(open) => !open && closeDialog()}>
        <DialogContent className="sm:max-w-[500px] max-h-[80vh] overflow-y-auto bg-white rounded-xl border-4 border-gray-200 shadow-xl">
          <DialogHeader>
            <DialogTitle className="flex items-center text-lg font-bold text-black tracking-wide">
              <Server className="h-5 w-5 text-gray-600 mr-2" />
              {title}
            </DialogTitle>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="mcp-name" className="text-base font-medium">MCP Name</Label>
              <Input
                id="mcp-name"
                value={isEdit ? activeEditMCP?.name || '' : newMCPName}
                onChange={(e) => isEdit 
                  ? setActiveEditMCP((prev) => prev ? {...prev, name: e.target.value} : null) 
                  : setNewMCPName(e.target.value)
                }
                disabled={isEdit} // Don't allow name editing in edit mode
                placeholder="my-mcp-service"
                className="border-2 focus:ring-2 focus:ring-gray-200"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="mcp-url" className="text-base font-medium">MCP URL</Label>
              <Input
                id="mcp-url"
                value={isEdit ? activeEditMCP?.url || '' : newMCPUrl}
                onChange={(e) => isEdit 
                  ? setActiveEditMCP((prev) => prev ? {...prev, url: e.target.value} : null) 
                  : setNewMCPUrl(e.target.value)
                }
                placeholder="http://localhost:8000"
                className="border-2 focus:ring-2 focus:ring-gray-200"
              />
              <p className="text-sm text-gray-500">
                Supports Websockets, FastMCP, Streamable HTTP, SSE or STDIO
              </p>
            </div>

            {formError && (
              <Alert variant="destructive" className="bg-red-50 border-red-200">
                <AlertCircle className="h-4 w-4 text-red-500" />
                <AlertDescription className="text-red-700">
                  {formError}
                </AlertDescription>
              </Alert>
            )}
          </div>

          <DialogFooter>
            <Button 
              variant="outline" 
              onClick={closeDialog} 
              className="border-2 hover:bg-gray-100 transition-all cursor-pointer"
            >
              Cancel
            </Button>
            <Button 
              onClick={buttonAction} 
              className="text-white bg-black hover:bg-gray-800 transform hover:scale-105 transition-all cursor-pointer"
              disabled={waitingForResponse}
            >
              {waitingForResponse ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Processing...
                </>
              ) : buttonText}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    )
  }

  const renderToolsDialog = () => {
    if (!activeToolsMCP) return null;
    
    return (
      <Dialog open={showToolsDialog} onOpenChange={(open) => !open && closeToolsDialog()}>
        <DialogContent className="sm:max-w-[500px] max-h-[80vh] overflow-hidden bg-white rounded-xl border-4 border-gray-200 shadow-xl">
          <DialogHeader>
            <DialogTitle className="flex items-center text-lg font-bold text-black tracking-wide">
              <Server className="h-5 w-5 text-gray-600 mr-2" />
              {activeToolsMCP.name} Tools
            </DialogTitle>
          </DialogHeader>

          <div className="py-4">
            <div className="space-y-2">
              <div className="text-xs uppercase font-medium text-gray-500">Available Tools ({activeToolsMCP.tools.length})</div>
              <ScrollArea className="h-[60vh] pr-4">
                <div className="space-y-3">
                  {activeToolsMCP.tools.map((tool) => (
                    <div key={tool.name} className="p-3 bg-gray-50 rounded-lg border border-gray-200 hover:bg-gray-100 transition-colors">
                      <div className="font-medium text-gray-900 text-base tracking-wide">
                        {tool.name}
                      </div>
                      {tool.description && (
                        <div className="text-sm text-gray-500 mt-1">{tool.description}</div>
                      )}
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </div>
          </div>

          <DialogFooter>
            <Button 
              onClick={closeToolsDialog} 
              className="bg-black text-white hover:bg-gray-800 transform hover:scale-105 transition-all cursor-pointer"
            >
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    )
  }

  const renderMCPCards = () => {
    if (isLoading && formattedMCPs.length === 0) {
      return (
        <div className="flex justify-center items-center h-40">
          <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-gray-900"></div>
          <span className="ml-3 text-gray-700">Loading MCP connections...</span>
        </div>
      );
    }

    // Add a loading state when adding a new MCP
    if (waitingForResponse && currentOperation === 'add') {
      return (
        <div className="flex flex-col justify-center items-center h-40">
          <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-gray-900 mb-4"></div>
          <span className="text-gray-700 text-lg font-medium">Adding new MCP connection...</span>
        </div>
      );
    }

    if (formattedMCPs.length === 0) {
      return (
        <div className="text-center py-10 border-2 border-dashed border-gray-200 rounded-lg bg-gray-50">
          <Server className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-700">No MCP connections</h3>
          <p className="text-gray-500 mb-4">Add your first MCP connection to start integrating tools</p>
          <Button 
            onClick={openAddDialog}
            className="bg-black text-white hover:bg-gray-800 cursor-pointer"
          >
            <Plus className="h-4 w-4 mr-2" />
            Add MCP Connection
          </Button>
        </div>
      );
    }

    return (
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {formattedMCPs.map((mcp) => (
          <Card key={mcp.name} className="border-2 border-gray-200 shadow-sm hover:shadow-md transition-all">
            <CardHeader className="pb-2">
              <CardTitle className="flex justify-between items-center text-lg font-bold">
                <div className="flex items-center">
                  <Server className="h-5 w-5 text-gray-600 mr-2" />
                  {mcp.name}
                </div>
                <Badge
                  variant="outline"
                  className="bg-green-50 text-green-700 border-green-200 font-medium"
                >
                  <CheckCircle2 className="h-3 w-3 mr-1" />
                  Connected
                </Badge>
              </CardTitle>
              <div className="flex items-center text-sm text-gray-500 mt-1">
                <Globe className="h-4 w-4 mr-1 text-gray-400" />
                {mcp.url}
              </div>
            </CardHeader>

            <CardContent className="pb-2">
              <div className="space-y-2">
                <div className="text-xs uppercase font-medium text-gray-500">
                  Available Tools ({mcp.tools.length})
                </div>
                {mcp.tools && mcp.tools.length > 0 ? (
                  <div className="flex flex-col space-y-2">
                    {/* Show only the first 2 tools */}
                    {mcp.tools.slice(0, 2).map((tool) => (
                      <div key={tool.name} className="py-2 px-3 bg-gray-50 rounded-lg">
                        <span className="font-medium text-gray-900 tracking-wide">{tool.name}</span>
                      </div>
                    ))}
                    
                    {/* Show "View more" button if more than 2 tools */}
                    {mcp.tools.length > 2 && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => openToolsDialog(mcp)}
                        className="mt-1 border-dashed border-gray-300 text-gray-600 hover:text-black hover:border-gray-500 transition-all"
                      >
                        <MoreHorizontal className="h-4 w-4 mr-1" />
                        View {mcp.tools.length - 2} more {mcp.tools.length - 2 === 1 ? 'tool' : 'tools'}
                      </Button>
                    )}
                  </div>
                ) : (
                  <div className="text-sm text-gray-500 italic p-2 bg-gray-50 border border-gray-100 rounded-md">
                    No tools available
                  </div>
                )}
              </div>
            </CardContent>

            <CardFooter className="pt-2 flex justify-end gap-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => handleRefreshMCP(mcp.name)}
                disabled={waitingForResponse && refreshingMCP === mcp.name}
                className="text-gray-600 hover:text-black hover:bg-gray-100 cursor-pointer"
              >
                {waitingForResponse && refreshingMCP === mcp.name ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <RefreshCw className="h-4 w-4" />
                )}
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => handleEditMCP(mcp)}
                disabled={waitingForResponse}
                className="text-gray-600 hover:text-black hover:bg-gray-100 cursor-pointer"
              >
                <Edit className="h-4 w-4" />
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => handleDeleteMCP(mcp.name)}
                disabled={waitingForResponse && deletingMCP === mcp.name}
                className="text-gray-600 hover:text-red-500 hover:bg-gray-100 cursor-pointer"
              >
                {waitingForResponse && deletingMCP === mcp.name ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Trash2 className="h-4 w-4" />
                )}
              </Button>
            </CardFooter>
          </Card>
        ))}
      </div>
    );
  };

  // Global spinner for any operation in progress except adding
  const renderGlobalSpinner = () => {
    if (waitingForResponse && currentOperation && currentOperation !== 'add') {
      return (
        <div className="fixed top-4 right-4 bg-black bg-opacity-80 rounded-full p-2 shadow-lg z-50">
          <Loader2 className="h-6 w-6 text-white animate-spin" />
        </div>
      );
    }
    return null;
  };

  return (
    <>
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="sm:max-w-[800px] max-h-[80vh] overflow-y-auto bg-white rounded-xl border-4 border-gray-200 shadow-xl">
          <DialogHeader>
            <DialogTitle className="flex items-center text-xl font-bold text-black tracking-wide">
              <Server className="h-6 w-6 text-gray-700 mr-2" />
              MCP Connection Manager
            </DialogTitle>
          </DialogHeader>

          <div className="py-4">
            {error && (
              <Alert variant="destructive" className="mb-4 bg-red-50 border-red-200">
                <AlertCircle className="h-4 w-4 text-red-500" />
                <AlertDescription className="text-red-700">
                  {error}
                </AlertDescription>
              </Alert>
            )}

            {renderMCPCards()}

            {formattedMCPs.length > 0 && (
              <div className="mt-4">
                <Button 
                  variant="outline" 
                  onClick={openAddDialog}
                  disabled={waitingForResponse}
                  className="w-full border-2 border-dashed border-gray-300 hover:border-gray-500 hover:bg-gray-50 transition-all cursor-pointer"
                >
                  <Plus className="h-4 w-4 mr-2" />
                  Add MCP Connection
                </Button>
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>

      {renderAddEditDialog()}
      {renderToolsDialog()}
      {renderGlobalSpinner()}
    </>
  );
} 