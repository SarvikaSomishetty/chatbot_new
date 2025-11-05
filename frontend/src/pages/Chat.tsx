import React, { useState, useRef, useEffect } from 'react';
import { Send, ThumbsUp, ThumbsDown, Plus, HelpCircle, FileText, MessageSquare, History, X } from 'lucide-react';
import { useParams } from 'react-router-dom';
import { useApp } from '../contexts/AppContext';
import { ChatMessage } from '../types';
import Header from '../components/Header';
import TicketModal from '../components/TicketModal';

interface ConversationHistory {
  conversation_id: string;
  title: string;
  domain: string;
  updated_at: string;
  message_count: number;
}

const Chat: React.FC = () => {
  const { domain } = useParams<{ domain: string }>();
  const { user } = useApp();
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
  const [sessionTicketId, setSessionTicketId] = useState<string | null>(null);
  const [showTicketModal, setShowTicketModal] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const [history, setHistory] = useState<ConversationHistory[]>([]);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const [faqs, setFaqs] = useState<string[]>([]);
  const [playingAudio, setPlayingAudio] = useState<string | null>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Load conversation history when component mounts or user/domain changes
  useEffect(() => {
    if (user && domain) {
      loadConversationHistory();
      loadDynamicFaqs();
    }
  }, [user, domain]);

  // Removed automatic FAQ refresh on every message to avoid UI jitter.

  const loadConversationHistory = async () => {
    if (!user || !domain) {
      console.log('❌ No user or domain found, skipping history load');
      return;
    }
    
    console.log('📚 Loading conversation history for user:', user.id, 'in domain:', domain);
    setIsLoadingHistory(true);
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        console.log('❌ No token found');
        return;
      }

      console.log('🔑 Making request to /api/history with domain parameter');
      const response = await fetch(`http://localhost:8000/api/history?domain=${encodeURIComponent(domain)}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      console.log('📡 History API response status:', response.status);
      if (response.ok) {
        const historyData = await response.json();
        console.log('📚 Received history data:', historyData);
        setHistory(historyData);
      } else {
        const errorData = await response.text();
        console.error('❌ History API error:', response.status, errorData);
      }
    } catch (error) {
      console.error('❌ Error loading conversation history:', error);
    } finally {
      setIsLoadingHistory(false);
    }
  };

  const resumeConversation = async (conversationId: string) => {
    if (!user) return;

    try {
      const token = localStorage.getItem('token');
      if (!token) return;

      // Load messages for this conversation
      const response = await fetch(`http://localhost:8000/api/history/${conversationId}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const messagesData = await response.json();
        
        // Convert API messages to ChatMessage format
        const convertedMessages: ChatMessage[] = messagesData.map((msg: any, index: number) => ({
          id: `${conversationId}-${index}`,
          content: msg.content,
          sender: msg.role === 'assistant' ? 'bot' : 'user',
          timestamp: new Date(msg.timestamp || Date.now())
        }));

        setMessages(convertedMessages);
        setSessionTicketId(conversationId);
        setShowHistory(false);
        
        // Scroll to bottom
        setTimeout(() => {
          messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
        }, 100);
      }
    } catch (error) {
      console.error('Error resuming conversation:', error);
    }
  };

  const loadDynamicFaqs = async () => {
    if (!user || !domain) return;
    try {
      const token = localStorage.getItem('token');
      if (!token) return;
      const res = await fetch(`http://localhost:8000/api/faqs?domain=${encodeURIComponent(domain)}&limit=6`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        }
      });
      if (res.ok) {
        const data = await res.json();
        if (Array.isArray(data.faqs)) setFaqs(data.faqs);
      }
    } catch (e) {
      // silent fail
    }
  };

  const startNewChat = () => {
    setMessages([{
      id: '1',
      content: `Hello! I'm your ${domain?.replace('-', ' ')} assistant. How can I help you today?`,
      sender: 'bot',
      timestamp: new Date()
    }]);
    setSessionTicketId(null);
    setShowHistory(false);
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim() || !user) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      content: message,
      sender: 'user',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setMessage('');
    setIsTyping(true);

    try {
      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('No authentication token found');
      }

      console.log('💬 Sending message:', {
        user_id: user.id,
        domain: domain || 'customer-support',
        question: message,
        conversation_id: sessionTicketId
      });

      // Send question to AI chatbot
      const response = await fetch('http://localhost:8000/ask', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          user_id: user.id, // Use authenticated user's ID
          domain: domain || 'customer-support',
          question: message,
          conversation_id: sessionTicketId
        })
      });

      console.log('📡 Ask API response status:', response.status);

      if (!response.ok) {
        throw new Error('Failed to get AI response');
      }

      const data = await response.json();
      console.log('✅ Received response:', data);
      
      // Update conversation ID if we got a new one
      if (data.conversation_id && !sessionTicketId) {
        console.log('🆕 New conversation created:', data.conversation_id);
        setSessionTicketId(data.conversation_id);
        // Reload history to include the new conversation
        loadConversationHistory();
      } else if (data.conversation_id && sessionTicketId) {
        console.log('📝 Continuing existing conversation:', data.conversation_id);
      }

      const botMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        content: data.answer,
        sender: 'bot',
        timestamp: new Date(),
        ttsPath: data.tts_path
      };
      
      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      console.error('Error getting AI response:', error);
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        content: 'I apologize, but I\'m having trouble connecting to the AI service. Please try again later.',
        sender: 'bot',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsTyping(false);
    }
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
        {/* History Panel */}
        {showHistory && (
          <div className="w-80 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 flex flex-col">
            <div className="p-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Chat History</h3>
                <p className="text-sm text-gray-500 dark:text-gray-400">{formatDomainName(domain || '')}</p>
              </div>
              <button
                onClick={() => setShowHistory(false)}
                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="flex-1 overflow-y-auto p-4">
              {isLoadingHistory ? (
                <div className="flex items-center justify-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                </div>
              ) : history.length === 0 ? (
                <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                  <History className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <p>No previous conversations found.</p>
                  <p className="text-sm mt-2">Start a new {formatDomainName(domain || '')} chat to see it here!</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {history.map((conv) => (
                    <button
                      key={conv.conversation_id}
                      onClick={() => resumeConversation(conv.conversation_id)}
                      className="w-full text-left p-3 rounded-lg border border-gray-200 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors duration-200"
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                            {conv.title}
                          </p>
                          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                            {conv.domain} • {conv.message_count} messages
                          </p>
                          <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                            {new Date(conv.updated_at).toLocaleDateString()} at{' '}
                            {new Date(conv.updated_at).toLocaleTimeString([], { 
                              hour: '2-digit', 
                              minute: '2-digit' 
                            })}
                          </p>
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

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
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setShowHistory(!showHistory)}
                  className="flex items-center space-x-2 bg-gradient-to-r from-teal-500 to-blue-600 text-white px-4 py-2 rounded-2xl hover:from-teal-600 hover:to-blue-700 transition-all duration-200 transform hover:scale-105 shadow-lg shadow-teal-500/25"
                >
                  <History className="w-4 h-4" />
                  <span>History</span>
                </button>
                <button
                  onClick={startNewChat}
                  className="flex items-center space-x-2 bg-gradient-to-r from-teal-500 to-blue-600 text-white px-4 py-2 rounded-2xl hover:from-teal-600 hover:to-blue-700 transition-all duration-200 transform hover:scale-105 shadow-lg shadow-teal-500/25"
                >
                  <Plus className="w-4 h-4" />
                  <span>New Chat</span>
                </button>
                <button
                  onClick={() => setShowTicketModal(true)}
                  className="flex items-center space-x-2 bg-gradient-to-r from-orange-500 to-amber-600 text-white px-4 py-2 rounded-2xl hover:from-orange-600 hover:to-amber-700 transition-all duration-200 transform hover:scale-105 shadow-lg shadow-orange-500/25"
                >
                  <Plus className="w-4 h-4" />
                  <span>Create Ticket</span>
                </button>
              </div>
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-6 space-y-6 custom-scrollbar scroll-smooth">
            {messages.map((msg, index) => (
              <div 
                key={msg.id} 
                className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'} animate-fade-in`}
                style={{ animationDelay: `${index * 0.1}s` }}
              >
                <div className={`max-w-sm lg:max-w-lg ${msg.sender === 'user'
                    ? 'bg-gradient-to-br from-teal-500 to-blue-600 text-white shadow-lg shadow-teal-500/25'
                    : 'bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-100 border border-gray-100 dark:border-gray-700 shadow-lg shadow-gray-200/50 dark:shadow-gray-800/50'
                  } rounded-3xl px-5 py-4 shadow-sm hover:shadow-md transition-all duration-200`}>
                  
                  {msg.sender === 'bot' && (
                    <div className="flex items-center mb-2">
                      <div className="w-6 h-6 bg-gradient-to-br from-teal-400 to-blue-500 rounded-full flex items-center justify-center mr-2">
                        <span className="text-white text-xs font-bold">🤖</span>
                      </div>
                      <span className="text-xs text-teal-600 dark:text-teal-400 font-medium">Assistant</span>
                    </div>
                  )}
                  
                  <p className={`text-sm leading-relaxed ${msg.sender === 'user' ? 'text-white' : 'text-gray-800 dark:text-gray-100 font-medium'}`}>
                    {msg.content}
                  </p>
                  
                  <p className={`text-xs mt-3 ${msg.sender === 'user' ? 'text-teal-100' : 'text-gray-500 dark:text-gray-400'}`}>
                    {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </p>

                  {msg.sender === 'bot' && (
                    <div className="flex items-center justify-between mt-4 pt-3 border-t border-gray-100 dark:border-gray-700">
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() => {
                            if (playingAudio === msg.id) {
                              // Stop current audio
                              if (msg.ttsPath) {
                                // Stop audio element
                                const audioElements = document.querySelectorAll('audio');
                                audioElements.forEach(audio => {
                                  audio.pause();
                                  audio.currentTime = 0;
                                });
                              } else {
                                // Stop speech synthesis
                                speechSynthesis.cancel();
                              }
                              setPlayingAudio(null);
                            } else {
                              // Stop any other playing audio first
                              if (playingAudio) {
                                speechSynthesis.cancel();
                                const audioElements = document.querySelectorAll('audio');
                                audioElements.forEach(audio => {
                                  audio.pause();
                                  audio.currentTime = 0;
                                });
                              }

                              if (msg.ttsPath) {
                                const ttsUrl = msg.ttsPath.startsWith('/')
                                  ? `http://localhost:8000${msg.ttsPath}`
                                  : msg.ttsPath;
                                const audio = new Audio(ttsUrl);
                                audio.addEventListener('ended', () => setPlayingAudio(null));
                                audio.addEventListener('error', () => setPlayingAudio(null));
                                audio.play().catch(err => {
                                  console.error('TTS playback failed', err);
                                  setPlayingAudio(null);
                                });
                                setPlayingAudio(msg.id);
                              } else {
                                // Fallback: use browser's built-in speech synthesis
                                const utterance = new SpeechSynthesisUtterance(msg.content);
                                utterance.addEventListener('end', () => setPlayingAudio(null));
                                utterance.addEventListener('error', () => setPlayingAudio(null));
                                speechSynthesis.speak(utterance);
                                setPlayingAudio(msg.id);
                              }
                            }
                          }}
                          className={`px-3 py-1.5 rounded-full text-xs font-medium transition-all duration-200 transform hover:scale-105 ${
                            playingAudio === msg.id 
                              ? 'bg-red-100 text-red-600 hover:bg-red-200 shadow-sm' 
                              : 'bg-teal-50 text-teal-600 hover:bg-teal-100 shadow-sm'
                          }`}
                          title={playingAudio === msg.id ? "Stop Audio" : (msg.ttsPath ? "Play TTS Audio" : "Play with Browser TTS")}
                        >
                          {playingAudio === msg.id ? "⏹️ Stop" : (msg.ttsPath ? "🔊 Play" : "🔊 Speak")}
                        </button>
                      </div>
                      
                      <div className="flex items-center space-x-1">
                        <span className="text-xs text-gray-500 dark:text-gray-400 mr-2">Helpful?</span>
                        <button
                          onClick={() => handleFeedback(msg.id, true)}
                          className={`p-2 rounded-full transition-all duration-200 transform hover:scale-110 ${
                            msg.helpful === true 
                              ? 'bg-green-100 text-green-600 shadow-sm' 
                              : 'hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-400 hover:text-green-500'
                          }`}
                        >
                          <ThumbsUp className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleFeedback(msg.id, false)}
                          className={`p-2 rounded-full transition-all duration-200 transform hover:scale-110 ${
                            msg.helpful === false 
                              ? 'bg-red-100 text-red-600 shadow-sm' 
                              : 'hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-400 hover:text-red-500'
                          }`}
                        >
                          <ThumbsDown className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))}

            {isTyping && (
              <div className="flex justify-start animate-fade-in">
                <div className="bg-white dark:bg-gray-800 text-gray-900 dark:text-white border border-gray-100 dark:border-gray-700 rounded-3xl px-5 py-4 shadow-lg shadow-gray-200/50 dark:shadow-gray-800/50">
                  <div className="flex items-center space-x-3">
                    <div className="w-6 h-6 bg-gradient-to-br from-teal-400 to-blue-500 rounded-full flex items-center justify-center">
                      <span className="text-white text-xs font-bold">🤖</span>
                    </div>
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-teal-400 rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-teal-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                      <div className="w-2 h-2 bg-teal-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                    </div>
                    <span className="text-xs text-teal-600 dark:text-teal-400 font-medium">Assistant is typing...</span>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Message Input */}
          <div className="bg-white dark:bg-gray-800 border-t border-gray-100 dark:border-gray-700 p-6">
            <form onSubmit={handleSendMessage} className="flex space-x-4">
              <div className="flex-1 relative">
                <input
                  type="text"
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  placeholder="Type your message..."
                  className="w-full px-6 py-4 border border-gray-200 dark:border-gray-600 rounded-2xl focus:ring-2 focus:ring-teal-500 focus:border-transparent bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 transition-all duration-200 shadow-sm hover:shadow-md"
                />
                <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                  <button
                    type="button"
                    className="p-2 text-gray-400 hover:text-teal-500 transition-colors duration-200"
                    title="Voice input (coming soon)"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                    </svg>
                  </button>
                </div>
              </div>
              <button
                type="submit"
                disabled={!message.trim() || isTyping}
                className="bg-gradient-to-r from-teal-500 to-blue-600 text-white px-6 py-4 rounded-2xl hover:from-teal-600 hover:to-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 transform hover:scale-105 shadow-lg shadow-teal-500/25"
              >
                <Send className="w-5 h-5" />
              </button>
            </form>
          </div>
        </div>

        {/* Sidebar - Fixed height container with scroll */}
        <div className="w-80 bg-white dark:bg-gray-800 border-l border-gray-200 dark:border-gray-700 flex flex-col h-full">
          <div className="p-4 flex-1 overflow-y-auto">
            {/* FAQs */}
            <div className="mb-6">
              <div className="flex items-center space-x-2 mb-4">
                <HelpCircle className="w-5 h-5 text-teal-600" />
                <h3 className="font-semibold text-gray-900 dark:text-white">Frequently Asked</h3>
              </div>
              <div className="space-y-3">
                {faqs.length === 0 ? (
                  <div className="text-sm text-gray-500 dark:text-gray-400 p-3 bg-gray-50 dark:bg-gray-700 rounded-xl">
                    No FAQs yet — ask something to generate suggestions.
                  </div>
                ) : (
                  <div className="space-y-3">
                    {faqs.map((faq, index) => (
                      <button
                        key={index}
                        onClick={() => setMessage(faq)}
                        className="w-full text-left p-3 text-sm text-gray-700 dark:text-gray-300 hover:bg-teal-50 dark:hover:bg-teal-900/20 rounded-xl border border-gray-200 dark:border-gray-600 transition-all duration-200 hover:shadow-sm"
                      >
                        {faq}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Quick Actions */}
            <div className="mb-6">
              <div className="flex items-center space-x-2 mb-4">
                <MessageSquare className="w-5 h-5 text-teal-600" />
                <h3 className="font-semibold text-gray-900 dark:text-white">Quick Actions</h3>
              </div>
              <div className="space-y-3">
                <button
                  onClick={() => setShowTicketModal(true)}
                  className="w-full flex items-center space-x-3 p-3 text-sm text-gray-700 dark:text-gray-300 hover:bg-orange-50 dark:hover:bg-orange-900/20 rounded-lg border border-orange-200 dark:border-orange-800 transition-colors duration-200"
                >
                  <FileText className="w-4 h-4 text-orange-600 flex-shrink-0" />
                  <span className="text-left">Still need help? Create a Ticket</span>
                </button>
              </div>
            </div>
          </div>

          {/* Status - Fixed at bottom */}
          <div className="p-4 border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
            <div className="bg-gradient-to-br from-teal-50 to-blue-50 dark:from-teal-900/20 dark:to-blue-900/20 p-4 rounded-xl border border-teal-100 dark:border-teal-800">
              <h4 className="font-medium text-teal-900 dark:text-teal-100 mb-3 flex items-center text-sm">
                <div className="w-2 h-2 bg-green-400 rounded-full mr-2 animate-pulse"></div>
                Status
              </h4>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between items-center">
                  <span className="text-teal-700 dark:text-teal-300">Response Time:</span>
                  <span className="text-teal-900 dark:text-teal-100 font-medium">~30 seconds</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-teal-700 dark:text-teal-300">Queue Position:</span>
                  <span className="text-teal-900 dark:text-teal-100 font-medium">Active</span>
                </div>
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