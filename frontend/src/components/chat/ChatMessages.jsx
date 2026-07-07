import React, { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const ChatMessages = ({ messages, isLoading, messagesEndRef }) => {
  const [expandedThinking, setExpandedThinking] = useState({});

  // Reset expanded thinking when messages change drastically (e.g. session change)
  useEffect(() => {
    if (messages.length === 0) {
      setExpandedThinking({});
    }
  }, [messages]);

  return (
    <div className="chat-messages" id="chatMessages">
      {messages.length === 0 && !isLoading && (
        <div className="welcome-message">
          <div className="welcome-icon">🧚‍♀️</div>
          <div className="welcome-text">안녕하세요! 무엇을 도와드릴까요?</div>
          <div className="welcome-subtext">메이플스토리에 대해 궁금한 점을 물어보세요.</div>
        </div>
      )}

      {messages.map((msg, idx) => (
        <div
          key={idx}
          className={`message ${msg.role === 'user' ? 'user' : 'bot'}`}
        >
          <div className="message-avatar">
            {msg.role === 'user' ? '👤' : '🧚‍♀️'}
          </div>
          <div className="message-content">
            {msg.role === 'assistant' && !msg.content ? (
              <div className="typing-dots">
                <div className="typing-dot"></div>
                <div className="typing-dot"></div>
                <div className="typing-dot"></div>
              </div>
            ) : (
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {msg.content}
              </ReactMarkdown>
            )}
            
            {msg.role === 'assistant' && msg.thinking && (
              <div className="thinking-container">
                <button
                  className="thinking-toggle"
                  onClick={() => setExpandedThinking(prev => ({
                    ...prev,
                    [idx]: !prev[idx]
                  }))}
                >
                  <span
                    className={`thinking-toggle-icon ${expandedThinking[idx] ? 'expanded' : ''}`}
                    aria-hidden="true"
                  >
                    🧠
                  </span>
                  {expandedThinking[idx] ? '사고 과정 숨기기' : '사고 과정 보기'}
                </button>
                {expandedThinking[idx] && (
                  <div className="thinking-content">
                    <div className="thinking-label">
                      <span className="thinking-label-icon">💭</span>
                      AI의 추론 과정
                    </div>
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {msg.thinking}
                    </ReactMarkdown>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      ))}

      {isLoading && (messages.length === 0 || messages[messages.length - 1].role !== 'assistant') && (
        <div className="message bot">
          <div className="message-avatar">🧚‍♀️</div>
          <div className="message-content">
            <div className="typing-dots">
              <div className="typing-dot"></div>
              <div className="typing-dot"></div>
              <div className="typing-dot"></div>
            </div>
          </div>
        </div>
      )}
      <div ref={messagesEndRef} />
    </div>
  );
};

export default ChatMessages;
