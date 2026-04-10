import { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Loader2, Sparkles, AlertCircle } from 'lucide-react';
import './Chat.css';

export default function Chat() {
  const [messages, setMessages] = useState([
    { id: 1, role: 'assistant', content: 'Hello! I am your Medical Literature Assistant. Upload some PDFs to the system, and ask me anything about their contents.' }
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage = { id: Date.now(), role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsTyping(true);

    // Initial placeholder for the streaming response
    const assistantMsgId = Date.now() + 1;
    setMessages(prev => [...prev, { id: assistantMsgId, role: 'assistant', content: '' }]);

    try {
      const response = await fetch("http://localhost:8000/api/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: userMessage.content })
      });

      if (!response.ok) {
        throw new Error('Network response was not ok');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value, { stream: true });
        
        setMessages(prev => prev.map(msg => {
          if (msg.id === assistantMsgId) {
            return { ...msg, content: msg.content + chunk };
          }
          return msg;
        }));
      }
    } catch (error) {
      console.error("Error fetching stream:", error);
      setMessages(prev => prev.map(msg => {
        if (msg.id === assistantMsgId) {
          return { ...msg, content: "Error communicating with the backend. Ensure FastAPI is running on port 8000.", isError: true };
        }
        return msg;
      }));
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <main className="chat-container glass-panel animate-fade-in" style={{ animationDelay: '0.1s' }}>
      <div className="chat-header">
        <Sparkles className="header-icon" />
        <div>
          <h2>Gemini-Assisted Analysis</h2>
          <p>Powered by Google AI & Milvus Vector Search</p>
        </div>
      </div>
      
      <div className="messages-area">
        {messages.map((msg) => (
          <div key={msg.id} className={`message-wrapper ${msg.role}`}>
            <div className="avatar">
              {msg.role === 'assistant' ? <Bot size={20} /> : <User size={20} />}
            </div>
            <div className={`message-bubble ${msg.isError ? 'error-bubble' : ''}`}>
              {msg.content || (msg.role === 'assistant' && isTyping ? <span className="typing-indicator">...</span> : '')}
            </div>
          </div>
        ))}
        {isTyping && messages[messages.length - 1].role !== 'assistant' && (
          <div className="message-wrapper assistant">
             <div className="avatar"><Bot size={20} /></div>
             <div className="message-bubble typing"><Loader2 className="spinner" size={16}/> Thinking...</div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <form className="input-area" onSubmit={handleSubmit}>
        <input 
          type="text" 
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a medical question..."
          disabled={isTyping}
        />
        <button type="submit" className="send-btn" disabled={!input.trim() || isTyping}>
          <Send size={18} />
        </button>
      </form>
    </main>
  );
}
