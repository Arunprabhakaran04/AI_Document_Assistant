import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Send, Upload, Plus, Trash2, LogOut, FileText, AlertCircle, CheckCircle, Loader, User, Bot } from 'lucide-react';

const API_URL = "http://127.0.0.1:8000";

const App = () => {
  // State management
  const [authToken, setAuthToken] = useState(localStorage.getItem('authToken'));
  const [email, setEmail] = useState(localStorage.getItem('email'));
  const [messages, setMessages] = useState([]);
  const [chatId, setChatId] = useState(null);
  const [chatTitles, setChatTitles] = useState([]);
  const [hasPdf, setHasPdf] = useState(false);
  const [pdfFilename, setPdfFilename] = useState(null);
  const [uploadTimestamp, setUploadTimestamp] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState(null);
  const [currentView, setCurrentView] = useState('login');
  const [inputMessage, setInputMessage] = useState('');
  
  // Form states
  const [loginForm, setLoginForm] = useState({ email: '', password: '' });
  const [registerForm, setRegisterForm] = useState({ email: '', password: '' });
  
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);

  // API call helper
  const apiCall = useCallback(async (endpoint, options = {}) => {
    const headers = {
      'Content-Type': 'application/json',
      ...(authToken && { Authorization: `Bearer ${authToken}` }),
      ...options.headers
    };

    try {
      const response = await fetch(`${API_URL}${endpoint}`, {
        ...options,
        headers
      });
      return response;
    } catch (error) {
      console.error('API call failed:', error);
      throw error;
    }
  }, [authToken]);

  // Load chat titles helper
  const loadChatTitles = useCallback(async () => {
    try {
      const response = await apiCall('/list_chats');
      if (response.status === 200) {
        const data = await response.json();
        setChatTitles(data.chats || []);
      }
    } catch (error) {
      console.error('Error loading chat titles:', error);
    }
  }, [apiCall]);

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    if (authToken) {
      loadChatTitles();
    }
  }, [authToken, loadChatTitles]);

  const register = async () => {
    if (!registerForm.email || !registerForm.password) {
      alert('Please fill in all fields');
      return;
    }

    try {
      const response = await apiCall('/register', {
        method: 'POST',
        body: JSON.stringify(registerForm)
      });

      if (response.status === 201) {
        alert('Account created successfully! Please login.');
        setCurrentView('login');
      } else {
        const error = await response.json();
        alert(`Registration failed: ${error.detail || 'Unknown error'}`);
      }
    } catch (error) {
      alert('Unable to connect to server');
    }
  };

  const login = async () => {
    if (!loginForm.email || !loginForm.password) {
      alert('Please fill in all fields');
      return;
    }

    try {
      const response = await apiCall('/login', {
        method: 'POST',
        body: JSON.stringify(loginForm)
      });

      if (response.status === 200) {
        const data = await response.json();
        setAuthToken(data.access_token);
        setEmail(loginForm.email);
        localStorage.setItem('authToken', data.access_token);
        localStorage.setItem('email', loginForm.email);
        loadChatTitles();
      } else {
        const error = await response.json();
        alert(`Login failed: ${error.detail || 'Invalid credentials'}`);
      }
    } catch (error) {
      alert('Unable to connect to server');
    }
  };

  const logout = async () => {
    try {
      // Always try to clean up server-side data, regardless of hasPdf state
      const response = await apiCall('/logout', {
        method: 'POST'
      });
      
      if (response.ok) {
        console.log('Server-side cleanup successful');
      } else {
        console.error('Server-side cleanup failed:', await response.text());
      }
    } catch (error) {
      console.error('Failed to clean up server-side data:', error);
    } finally {
      // Clear local state regardless of server cleanup success
      setAuthToken(null);
      setEmail(null);
      setMessages([]);
      setChatId(null);
      setChatTitles([]);
      setHasPdf(false);
      setPdfFilename(null);
      setUploadTimestamp(null);
      localStorage.removeItem('authToken');
      localStorage.removeItem('email');
      setCurrentView('login');
    }
  };

  const loadChatMessages = async (chatIdToLoad) => {
    try {
      const response = await apiCall(`/chat_history/${chatIdToLoad}`);
      if (response.status === 200) {
        const data = await response.json();
        const formattedMessages = data.messages.map(msg => ({
          role: msg.role,
          content: msg.content + (msg.role === 'assistant' && msg.source 
            ? `\n\n*${msg.source === 'rag' ? 'Answer based on your uploaded document' : 'General AI response'}*`
            : '')
        }));
        setChatId(chatIdToLoad);
        setMessages(formattedMessages);
      }
    } catch (error) {
      alert('Failed to load chat history');
    }
  };

  const deleteChat = async (chatIdToDelete) => {
    if (!window.confirm('Are you sure you want to delete this chat?')) return;

    try {
      const response = await apiCall(`/chat/${chatIdToDelete}`, { method: 'DELETE' });
      if (response.status === 200) {
        loadChatTitles();
        if (chatId === chatIdToDelete) {
          setChatId(null);
          setMessages([]);
        }
      }
    } catch (error) {
      alert('Failed to delete chat');
    }
  };

  const uploadPdf = async (file) => {
    if (!file) return;

    setUploadStatus('uploading');
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${API_URL}/upload_pdf`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${authToken}` },
        body: formData
      });

      if (response.status === 202) {
        const data = await response.json();
        const taskId = data.task_id;
        
        // Poll for task status
        const pollStatus = async () => {
          let attempts = 0;
          const maxAttempts = 180;
          const pollInterval = 1000; // 1 second

          const poll = async () => {
            if (attempts >= maxAttempts) {
              setUploadStatus('error');
              alert('PDF processing timed out. Please try again.');
              return;
            }

            try {
              const statusResponse = await apiCall(`/task_status/${taskId}`);
              if (!statusResponse.ok) {
                throw new Error(`HTTP error! status: ${statusResponse.status}`);
              }
              
              const statusData = await statusResponse.json();
              console.log('Task status:', statusData); // Debug log
              
              switch(statusData.status?.toLowerCase()) {
                case 'completed':
                  setHasPdf(true);
                  setPdfFilename(file.name);
                  setUploadTimestamp(new Date().toISOString());
                  setUploadStatus('success');
                  return;
                case 'failed':
                  setUploadStatus('error');
                  alert(`Processing failed: ${statusData.message || 'Unknown error'}`);
                  return;
                case 'pending':
                case 'processing':
                  attempts++;
                  setTimeout(poll, pollInterval);
                  break;
                default:
                  setUploadStatus('error');
                  alert(`Unknown status: ${statusData.status}`);
                  return;
              }
            } catch (error) {
              console.error('Error checking task status:', error);
              setUploadStatus('error');
              alert('Failed to check processing status. Please try again.');
              return;
            }
          };

          await poll();
        };
        
        pollStatus();
      } else {
        setUploadStatus('error');
        const error = await response.json();
        alert(`Upload failed: ${error.detail || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Upload error:', error);
      setUploadStatus('error');
      alert('Unable to connect to server');
    }
  };

  const sendMessage = async () => {
    if (!inputMessage.trim()) return;

    const currentChatId = chatId || generateChatId();
    if (!chatId) setChatId(currentChatId);

    const userMessage = { role: 'user', content: inputMessage };
    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      const response = await apiCall('/chat', {
        method: 'POST',
        body: JSON.stringify({
          query: inputMessage,
          chat_id: currentChatId,
          has_pdf: hasPdf
        })
      });

      if (response.status === 200) {
        const data = await response.json();
        let reply = data.response;
        
        if (typeof reply === 'object') {
          reply = reply.result || Object.values(reply).find(v => typeof v === 'string') || '[No response]';
        }

        const source = data.source;
        if (source === 'rag') {
          reply += '\n\n*Answer based on your uploaded document*';
        } else if (source === 'general') {
          reply += '\n\n*General AI response*';
        }

        setMessages(prev => [...prev, { role: 'assistant', content: reply }]);
        loadChatTitles();
      } else {
        const error = await response.json();
        setMessages(prev => [...prev, { 
          role: 'assistant', 
          content: `Error: ${response.status} - ${error.detail || 'Something went wrong'}` 
        }]);
      }
    } catch (error) {
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: `Unable to connect to server: ${error.message}` 
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const generateChatId = () => {
    return Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
  };

  const newChat = () => {
    setChatId(generateChatId());
    setMessages([]);
  };

  const clearPdf = async () => {
    try {
      // Call the logout endpoint to clean up server-side data
      const response = await apiCall('/logout', {
        method: 'POST'
      });
      
      if (response.ok) {
        console.log('Server-side PDF data cleanup successful');
        // Clear local state only after successful server cleanup
        setHasPdf(false);
        setPdfFilename(null);
        setUploadTimestamp(null);
        setUploadStatus(null);
      } else {
        console.error('Server-side PDF cleanup failed:', await response.text());
        alert('Failed to clear PDF data on server. Please try again.');
      }
    } catch (error) {
      console.error('Failed to clear PDF data:', error);
      alert('Failed to clear PDF data. Please try again.');
    }
  };

  if (!authToken) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="bg-gray-800 p-8 rounded-lg shadow-xl w-full max-w-md">
          <h1 className="text-3xl font-bold text-white mb-8 text-center">AI Assistant</h1>
          
          <div className="flex mb-6">
            <button
              onClick={() => setCurrentView('login')}
              className={`flex-1 py-2 px-4 rounded-l-lg ${
                currentView === 'login' 
                  ? 'bg-blue-600 text-white' 
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              Login
            </button>
            <button
              onClick={() => setCurrentView('register')}
              className={`flex-1 py-2 px-4 rounded-r-lg ${
                currentView === 'register' 
                  ? 'bg-blue-600 text-white' 
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              Register
            </button>
          </div>

          {currentView === 'login' ? (
            <div className="space-y-4">
              <input
                type="email"
                placeholder="Email"
                value={loginForm.email}
                onChange={(e) => setLoginForm({...loginForm, email: e.target.value})}
                className="w-full p-3 bg-gray-700 text-white rounded-lg border border-gray-600 focus:border-blue-500 focus:outline-none"
              />
              <input
                type="password"
                placeholder="Password"
                value={loginForm.password}
                onChange={(e) => setLoginForm({...loginForm, password: e.target.value})}
                className="w-full p-3 bg-gray-700 text-white rounded-lg border border-gray-600 focus:border-blue-500 focus:outline-none"
              />
              <button
                onClick={login}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white py-3 rounded-lg font-semibold transition-colors"
              >
                Sign In
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              <input
                type="email"
                placeholder="Email"
                value={registerForm.email}
                onChange={(e) => setRegisterForm({...registerForm, email: e.target.value})}
                className="w-full p-3 bg-gray-700 text-white rounded-lg border border-gray-600 focus:border-blue-500 focus:outline-none"
              />
              <input
                type="password"
                placeholder="Password"
                value={registerForm.password}
                onChange={(e) => setRegisterForm({...registerForm, password: e.target.value})}
                className="w-full p-3 bg-gray-700 text-white rounded-lg border border-gray-600 focus:border-blue-500 focus:outline-none"
              />
              <button
                onClick={register}
                className="w-full bg-green-600 hover:bg-green-700 text-white py-3 rounded-lg font-semibold transition-colors"
              >
                Create Account
              </button>
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 flex">
      {/* Sidebar */}
      <div className="w-80 bg-gray-800 border-r border-gray-700 flex flex-col h-screen">
        <div className="p-4 border-b border-gray-700 flex-shrink-0">
          <h1 className="text-xl font-bold text-white mb-2">AI Assistant</h1>
          <p className="text-gray-400 text-sm">Welcome, {email}</p>
          <button
            onClick={logout}
            className="flex items-center gap-2 mt-3 text-red-400 hover:text-red-300 text-sm"
          >
            <LogOut size={16} /> Logout
          </button>
        </div>

        {/* PDF Upload Section */}
        <div className="p-4 border-b border-gray-700 flex-shrink-0">
          <h3 className="text-white font-semibold mb-3">Document Upload</h3>
          
          {hasPdf ? (
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-green-400">
                <CheckCircle size={16} />
                <span className="text-sm">PDF Active</span>
              </div>
              <p className="text-gray-300 text-sm truncate">{pdfFilename}</p>
              {uploadTimestamp && (
                <p className="text-gray-500 text-xs">
                  {new Date(uploadTimestamp).toLocaleString()}
                </p>
              )}
              <button
                onClick={clearPdf}
                className="text-red-400 hover:text-red-300 text-sm"
              >
                Clear PDF
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-2 text-yellow-400 mb-3">
              <AlertCircle size={16} />
              <span className="text-sm">No PDF uploaded</span>
            </div>
          )}

          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf"
            onChange={(e) => e.target.files[0] && uploadPdf(e.target.files[0])}
            className="hidden"
          />
          
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={uploadStatus === 'uploading'}
            className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white py-2 px-4 rounded-lg flex items-center justify-center gap-2 transition-colors"
          >
            {uploadStatus === 'uploading' ? (
              <>
                <Loader className="animate-spin" size={16} />
                Processing...
              </>
            ) : (
              <>
                <Upload size={16} />
                Upload PDF
              </>
            )}
          </button>
        </div>

        {/* Chat Management */}
        <div className="p-4 border-b border-gray-700 flex-shrink-0">
          <button
            onClick={newChat}
            className="w-full bg-green-600 hover:bg-green-700 text-white py-2 px-4 rounded-lg flex items-center justify-center gap-2 transition-colors"
          >
            <Plus size={16} />
            New Chat
          </button>
        </div>

        {/* Previous Chats - Fixed height with scrolling */}
        <div className="flex-1 min-h-0 flex flex-col">
          {chatTitles.length > 0 && (
            <>
              <div className="p-4 pb-2 flex-shrink-0">
                <h3 className="text-white font-semibold">Previous Chats</h3>
              </div>
              <div className="flex-1 overflow-y-auto px-4 pb-4 min-h-0">
                <div className="space-y-2">
                  {chatTitles.map((chat) => (
                    <div key={chat.chat_id} className="flex items-center gap-2">
                      <button
                        onClick={() => loadChatMessages(chat.chat_id)}
                        className="flex-1 text-left p-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg truncate transition-colors"
                      >
                        {chat.title}
                      </button>
                      <button
                        onClick={() => deleteChat(chat.chat_id)}
                        className="p-2 text-red-400 hover:text-red-300 hover:bg-gray-700 rounded-lg transition-colors flex-shrink-0"
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col h-screen">
        <div className="p-4 border-b border-gray-700 bg-gray-800 flex-shrink-0">
          <h2 className="text-xl font-bold text-white">Chat Assistant</h2>
          {chatId && (
            <p className="text-gray-400 text-sm">Chat ID: {chatId.substring(0, 8)}...</p>
          )}
          
          {hasPdf ? (
            <div className="flex items-center gap-2 mt-2 text-blue-400">
              <FileText size={16} />
              <span className="text-sm">PDF Active: {pdfFilename}</span>
            </div>
          ) : (
            <div className="flex items-center gap-2 mt-2 text-yellow-400">
              <AlertCircle size={16} />
              <span className="text-sm">No PDF uploaded - Using general AI</span>
            </div>
          )}
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((message, index) => (
            <div key={index} className={`flex gap-3 ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              {message.role === 'assistant' && (
                <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center flex-shrink-0">
                  <Bot size={16} className="text-white" />
                </div>
              )}
              <div className={`max-w-[70%] p-3 rounded-lg ${
                message.role === 'user' 
                  ? 'bg-blue-600 text-white' 
                  : 'bg-gray-700 text-gray-100'
              }`}>
                <div className="whitespace-pre-wrap">{message.content}</div>
              </div>
              {message.role === 'user' && (
                <div className="w-8 h-8 bg-green-600 rounded-full flex items-center justify-center flex-shrink-0">
                  <User size={16} className="text-white" />
                </div>
              )}
            </div>
          ))}
          
          {isLoading && (
            <div className="flex gap-3">
              <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
                <Bot size={16} className="text-white" />
              </div>
              <div className="bg-gray-700 p-3 rounded-lg">
                <div className="flex items-center gap-2 text-gray-300">
                  <Loader className="animate-spin" size={16} />
                  Thinking...
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Input - Fixed at bottom */}
        <div className="p-4 border-t border-gray-700 bg-gray-800 flex-shrink-0">
          <div className="flex gap-3">
            <input
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && !isLoading && sendMessage()}
              placeholder="Ask me anything..."
              className="flex-1 p-3 bg-gray-700 text-white rounded-lg border border-gray-600 focus:border-blue-500 focus:outline-none"
              disabled={isLoading}
            />
            <button
              onClick={sendMessage}
              disabled={isLoading || !inputMessage.trim()}
              className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white p-3 rounded-lg transition-colors"
            >
              <Send size={20} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default App;