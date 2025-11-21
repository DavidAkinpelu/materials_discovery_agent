import React, { useState, useRef, useEffect } from 'react';
import { useChat } from '../hooks/useChat';
import { MessageBubble } from './MessageBubble';
import { ExampleQueries } from './ExampleQueries';
import { Send, Loader2 } from 'lucide-react';

export const ChatInterface: React.FC = () => {
  const { messages, isLoading, sendMessage, clearChat } = useChat();
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSubmit = async (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!input.trim() || isLoading) return;

    const query = input;
    setInput('');
    await sendMessage(query);
  };

  const handleExampleSelect = (query: string) => {
    setInput(query);
  };

  const handleLogoClick = () => {
    clearChat(); // Use clearChat to reset both messages and session
    setInput('');
  };

  return (
    <div className="flex flex-col h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 px-6 py-4 shadow-sm z-10">
        <div className="max-w-6xl mx-auto flex items-center gap-3">
           <button 
             onClick={handleLogoClick}
             className="flex items-center gap-3 hover:opacity-80 transition-opacity cursor-pointer"
             title="Reset chat"
           >
             <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center text-white font-bold">M</div>
             <h1 className="text-xl font-semibold text-slate-800">Materials Discovery Agent</h1>
           </button>
        </div>
      </header>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-6">
        <div className="max-w-6xl mx-auto">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-[60vh] space-y-8">
              <div className="text-center space-y-2">
                <h2 className="text-2xl font-bold text-slate-800">What materials are you looking for?</h2>
                <p className="text-slate-500">I can help you discover materials based on properties, applications, and more.</p>
              </div>
              <ExampleQueries onSelect={handleExampleSelect} />
            </div>
          ) : (
            <>
              {messages.map((msg, idx) => (
                <MessageBubble key={idx} message={msg} />
              ))}
              {isLoading && (
                <div className="flex justify-start mb-6">
                  <div className="bg-white border border-slate-200 rounded-2xl px-6 py-4 shadow-sm flex items-center gap-3">
                    <Loader2 className="w-4 h-4 animate-spin text-blue-600" />
                    <span className="text-sm text-slate-500">Agent is reasoning...</span>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </>
          )}
        </div>
      </div>

      {/* Input */}
      <div className="bg-white border-t border-slate-200 px-4 py-4">
        <div className="max-w-6xl mx-auto">
          <form onSubmit={handleSubmit} className="relative flex items-center gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Describe the material you need..."
              className="w-full px-4 py-3 pr-12 rounded-xl border border-slate-200 focus:border-blue-500 focus:ring-2 focus:ring-blue-100 outline-none transition-all"
              disabled={isLoading}
            />
            <button
              type="submit"
              disabled={!input.trim() || isLoading}
              className="absolute right-2 p-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:hover:bg-blue-600 transition-colors"
            >
              {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
            </button>
          </form>
          <p className="text-center text-xs text-slate-400 mt-2">
            Powered by OpenAI & LangGraph. Agent may make mistakes.
          </p>
        </div>
      </div>
    </div>
  );
};

