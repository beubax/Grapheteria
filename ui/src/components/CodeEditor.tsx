import { useState } from 'react';
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
  module?: string;  // Added module prop
}

export function CodeEditor({
  initialCode,
  onSave,
  open,
  onOpenChange,
  title,
  language = 'python',
  module
}: CodeEditorProps) {
  const [code, setCode] = useState(initialCode);

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
        className="sm:max-w-[80vw] max-h-[90vh] flex flex-col bg-white"
        onClick={stopPropagation}
        onMouseDown={stopPropagation}
        onDoubleClick={stopPropagation}
        onMouseUp={stopPropagation}
      >
        <DialogHeader>
          <div className="flex flex-col">
            <DialogTitle>{title}</DialogTitle>
            {module && (
              <div className="text-sm text-gray-600 mt-1">
                Located in <code className="bg-gray-100 px-1.5 py-0.5 rounded text-sm font-mono text-gray-800">{module}</code>
              </div>
            )}
          </div>
        </DialogHeader>
        <div 
          className="flex-1 min-h-[50vh] bg-white mt-2"
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
              minimap: { enabled: true },
              scrollBeyondLastLine: false,
              fontSize: 14,
              wordWrap: 'on',
              theme: 'vs'
            }}
            className="border rounded"
          />
        </div>
        <DialogFooter className="mt-4">
          <Button 
            variant="outline" 
            onClick={(e) => {
              stopPropagation(e);
              onOpenChange(false);
            }}
            className="hover:bg-gray-100 cursor-pointer"
          >
            Cancel
          </Button>
          <div className="flex flex-col items-end">
            <Button 
              onClick={(e) => {
                stopPropagation(e);
                handleSave();
              }}
              className="bg-blue-600 hover:bg-blue-700 text-white cursor-pointer"
            >
              Save
            </Button>
            <span className="text-xs text-red-600 mt-1 font-medium">Experimental</span>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}