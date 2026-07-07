import React, { useState, useEffect } from 'react';

const ChatInput = ({ onSend, isLoading, currentSessionId, initialMessage }) => {
  const [input, setInput] = useState('');

  // 홈에서 넘어온 초기 메시지 처리
  useEffect(() => {
    if (initialMessage) {
      setInput(initialMessage);
    }
  }, [initialMessage]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!input.trim() || isLoading || !currentSessionId) return;
    
    onSend(input);
    setInput('');
  };

  return (
    <div className="chat-input-container">
      <form className="chat-input-wrapper" onSubmit={handleSubmit}>
        <textarea
          className="chat-input-main"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="메시지를 입력하세요..."
          aria-label="메시지 입력"
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              handleSubmit(e);
            }
          }}
        />
        <button
          type="submit"
          className="chat-send-main"
          aria-label="메시지 보내기"
          disabled={isLoading || !currentSessionId || !input.trim()}
        >
          <span aria-hidden="true">➤</span>
        </button>
      </form>
    </div>
  );
};

export default ChatInput;
