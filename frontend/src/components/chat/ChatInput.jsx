import React, { useEffect, useRef, useState } from 'react';
import { ArrowUp, Loader2 as LoaderCircle, Sparkles } from 'lucide-react';

const ChatInput = ({ onSend, isLoading, isInitializing, currentSessionId, initialMessage }) => {
  const [input, setInput] = useState('');
  const inputRef = useRef(null);
  const isComposingRef = useRef(false);
  const isBusy = isLoading || isInitializing;

  useEffect(() => {
    if (initialMessage) {
      setInput(initialMessage);
      inputRef.current?.focus();
    }
  }, [initialMessage]);

  useEffect(() => {
    const textarea = inputRef.current;
    if (!textarea) return;
    textarea.style.height = 'auto';
    textarea.style.height = `${Math.min(textarea.scrollHeight, 144)}px`;
  }, [input]);

  const handleSubmit = (event) => {
    event.preventDefault();
    const question = input.trim();
    if (!question || isBusy || !currentSessionId || isComposingRef.current) return;
    onSend(question);
    setInput('');
    inputRef.current?.focus();
  };

  const handleKeyDown = (event) => {
    if (event.key !== 'Enter' || event.shiftKey) return;
    // 한글 조합을 끝내는 Enter가 메시지를 함께 전송하지 않도록 한다.
    if (event.nativeEvent.isComposing || isComposingRef.current || event.keyCode === 229) return;
    event.preventDefault();
    handleSubmit(event);
  };

  return (
    <div className="chat-input-container">
      <form className="chat-input-wrapper" onSubmit={handleSubmit}>
        <Sparkles className="chat-input-sparkle" size={19} aria-hidden="true" />
        <textarea
          ref={inputRef}
          className="chat-input-main"
          value={input}
          onChange={(event) => setInput(event.target.value)}
          onCompositionStart={() => { isComposingRef.current = true; }}
          onCompositionEnd={() => { isComposingRef.current = false; }}
          placeholder={isInitializing ? '모험을 준비하고 있어요…' : '메이플에 대해 궁금한 것을 물어보세요'}
          aria-label="메이플 AI에게 질문하기"
          aria-describedby="chatInputHelp"
          rows={1}
          onKeyDown={handleKeyDown}
          disabled={isInitializing}
        />
        <button
          type="submit"
          className="chat-send-main"
          aria-label={isBusy ? '답변 준비 중' : '질문 보내기'}
          disabled={isBusy || !currentSessionId || !input.trim()}
        >
          {isBusy ? <LoaderCircle className="chat-spinner" size={19} /> : <ArrowUp size={20} />}
        </button>
      </form>
      <div className="chat-input-footer" id="chatInputHelp">
        <span>AI의 답변은 실제 게임 정보와 다를 수 있어요.</span>
        <span className="chat-keyboard-hint"><kbd>Enter</kbd> 전송 <span>·</span> <kbd>Shift + Enter</kbd> 줄바꿈</span>
      </div>
    </div>
  );
};

export default ChatInput;
