import { useState } from 'react';
import { sendChat } from '../lib/api';

export type Message = {
  role: 'user' | 'assistant';
  content: string;
  reasoning?: any[];
  results?: any;
  images?: Array<{
    smiles: string;
    image_data: string;
    width: number;
    height: number;
  }>;
};

export const useChat = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | undefined>();

  const sendMessage = async (content: string) => {
    try {
      setIsLoading(true);
      // Add user message
      const userMsg: Message = { role: 'user', content };
      setMessages((prev) => [...prev, userMsg]);

      const response = await sendChat(content, sessionId);
      
      if (response.session_id && !sessionId) {
        setSessionId(response.session_id);
      }

      const assistantMsg: Message = {
        role: 'assistant',
        content: response.response,
        reasoning: response.reasoning_trace,
        results: response.search_results,
        images: response.images
      };

      setMessages((prev) => [...prev, assistantMsg]);
      return response;
    } catch (error) {
      console.error('Chat error:', error);
      const errorMsg: Message = { role: 'assistant', content: "Sorry, I encountered an error. Please try again." };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const clearChat = () => {
    setMessages([]);
    setSessionId(undefined); // Reset session ID to create new session on next message
  };

  return {
    messages,
    isLoading,
    sendMessage,
    clearChat // Exposed for clearing chat and resetting session
  };
};

