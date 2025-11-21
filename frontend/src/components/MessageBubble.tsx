import React from 'react';
import ReactMarkdown from 'react-markdown';
import type { Components } from 'react-markdown';
import type { Message } from '../hooks/useChat';
import { MaterialsTable } from './MaterialsTable';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface MessageBubbleProps {
  message: Message;
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
  const isUser = message.role === 'user';
  
  // Filter out error messages from display
  const shouldShowMessage = isUser || !message.content.toLowerCase().includes('error');
  
  // Clean content: remove error keywords and technical details
  const cleanContent = (content: string): string => {
    if (isUser) return content;
    
    // Remove error lines and technical traces
    return content
      .split('\n')
      .filter(line => {
        const lower = line.toLowerCase();
        return !lower.includes('error:') && 
               !lower.includes('traceback') && 
               !lower.includes('exception') &&
               !lower.includes('failed:') &&
               !lower.includes('warning:');
      })
      .join('\n')
      .trim() || "I encountered an issue processing your request. Please try rephrasing your query.";
  };

  // Custom markdown components for better rendering
  const markdownComponents: Components = {
    // Explicit header components to ensure proper styling
    h1: ({ children }) => (
      <h1 className="text-2xl font-bold text-slate-900 mb-4 mt-6">
        {children}
      </h1>
    ),
    h2: ({ children }) => (
      <h2 className="text-xl font-bold text-slate-800 mb-3 mt-5">
        {children}
      </h2>
    ),
    h3: ({ children }) => (
      <h3 className="text-lg font-semibold text-slate-800 mb-3 mt-4 border-b border-slate-200 pb-1">
        {children}
      </h3>
    ),
    h4: ({ children }) => (
      <h4 className="text-base font-semibold text-slate-700 mb-2 mt-3">
        {children}
      </h4>
    ),
    // Better blockquote styling
    blockquote: ({ children }) => (
      <blockquote className="border-l-4 border-blue-500 pl-4 py-2 my-4 bg-blue-50 rounded-r italic">
        {children}
      </blockquote>
    ),
    // Enhanced list items
    li: ({ children }) => (
      <li className="my-1.5 leading-relaxed">
        {children}
      </li>
    ),
  };

  if (!shouldShowMessage) {
    return (
      <div className="flex w-full mb-6 justify-start">
        <div className="max-w-[95%] bg-amber-50 border border-amber-200 rounded-2xl px-8 py-5">
          <p className="text-slate-700">I'm working on finding the best materials for you. Please wait a moment...</p>
        </div>
      </div>
    );
  }

  return (
    <div className={cn("flex w-full mb-6", isUser ? "justify-end" : "justify-start")}>
      <div className={cn(
        "rounded-2xl",
        isUser 
          ? "max-w-[85%] bg-blue-600 text-white px-6 py-4" 
          : "max-w-[95%] bg-white border border-slate-200 shadow-sm px-8 py-6"
      )}>
        <div className={cn(
          "prose prose-lg max-w-none leading-relaxed",
          isUser ? "prose-invert" : "prose-slate",
          // Enhanced prose styling for assistant messages
          !isUser && [
            // Headings - clear hierarchy
            "prose-h1:text-2xl prose-h1:font-bold prose-h1:text-slate-900 prose-h1:mb-4 prose-h1:mt-6",
            "prose-h2:text-xl prose-h2:font-bold prose-h2:text-slate-800 prose-h2:mb-3 prose-h2:mt-5",
            "prose-h3:text-lg prose-h3:font-semibold prose-h3:text-slate-800 prose-h3:mb-3 prose-h3:mt-4 prose-h3:border-b prose-h3:border-slate-200 prose-h3:pb-1",
            "prose-h4:text-base prose-h4:font-semibold prose-h4:text-slate-700 prose-h4:mb-2 prose-h4:mt-3",
            
            // Paragraphs and text
            "prose-p:text-slate-700 prose-p:leading-relaxed prose-p:mb-4 prose-p:text-base",
            
            // Strong and emphasis
            "prose-strong:text-slate-900 prose-strong:font-semibold prose-strong:text-[1.02em]",
            "prose-em:text-slate-600 prose-em:italic",
            
            // Lists - better spacing and styling
            "prose-ul:my-3 prose-ul:list-disc prose-ul:pl-6 prose-ul:space-y-1.5",
            "prose-ol:my-3 prose-ol:list-decimal prose-ol:pl-6 prose-ol:space-y-1.5",
            "prose-li:text-slate-700 prose-li:leading-relaxed",
            "prose-li>p:my-1",
            
            // Nested lists
            "prose-ul>li>ul:mt-2 prose-ul>li>ul:mb-1",
            "prose-ol>li>ol:mt-2 prose-ol>li>ol:mb-1",
            
            // Code and technical content
            "prose-code:text-blue-700 prose-code:bg-blue-50 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded prose-code:text-sm prose-code:font-mono prose-code:font-medium",
            "prose-pre:bg-slate-50 prose-pre:border prose-pre:border-slate-200 prose-pre:rounded-lg prose-pre:p-4 prose-pre:overflow-x-auto",
            "prose-pre>code:bg-transparent prose-pre>code:p-0 prose-pre>code:text-slate-800",
            
            // Blockquotes
            "prose-blockquote:border-l-4 prose-blockquote:border-blue-500 prose-blockquote:pl-4 prose-blockquote:py-2 prose-blockquote:bg-blue-50 prose-blockquote:rounded-r",
            "prose-blockquote>p:text-slate-700 prose-blockquote>p:my-1",
            
            // Links
            "prose-a:text-blue-600 prose-a:no-underline hover:prose-a:underline prose-a:font-medium",
            
            // Horizontal rules
            "prose-hr:border-slate-300 prose-hr:my-6",
            
            // Tables (if used)
            "prose-table:border-collapse prose-table:w-full",
            "prose-th:bg-slate-100 prose-th:border prose-th:border-slate-300 prose-th:px-4 prose-th:py-2 prose-th:text-left prose-th:font-semibold",
            "prose-td:border prose-td:border-slate-300 prose-td:px-4 prose-td:py-2"
          ]
        )}>
           <ReactMarkdown components={markdownComponents}>
             {cleanContent(message.content)}
           </ReactMarkdown>
        </div>

        {!isUser && message.results && message.results.materials_project && 
         Array.isArray(message.results.materials_project) &&
         message.results.materials_project.length > 0 && 
         !message.results.materials_project[0].error && (
            <div className="mt-6">
                <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-3">Materials Found</p>
                <MaterialsTable materials={message.results.materials_project} />
            </div>
        )}

        {!isUser && message.images && message.images.length > 0 && (
          <div className="mt-6">
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-3">Chemical Structures</p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {message.images.map((img, idx) => (
                <div key={idx} className="border border-slate-200 rounded-lg p-4 bg-slate-50">
                  <img 
                    src={img.image_data} 
                    alt={`Chemical structure: ${img.smiles}`}
                    className="w-full h-auto rounded"
                    style={{ maxWidth: `${img.width}px`, maxHeight: `${img.height}px` }}
                  />
                  <p className="text-xs text-slate-600 mt-2 font-mono break-all">
                    {img.smiles}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

