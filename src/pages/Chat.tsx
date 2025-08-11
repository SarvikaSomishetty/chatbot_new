import React, { useState, useRef, useEffect } from 'react';
import { Send, ThumbsUp, ThumbsDown, Plus, HelpCircle, FileText, MessageSquare } from 'lucide-react';
import { useParams } from 'react-router-dom';
import { useApp } from '../contexts/AppContext';
import { ChatMessage } from '../types';
import Header from '../components/Header';
import TicketModal from '../components/TicketModal';

const Chat: React.FC = () => {
  const { domain } = useParams<{ domain: string }>();
  const { selectedDomain } = useApp();
  const [message, setMessage] = useState('');
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: '1',
      content: `Hello! I'm your ${domain?.replace('-', ' ')} assistant. How can I help you today?`,
      sender: 'bot',
      timestamp: new Date()
    }
  ]);
  const [isTyping, setIsTyping] = useState(false);
  const [showTicketModal, setShowTicketModal] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const faqs = [
    'How do I reset my password?',
    'Where can I find my order history?',
    'How do I contact support?',
    'What are your business hours?'
  ];

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim()) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      content: message,
      sender: 'user',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setMessage('');
    setIsTyping(true);

    // Simulate bot response
    setTimeout(() => {
      const botMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        content: `I understand you're asking about "${message}". Let me help you with that. Based on our knowledge base, here's what I can suggest...`,
        sender: 'bot',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, botMessage]);
      setIsTyping(false);
    }, 2000);
  };

  const handleFeedback = (messageId: string, helpful: boolean) => {
    setMessages(prev =>
      prev.map(msg =>
        msg.id === messageId ? { ...msg, helpful } : msg
      )
    );
  };

  const formatDomainName = (domain: string) => {
    return domain.split('-').map(word => 
      word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ');
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors duration-200">
      <Header showProfile />
      
      <div className="flex h-[calc(100vh-4rem)]">
        {/* Main Chat Area */}
        <div className="flex-1 flex flex-col">
          {/* Chat Header */}
          <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 p-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                  {formatDomainName(domain || '')} Chat
                </h2>
                <div className="flex items-center space-x-2 mt-1">
                  <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                  <span className="text-sm text-gray-500 dark:text-gray-400">AI Assistant Online</span>
                </div>
              </div>
              <button
                onClick={() => setShowTicketModal(true)}
                className="flex items-center space-x-2 bg-orange-600 text-white px-4 py-2 rounded-lg hover:bg-orange-700 transition-colors duration-200"
              >
                <Plus className="w-4 h-4" />
                <span>Create Ticket</span>
              </button>
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.map((msg) => (
              <div key={msg.id} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-xs lg:max-w-md ${
                  msg.sender === 'user' 
                    ? 'bg-blue-600 text-white' 
                    : 'bg-white dark:bg-gray-800 text-gray-900 dark:text-white border border-gray-200 dark:border-gray-700'
                } rounded-2xl px-4 py-3 shadow-sm`}>
                  <p className="text-sm">{msg.content}</p>
                  <p className="text-xs mt-2 opacity-75">
                    {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </p>
                  
                  {msg.sender === 'bot' && (
                    <div className="flex items-center space-x-2 mt-3 pt-2 border-t border-gray-100 dark:border-gray-700">
                      <span className="text-xs opacity-75">Was this helpful?</span>
                      <button
                        onClick={() => handleFeedback(msg.id, true)}
                        className={`p-1 rounded ${msg.helpful === true ? 'bg-green-100 text-green-600' : 'hover:bg-gray-100 dark:hover:bg-gray-700'}`}
                      >
                        <ThumbsUp className="w-3 h-3" />
                      </button>
                      <button
                        onClick={() => handleFeedback(msg.id, false)}
                        className={`p-1 rounded ${msg.helpful === false ? 'bg-red-100 text-red-600' : 'hover:bg-gray-100 dark:hover:bg-gray-700'}`}
                      >
                        <ThumbsDown className="w-3 h-3" />
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ))}
            
            {isTyping && (
              <div className="flex justify-start">
                <div className="bg-white dark:bg-gray-800 rounded-2xl px-4 py-3 shadow-sm border border-gray-200 dark:border-gray-700">
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-75" />
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-150" />
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Message Input */}
          <div className="bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 p-4">
            <form onSubmit={handleSendMessage} className="flex space-x-4">
              <div className="flex-1">
                <input
                  type="text"
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  placeholder="Type your message..."
                  className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 transition-colors duration-200"
                />
              </div>
              <button
                type="submit"
                disabled={!message.trim() || isTyping}
                className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
              >
                <Send className="w-5 h-5" />
              </button>
            </form>
          </div>
        </div>

        {/* Sidebar */}
        <div className="w-80 bg-white dark:bg-gray-800 border-l border-gray-200 dark:border-gray-700 p-4 space-y-6">
          {/* FAQs */}
          <div>
            <div className="flex items-center space-x-2 mb-4">
              <HelpCircle className="w-5 h-5 text-blue-600" />
              <h3 className="font-semibold text-gray-900 dark:text-white">Frequently Asked</h3>
            </div>
            <div className="space-y-2">
              {faqs.map((faq, index) => (
                <button
                  key={index}
                  onClick={() => setMessage(faq)}
                  className="w-full text-left p-3 text-sm text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-lg border border-gray-200 dark:border-gray-600 transition-colors duration-200"
                >
                  {faq}
                </button>
              ))}
            </div>
          </div>

          {/* Quick Actions */}
          <div>
            <div className="flex items-center space-x-2 mb-4">
              <MessageSquare className="w-5 h-5 text-green-600" />
              <h3 className="font-semibold text-gray-900 dark:text-white">Quick Actions</h3>
            </div>
            <div className="space-y-2">
              <button
                onClick={() => setShowTicketModal(true)}
                className="w-full flex items-center space-x-3 p-3 text-sm text-gray-600 dark:text-gray-300 hover:bg-orange-50 dark:hover:bg-orange-900/20 rounded-lg border border-orange-200 dark:border-orange-800 transition-colors duration-200"
              >
                <FileText className="w-4 h-4 text-orange-600" />
                <span>Still need help? Create a Ticket</span>
              </button>
            </div>
          </div>

          {/* Status */}
          <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg">
            <h4 className="font-medium text-blue-900 dark:text-blue-100 mb-2">Status</h4>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-blue-700 dark:text-blue-300">Response Time:</span>
                <span className="text-blue-900 dark:text-blue-100">~30 seconds</span>
              </div>
              <div className="flex justify-between">
                <span className="text-blue-700 dark:text-blue-300">Queue Position:</span>
                <span className="text-blue-900 dark:text-blue-100">Active</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <TicketModal
        isOpen={showTicketModal}
        onClose={() => setShowTicketModal(false)}
        domain={formatDomainName(domain || '')}
      />
    </div>
  );
};

export default Chat;