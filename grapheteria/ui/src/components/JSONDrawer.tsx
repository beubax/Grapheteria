"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Trash2, Plus, ArrowLeft, Edit, ChevronDown, ChevronRight, Settings, Database } from "lucide-react"
import { Textarea } from "@/components/ui/textarea"
import type { JSX } from "react/jsx-runtime"

type ConfigValue = string | number | boolean | null | Record<string, any> | any[]
type ConfigDict = Record<string, ConfigValue>

interface JSONDrawerProps {
  initialConfig: ConfigDict
  onSave?: (config: ConfigDict) => void
  open: boolean
  onOpenChange: (open: boolean) => void
  title?: string
  variant?: 'workflow' | 'node' | 'debug'
  keyLabel?: string
}

export function JSONDrawer({ initialConfig, onSave, open, onOpenChange, title = "Configuration Settings", variant = 'workflow', keyLabel = "Key" }: JSONDrawerProps) {
  const [config, setConfig] = useState<ConfigDict>(initialConfig)
  const [editingItem, setEditingItem] = useState<{
    key: string
    newKey: string
    value: ConfigValue
    path: string[]
  } | null>(null)
  const [newItemKey, setNewItemKey] = useState("")
  const [newItemValueType, setNewItemValueType] = useState<string>("string")
  const [newItemValue, setNewItemValue] = useState<string>("")
  const [expandedPaths, setExpandedPaths] = useState<Set<string>>(new Set())
  const [isEditView, setIsEditView] = useState(false)

  const handleSave = () => {
    if (onSave) {
      onSave(config)
    }
    setConfig(initialConfig)
    onOpenChange(false)
  }

  const toggleExpand = (path: string) => {
    const newExpandedPaths = new Set(expandedPaths)
    if (newExpandedPaths.has(path)) {
      newExpandedPaths.delete(path)
    } else {
      newExpandedPaths.add(path)
    }
    setExpandedPaths(newExpandedPaths)
  }

  const parseValue = (value: string, type: string): ConfigValue => {
    switch (type) {
      case "string":
        return value
      case "number":
        return Number(value)
      case "boolean":
        return value === "true"
      case "null":
        return null
      case "list":
        return []
      case "object":
        return {}
      default:
        return value
    }
  }

  const getNestedValue = (obj: any, path: string[]): any => {
    if (path.length === 0) return obj

    let current = obj
    for (const key of path) {
      if (current === undefined || current === null) return undefined
      current = current[key]
    }

    return current
  }

  const handleValueTypeChange = (type: string) => {
    setNewItemValueType(type)

    // Set default values based on type
    switch (type) {
      case "string":
        setNewItemValue("")
        break
      case "number":
        setNewItemValue("0")
        break
      case "boolean":
        setNewItemValue("false")
        break
      case "null":
        setNewItemValue("")
        break
      case "list":
        setNewItemValue("[]")
        break
      case "object":
        setNewItemValue("{}")
        break
      default:
        setNewItemValue("")
    }
  }

  const handleAddItem = (parentPath: string[] = []) => {
    // For root level, require a key
    if (parentPath.length === 0 && !newItemKey.trim()) return

    let processedValue: ConfigValue

    try {
      // Try to parse as JSON if it's a complex type
      if (newItemValueType === "object" || newItemValueType === "list") {
        processedValue = newItemValue ? JSON.parse(newItemValue) : newItemValueType === "list" ? [] : {}
      } else {
        processedValue = parseValue(newItemValue, newItemValueType)
      }
    } catch (e) {
      // If parsing fails, use the raw value
      processedValue = newItemValue
    }

    if (parentPath.length === 0) {
      // Adding to root
      setConfig({
        ...config,
        [newItemKey]: processedValue,
      })
    } else {
      // Adding to nested structure
      const newConfig = { ...config }
      let current: any = newConfig

      // Navigate to the parent object
      for (let i = 0; i < parentPath.length - 1; i++) {
        current = current[parentPath[i]]
      }

      const parentObj = current[parentPath[parentPath.length - 1]]

      if (Array.isArray(parentObj)) {
        // For arrays, just push the new value
        parentObj.push(processedValue)
      } else {
        // For objects, add the new key-value pair
        if (newItemKey.trim()) {
          parentObj[newItemKey] = processedValue
        }
      }

      setConfig(newConfig)
    }

    setNewItemKey("")
    setNewItemValue("")
    setNewItemValueType("string")
    setEditingItem(null)
    setIsEditView(false)
  }

  const handleRemoveItem = (key: string, path: string[] = []) => {
    const newConfig = { ...config }

    if (path.length === 0) {
      // Removing from root
      delete newConfig[key]
    } else {
      // Removing from nested object
      let current: any = newConfig

      // Navigate to the parent object
      for (let i = 0; i < path.length - 1; i++) {
        current = current[path[i]]
      }

      const parentObj = current[path[path.length - 1]]

      if (Array.isArray(parentObj)) {
        // For arrays, remove by index
        parentObj.splice(Number(key), 1)
      } else {
        // For objects, delete the key
        delete parentObj[key]
      }
    }

    setConfig(newConfig)
  }

  const startEditing = (key: string, value: ConfigValue, path: string[] = []) => {
    setEditingItem({
      key,
      newKey: key,
      value,
      path,
    })
    setNewItemValue(getValueStringFromValue(value))
    setNewItemValueType(getValueTypeFromValue(value))
    setIsEditView(true)
  }

  const handleUpdateItem = () => {
    if (!editingItem) return

    const { key, newKey, path } = editingItem
    let processedValue: ConfigValue

    try {
      // Try to parse as JSON if it's a complex type
      if (newItemValueType === "object" || newItemValueType === "list") {
        processedValue = newItemValue ? JSON.parse(newItemValue) : newItemValueType === "list" ? [] : {}
      } else {
        processedValue = parseValue(newItemValue, newItemValueType)
      }
    } catch (e) {
      // If parsing fails, use the raw value
      processedValue = newItemValue
    }

    const newConfig = { ...config }

    if (path.length === 0) {
      // Updating root level
      if (key !== newKey && newKey.trim()) {
        // Key has changed, remove old key and add new one
        delete newConfig[key]
        newConfig[newKey] = processedValue
      } else if (newKey.trim()) {
        // Just update the value
        newConfig[key] = processedValue
      }
    } else {
      // Updating nested object
      let current: any = newConfig

      // Navigate to the parent object
      for (let i = 0; i < path.length - 1; i++) {
        current = current[path[i]]
      }

      const parentObj = current[path[path.length - 1]]

      if (Array.isArray(parentObj)) {
        // For arrays, just update the value at the index
        const index = Number(key)
        parentObj[index] = processedValue
      } else {
        // For objects, handle key changes
        if (key !== newKey && newKey.trim()) {
          // Key has changed, remove old key and add new one
          delete parentObj[key]
          parentObj[newKey] = processedValue
        } else if (newKey.trim()) {
          // Just update the value
          parentObj[key] = processedValue
        }
      }
    }

    setConfig(newConfig)
    setEditingItem(null)
    setIsEditView(false)
  }

  const cancelEditing = () => {
    setEditingItem(null)
    setIsEditView(false)
  }

  const getValueDisplay = (value: ConfigValue): JSX.Element => {
    if (value === null) return <span className="text-gray-400 italic">None</span>

    if (typeof value === "boolean") {
      return (
        <Badge
          variant={value ? "default" : "outline"}
          className={
            value 
              ? "bg-gray-100 text-gray-800 hover:bg-gray-100 border-2 border-gray-200 font-semibold" 
              : "bg-white text-gray-800 hover:bg-gray-100 border-2 border-gray-200 font-semibold"
          }
        >
          {value ? "True" : "False"}
        </Badge>
      )
    }

    if (Array.isArray(value)) {
      return <span className="text-gray-700 font-medium">📋 List[{value.length}]</span>
    }

    if (typeof value === "object") {
      const keys = Object.keys(value)
      return <span className="text-gray-700 font-medium">📘 Dict[{keys.length}]</span>
    }

    return <span className="font-medium">{String(value)}</span>
  }

  const getTypeDisplay = (value: ConfigValue): string => {
    if (value === null) return "null"
    if (Array.isArray(value)) return "list"
    if (typeof value === "object") return "object"
    return typeof value
  }

  const getValueTypeFromValue = (value: ConfigValue): string => {
    if (value === null) return "null"
    if (Array.isArray(value)) return "list"
    if (typeof value === "object") return "object"
    return typeof value
  }

  const getValueStringFromValue = (value: ConfigValue): string => {
    if (value === null) return ""
    if (typeof value === "object" || Array.isArray(value)) {
      return JSON.stringify(value, null, 2)
    }
    return String(value)
  }

  const renderConfigItems = (items: ConfigDict | any[], path: string[] = []): JSX.Element => {
    if (Array.isArray(items)) {
      return (
        <div className="space-y-1">
          {items.length === 0 ? (
            <div></div>
          ) : (
            items.map((item, index) => {
              const currentPath = [...path, String(index)]
              const pathString = currentPath.join(".")
              const isExpandable = typeof item === "object" && item !== null
              const isExpanded = expandedPaths.has(pathString)

              return (
                <div key={pathString} className="border-l-2 border-gray-200 pl-2 transition-all duration-200">
                  <div className="flex items-center justify-between py-1 px-2 rounded-md hover:bg-gray-50 transition-colors duration-150">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        {isExpandable && (
                          <button
                            onClick={() => toggleExpand(pathString)}
                            className="p-1 rounded-full hover:bg-gray-200 transition-colors duration-150"
                          >
                            {isExpanded ? <ChevronDown className="h-3 w-3 text-black" /> : <ChevronRight className="h-3 w-3 text-black" />}
                          </button>
                        )}
                        <span className="font-medium text-black">[{index}]</span>
                        <Badge variant="outline" className="text-xs bg-gray-50 border-gray-200">
                          {getTypeDisplay(item)}
                        </Badge>
                      </div>
                      <div className="text-gray-700 mt-1 ml-5">{getValueDisplay(item)}</div>
                    </div>
                    <div className="flex gap-1">
                      <Button variant="ghost" size="icon" onClick={() => startEditing(String(index), item, path)}
                        className="hover:bg-gray-100 text-gray-600">
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => handleRemoveItem(String(index), path)}
                        className="text-gray-600 hover:text-black hover:bg-gray-100"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>

                  {isExpandable && isExpanded && (
                    <div className="ml-6 mt-1 mb-2">
                      {typeof item === "object" &&
                        item !== null &&
                        !Array.isArray(item) &&
                        renderConfigItems(item as ConfigDict, currentPath)}
                      {Array.isArray(item) && renderConfigItems(item, currentPath)}

                      {/* Add button for nested items */}
                      <div className="mt-2">
                        <Button
                          variant="outline"
                          size="sm"
                          className="w-full border-dashed"
                          onClick={() => {
                            setNewItemKey("")
                            setNewItemValue("")
                            setNewItemValueType("string")
                            setEditingItem({ key: "", newKey: "", value: "", path: currentPath })
                            setIsEditView(true)
                          }}
                        >
                          <Plus className="h-3 w-3 mr-1" /> Add
                        </Button>
                      </div>
                    </div>
                  )}
                </div>
              )
            })
          )}
        </div>
      )
    } else {
      return (
        <div className="space-y-1">
          {Object.entries(items).map(([key, value]) => {
            const currentPath = [...path, key]
            const pathString = currentPath.join(".")
            const isExpandable = typeof value === "object" && value !== null
            const isExpanded = expandedPaths.has(pathString)

            return (
              <div key={pathString} className="border-l-2 border-gray-200 pl-2 transition-all duration-200">
                <div className="flex items-center justify-between py-1 px-2 rounded-md hover:bg-gray-50 transition-colors duration-150">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      {isExpandable && (
                        <button onClick={() => toggleExpand(pathString)} className="p-1 rounded-full hover:bg-gray-200 transition-colors duration-150">
                          {isExpanded ? <ChevronDown className="h-3 w-3 text-black" /> : <ChevronRight className="h-3 w-3 text-black" />}
                        </button>
                      )}
                      <span className="font-medium text-black">{key}</span>
                      <Badge variant="outline" className="text-xs bg-gray-50 border-gray-200">
                        {getTypeDisplay(value)}
                      </Badge>
                    </div>
                    <div className="text-gray-700 mt-1 ml-5">{getValueDisplay(value)}</div>
                  </div>
                  <div className="flex gap-1">
                    <Button variant="ghost" size="icon" onClick={() => startEditing(key, value, path)}
                      className="hover:bg-gray-100 text-gray-600">
                      <Edit className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => handleRemoveItem(key, path)}
                      className="text-gray-600 hover:text-black hover:bg-gray-100"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>

                {isExpandable && isExpanded && (
                  <div className="ml-6 mt-1 mb-2">
                    {typeof value === "object" &&
                      value !== null &&
                      !Array.isArray(value) &&
                      renderConfigItems(value as ConfigDict, currentPath)}
                    {Array.isArray(value) && renderConfigItems(value, currentPath)}

                    {/* Add button for nested items */}
                    <div className="mt-2">
                      <Button
                        variant="outline"
                        size="sm"
                        className="w-full border-dashed"
                        onClick={() => {
                          setNewItemKey("")
                          setNewItemValue("")
                          setNewItemValueType("string")
                          setEditingItem({ key: "", newKey: "", value: "", path: currentPath })
                          setIsEditView(true)
                        }}
                      >
                        <Plus className="h-3 w-3 mr-1" /> Add
                      </Button>
                    </div>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )
    }
  }

  const renderEditView = () => {
    return (
      <div className="space-y-2">
        <div className="flex items-center mb-2">
          <Button 
            variant="ghost" 
            size="sm" 
            onClick={cancelEditing} 
            className="mr-2 hover:bg-gray-100 hover:text-black transition-colors duration-150"
          >
            <ArrowLeft className="h-4 w-4 mr-1" /> Back
          </Button>
        </div>

        {/* Show key input only if not adding to a list */}
        {(!editingItem?.path.length || !Array.isArray(getNestedValue(config, editingItem?.path || []))) && (
          <div className="space-y-1">
            <Label htmlFor="edit-key">{keyLabel}</Label>
            <Input
              id="edit-key"
              value={editingItem?.key ? editingItem.newKey : newItemKey}
              onChange={(e) =>
                editingItem?.key
                  ? setEditingItem({ ...editingItem, newKey: e.target.value })
                  : setNewItemKey(e.target.value)
              }
              placeholder={`Enter ${keyLabel.toLowerCase()} name`}
            />
          </div>
        )}

        <div className="space-y-1">
          <Label htmlFor="edit-value-type" className="font-medium text-gray-700">Value Type</Label>
          <Select value={newItemValueType} onValueChange={handleValueTypeChange}>
            <SelectTrigger className="border-2 focus:ring-2 focus:ring-gray-200 transition-all duration-200 bg-white">
              <SelectValue placeholder="Select value type" />
            </SelectTrigger>
            <SelectContent className="border-2 border-gray-200 bg-white shadow-md z-50">
              <SelectItem value="string">String</SelectItem>
              <SelectItem value="number">Number</SelectItem>
              <SelectItem value="boolean">Boolean</SelectItem>
              <SelectItem value="null">None (null)</SelectItem>
              <SelectItem value="list">List</SelectItem>
              <SelectItem value="object">Dict</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-1">
          <Label htmlFor="edit-value">Value</Label>
          {newItemValueType === "boolean" ? (
            <Select value={String(newItemValue)} onValueChange={setNewItemValue}>
              <SelectTrigger className="bg-white border-2">
                <SelectValue placeholder="Select boolean value" />
              </SelectTrigger>
              <SelectContent className="bg-white border-2 border-gray-200 shadow-md z-50">
                <SelectItem value="true">True</SelectItem>
                <SelectItem value="false">False</SelectItem>
              </SelectContent>
            </Select>
          ) : newItemValueType === "null" ? (
            <div className="p-2 bg-gray-100 rounded-md text-gray-500 text-sm">Value will be set to None (null)</div>
          ) : newItemValueType === "list" || newItemValueType === "object" ? (
            <div className="space-y-1">
              <div className="p-2 bg-gray-100 rounded-md text-gray-500 text-sm">
                {newItemValueType === "list"
                  ? "Value will be initialized as an empty list"
                  : "Value will be initialized as an empty dictionary"}
              </div>
              <Textarea
                placeholder={`Or enter JSON for a pre-populated ${newItemValueType === "list" ? "list" : "dictionary"}`}
                value={newItemValue}
                onChange={(e) => setNewItemValue(e.target.value)}
                className="font-mono text-sm"
                rows={3}
              />
            </div>
          ) : (
            <Input
              id="edit-value"
              value={String(newItemValue || "")}
              onChange={(e) => setNewItemValue(e.target.value)}
              placeholder={`Enter ${newItemValueType} value`}
              type={newItemValueType === "number" ? "number" : "text"}
            />
          )}
        </div>

        <div className="flex gap-2 pt-2">
          <Button 
            variant="outline" 
            onClick={cancelEditing} 
            className="flex-1 border-2 hover:bg-gray-100 transition-all duration-200"
            size="sm"
          >
            Cancel
          </Button>
          <Button
            onClick={editingItem?.key ? handleUpdateItem : () => handleAddItem(editingItem?.path || [])}
            className="text-white flex-1 bg-black hover:bg-gray-800 hover:scale-105 transition-all duration-200"
            size="sm"
          >
            {editingItem?.key ? "Update" : "Add"}
          </Button>
        </div>
      </div>
    )
  }

  const renderListView = () => {
    return (
      <div className="space-y-2">
        {Object.keys(config).length === 0 ? (
          <div className="text-center py-8 text-gray-500 font-medium italic bg-gray-50 rounded-lg">
            No configuration items yet 🏝️
          </div>
        ) : (
          renderConfigItems(config)
        )}

        {/* Add button for root level */}
        <Button
          variant="outline"
          size="sm"
          className="w-full border-dashed border-2 border-gray-300 hover:border-gray-500 hover:bg-gray-50 mt-2 transition-all duration-300 font-medium"
          onClick={() => {
            setNewItemKey("")
            setNewItemValue("")
            setNewItemValueType("string")
            setEditingItem({ key: "", newKey: "", value: "", path: [] })
            setIsEditView(true)
          }}
        >
          <Plus className="h-4 w-4 mr-1 text-black" /> Add
        </Button>
      </div>
    )
  }

  const getIcon = () => {
    switch (variant) {
      case 'workflow': return <Settings className="h-5 w-5 text-gray-600" />;
      case 'node': return <Edit className="h-5 w-5 text-gray-600" />;
      case 'debug': return <Database className="h-5 w-5 text-gray-600" />;
    }
  };

  return (
    <Dialog open={open} onOpenChange={(isOpen) => {
      if (!isOpen) {
        setConfig(initialConfig);
      }
      onOpenChange(isOpen);
    }}>
      <DialogContent className="sm:max-w-[500px] max-h-[80vh] overflow-y-auto bg-white rounded-xl border-4 border-gray-200 shadow-xl px-3 py-1">
        <DialogHeader className="p-0 m-0">
          <DialogTitle className="flex items-center justify-center text-lg font-bold text-black tracking-wide m-0">
            {getIcon()}
            <span className="ml-2">{title}</span>
          </DialogTitle>
        </DialogHeader>

        <Card className="border-0 shadow-none m-0 p-0">
          <CardContent className="p-0 m-0">{isEditView ? renderEditView() : renderListView()}</CardContent>
        </Card>

        {!isEditView && (
          <DialogFooter className="m-0 p-0 mt-0">
            <Button onClick={handleSave} className="text-white bg-black hover:bg-gray-800 transition-all duration-300 transform hover:scale-105 shadow-md">
              Save
            </Button>
          </DialogFooter>
        )}
      </DialogContent>
    </Dialog>
  )
}

