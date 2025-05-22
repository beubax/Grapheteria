import React, { useState, useRef, useEffect } from 'react';
import { Button } from './ui/button';
import { Card, CardContent } from './ui/card';
import { Sparkles, X, Bot, User, Loader2 } from 'lucide-react';
import { updateWorkflow } from '../utils/debugActions';

interface AIUpdateDrawerProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  workflowId: string;
}

const AIUpdateDrawer: React.FC<AIUpdateDrawerProps> = ({ open, onOpenChange, workflowId }) => {
  const [drawerWidth, setDrawerWidth] = useState(400);
  const [isResizing, setIsResizing] = useState(false);
  const [chatMessages, setChatMessages] = useState([
    { sender: 'ai', text: 'How can I help you update your workflow?' }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (open && chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [chatMessages, open]);

  // Handle resizing
  const startResizing = (e: React.MouseEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsResizing(true);
  };
  useEffect(() => {
    const handleResize = (e: MouseEvent) => {
      if (!isResizing) return;
      const newWidth = window.innerWidth - e.clientX;
      if (newWidth >= 320 && newWidth <= window.innerWidth * 0.7) {
        setDrawerWidth(newWidth);
      }
    };
    const stopResizing = () => setIsResizing(false);
    if (isResizing) {
      document.addEventListener('mousemove', handleResize);
      document.addEventListener('mouseup', stopResizing);
    }
    return () => {
      document.removeEventListener('mousemove', handleResize);
      document.removeEventListener('mouseup', stopResizing);
    };
  }, [isResizing]);

  // Handle chat send
  const handleSend = async () => {
    if (!input.trim()) return;
    setChatMessages([...chatMessages, { sender: 'user', text: input }]);
    setInput('');
    setIsLoading(true);
    
    try {
      const { data, error } = await updateWorkflow(workflowId, input);
      if (error) {
        setChatMessages(prev => [...prev, { sender: 'ai', text: error }]);
      } else {
        setChatMessages(prev => [...prev, { sender: 'ai', text: data.message }]);
      }
    } catch (err) {
      setChatMessages(prev => [...prev, { sender: 'ai', text: 'An error occurred while processing your request.' }]);
    } finally {
      setIsLoading(false);
    }
  };

  // Handle form submission
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!isLoading && input.trim()) {
      handleSend();
    }
  };

  if (!open) return null;

  return (
    <div
      className="fixed top-0 right-0 h-screen bg-white shadow-2xl z-50 flex flex-col border-l border-gray-200"
      style={{ 
        width: drawerWidth, 
        transition: isResizing ? 'none' : 'right 0.3s', 
        minWidth: 320, 
        maxWidth: '70vw',
        touchAction: 'auto'
      }}
    >
      {/* Resize handle */}
      <div
        onMouseDown={startResizing}
        className="absolute left-0 top-0 w-2 cursor-ew-resize z-10 bg-transparent hover:bg-gray-200 transition"
        style={{ 
          userSelect: 'none',
          pointerEvents: 'auto',
          height: 'calc(100% - 60px)'
        }}
      />
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-4 border-b bg-gray-50">
        <div className="flex items-center gap-2 text-lg font-semibold">
          <Sparkles className="h-5 w-5 text-purple-600" />
          AI Update
        </div>
        <Button size="icon" variant="ghost" onClick={() => onOpenChange(false)}>
          <X className="h-5 w-5" />
        </Button>
      </div>
      {/* Content */}
      <div className="flex-1 overflow-hidden relative" style={{ pointerEvents: 'auto' }}>
        <div className="flex flex-col h-full">
          {/* Chat messages container */}
          <div 
            className="flex-1 overflow-y-auto px-4 py-4 space-y-3" 
            style={{ height: 'calc(100% - 60px)' }}
          >
            {chatMessages.map((msg, idx) => (
              <Card key={idx} className={`w-fit max-w-[80%] ${msg.sender === 'user' ? 'ml-auto bg-purple-100' : 'mr-auto bg-gray-100'}`}>
                <CardContent className="flex items-center gap-2 py-2 px-3">
                  {msg.sender === 'ai' ? <Bot className="h-4 w-4 text-purple-600" /> : <User className="h-4 w-4 text-gray-500" />}
                  <span className="whitespace-pre-line text-sm">{msg.text}</span>
                </CardContent>
              </Card>
            ))}
            
            {isLoading && (
              <Card className="w-fit max-w-[80%] mr-auto bg-gray-100">
                <CardContent className="flex items-center gap-2 py-2 px-3">
                  <Bot className="h-4 w-4 text-purple-600" />
                  <Loader2 className="h-4 w-4 animate-spin text-purple-600" />
                  <span className="text-sm text-gray-500">Thinking...</span>
                </CardContent>
              </Card>
            )}
            
            <div ref={chatEndRef} />
          </div>
          
          {/* Chat input area - simplified for maximum clickability */}
          <form onSubmit={handleSubmit} className="border-t bg-white p-3 flex h-[60px]" style={{ position: 'relative', zIndex: 50 }}>
            <input
              className="flex-1 border rounded-md px-3 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 mr-2"
              placeholder="Type your request..."
              value={input}
              onChange={e => setInput(e.target.value)}
              disabled={isLoading}
              style={{ height: '100%', margin: 0, padding: '0 12px', boxSizing: 'border-box' }}
            />
            <button
              type="submit"
              className={`bg-purple-600 ${isLoading ? 'opacity-70 cursor-not-allowed' : 'hover:bg-purple-700'} text-white rounded-md px-4 text-sm font-medium`}
              style={{ height: '100%', cursor: isLoading ? 'not-allowed' : 'pointer', minWidth: '70px' }}
              disabled={isLoading}
            >
              {isLoading ? <Loader2 className="h-4 w-4 animate-spin mx-auto" /> : 'Send'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default AIUpdateDrawer; 