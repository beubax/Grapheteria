import { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from './ui/dialog';
import { Button } from './ui/button';
import Editor from '@monaco-editor/react'; // You'll need to install this package

interface CodeEditorProps {
  initialCode: string;
  onSave: (code: string) => void;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  language?: string;
  module?: string;
  showClassNameInput?: boolean;
  onClassNameChange?: (className: string) => void;
  className?: string;
}

export function CodeEditor({
  initialCode,
  onSave,
  open,
  onOpenChange,
  title,
  language = 'python',
  module,
  showClassNameInput = false,
  onClassNameChange,
  className = ''
}: CodeEditorProps) {
  const [code, setCode] = useState(initialCode);
  const [nodeClassName, setNodeClassName] = useState(className);

  useEffect(() => {
    setNodeClassName(className);
  }, [className]);

  const handleSave = () => {
    onSave(code);
    onOpenChange(false);
  };

  // Prevent event propagation
  const stopPropagation = (e: React.MouseEvent) => {
    e.stopPropagation();
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent 
        className="sm:max-w-[80vw] max-h-[88vh] flex flex-col bg-white p-4 pb-6"
        onClick={stopPropagation}
        onMouseDown={stopPropagation}
        onDoubleClick={stopPropagation}
        onMouseUp={stopPropagation}
      >
        <DialogHeader className="pb-0">
          <div className="flex flex-col">
            {showClassNameInput ? (
              <div className="mb-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Class Name
                </label>
                <input
                  type="text"
                  value={nodeClassName}
                  onChange={(e) => {
                    setNodeClassName(e.target.value);
                    if (onClassNameChange) {
                      onClassNameChange(e.target.value);
                    }
                  }}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  placeholder="YourCustomNodeName"
                />
              </div>
            ) : (
              <DialogTitle>{title}</DialogTitle>
            )}
            {module && (
              <div className="text-sm text-gray-600 mt-1">
                Located in <code className="bg-gray-100 px-1.5 py-0.5 rounded text-sm font-mono text-gray-800">{module}</code>
              </div>
            )}
          </div>
        </DialogHeader>
        
        <div 
          className="flex-1 min-h-[50vh] bg-white mt-0"
          onClick={stopPropagation}
          onMouseDown={stopPropagation}
          onDoubleClick={stopPropagation}
          onMouseUp={stopPropagation}
        >
          <Editor
            height="50vh"
            defaultLanguage={language}
            defaultValue={initialCode}
            onChange={(value) => setCode(value || '')}
            options={{
              minimap: { enabled: false },
              scrollBeyondLastLine: false,
              fontSize: 12,
              wordWrap: 'on',
              theme: 'vs'
            }}
            className="border rounded"
          />
        </div>
        <DialogFooter className="mt-0">
          <Button 
            variant="outline" 
            onClick={(e) => {
              stopPropagation(e);
              onOpenChange(false);
            }}
            className="hover:bg-gray-100 cursor-pointer text-sm px-3 py-1 h-8"
          >
            Cancel
          </Button>
          <div className="flex flex-col items-end">
            <Button 
              onClick={(e) => {
                stopPropagation(e);
                handleSave();
              }}
              className="bg-blue-600 hover:bg-blue-700 text-white cursor-pointer text-sm px-3 py-1 h-8"
            >
              Save
            </Button>
            <span className="text-[10px] text-red-600 mt-0.5">Experimental</span>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}