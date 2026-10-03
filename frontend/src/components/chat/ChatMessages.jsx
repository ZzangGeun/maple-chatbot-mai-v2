import React, { useEffect, useState } from 'react';
import { AlertCircle, ArrowUpRight, ChevronDown, Compass, Gem, Leaf, RotateCcw, Sparkles, Swords, UserRound, X } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const SUGGESTIONS = [
  { icon: Compass, title: '어디서 사냥할까요?', detail: '레벨에 맞는 사냥터 찾기', question: '레벨 200 이후에는 어떤 사냥터에서 육성하면 좋을까?', color: 'green' },
  { icon: Swords, title: '보스 공략이 궁금해요', detail: '첫 도전을 위한 준비', question: '보스를 처음 도전하는데, 어떤 순서로 준비하면 좋을까?', color: 'orange' },
  { icon: Gem, title: '장비를 바꿔볼까요?', detail: '알뜰하게 강해지는 방법', question: '메이플 초보자가 장비를 맞출 때 무엇부터 신경 써야 할까?', color: 'purple' },
];

const GuideMascot = () => (
  <div className="chat-mascot-scene" aria-hidden="true">
    <Sparkles className="chat-mascot-sparkle chat-mascot-sparkle-one" size={20} />
    <Sparkles className="chat-mascot-sparkle chat-mascot-sparkle-two" size={14} />
    <div className="chat-mascot">
      <div className="chat-mascot-cap"><i /><i /><i /></div>
      <div className="chat-mascot-face"><span className="chat-mascot-eye" /><span className="chat-mascot-smile" /><span className="chat-mascot-eye" /></div>
      <div className="chat-mascot-feet"><i /><i /></div>
    </div>
    <span className="chat-mascot-shadow" />
    <span className="chat-mascot-leaf"><Leaf size={17} /></span>
  </div>
);

const TypingIndicator = ({ initializing = false }) => (
  <div className="chat-typing" role="status">
    <span className="chat-typing-dots" aria-hidden="true"><i /><i /><i /></span>
    <span>{initializing ? '모험을 준비하고 있어요' : '가이드가 답변을 준비하고 있어요'}</span>
  </div>
);

const ChatMessages = ({ messages, isLoading, isInitializing, messagesEndRef, onSuggest, canSend, error, onRetry, onDismissError }) => {
  const [expandedThinking, setExpandedThinking] = useState({});

  useEffect(() => {
    if (messages.length === 0) setExpandedThinking({});
  }, [messages]);

  const lastMessage = messages[messages.length - 1];

  return (
    <div className="chat-messages" id="chatMessages" aria-busy={isLoading || isInitializing}>
      {messages.length === 0 && (
        <div className="chat-welcome">
          <GuideMascot />
          <span className="chat-welcome-eyebrow"><Sparkles size={13} /> 오늘의 모험도 함께해요</span>
          <h2>어떤 모험을 도와드릴까요?</h2>
          <p>사냥터부터 장비, 보스 공략까지.<br />메이플의 궁금한 이야기를 들려주세요.</p>
          <div className="chat-suggestions">
            {SUGGESTIONS.map(({ icon: Icon, title, detail, question, color }) => (
              <button type="button" key={title} className={`chat-suggestion ${color}`} disabled={!canSend} onClick={() => onSuggest(question)}>
                <span className="chat-suggestion-icon"><Icon size={20} /></span>
                <span className="chat-suggestion-copy"><strong>{title}</strong><span>{detail}</span></span>
                <ArrowUpRight className="chat-suggestion-arrow" size={16} />
              </button>
            ))}
          </div>
          {isInitializing && <TypingIndicator initializing />}
        </div>
      )}

      {messages.map((message, index) => {
        const isUser = message.role === 'user';
        const messageKey = message.id ?? index;
        return (
          <article key={messageKey} className={`chat-message ${isUser ? 'user' : 'bot'}${message.isError ? ' has-error' : ''}`}>
            <div className="chat-message-avatar" aria-hidden="true">{isUser ? <UserRound size={18} /> : <Leaf size={19} />}</div>
            <div className="chat-message-body">
              <span className="chat-message-name">{isUser ? '나의 질문' : '메이플 AI 가이드'}</span>
              <div className="chat-message-content">
                {!isUser && !message.content ? (
                  message.isError ? <p>답변을 가져오지 못했어요. 다시 시도해 주세요.</p> : <TypingIndicator />
                ) : (
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
                )}
                {!isUser && message.thinking && (
                  <div className="chat-thinking">
                    <button
                      type="button"
                      className="chat-thinking-toggle"
                      aria-expanded={Boolean(expandedThinking[messageKey])}
                      onClick={() => setExpandedThinking(previous => ({ ...previous, [messageKey]: !previous[messageKey] }))}
                    >
                      <Sparkles size={13} /> 답변의 사고 과정 <ChevronDown className={expandedThinking[messageKey] ? 'is-expanded' : ''} size={14} />
                    </button>
                    {expandedThinking[messageKey] && (
                      <div className="chat-thinking-content"><ReactMarkdown remarkPlugins={[remarkGfm]}>{message.thinking}</ReactMarkdown></div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </article>
        );
      })}

      {isLoading && !isInitializing && lastMessage?.role !== 'assistant' && (
        <div className="chat-message bot">
          <div className="chat-message-avatar" aria-hidden="true"><Leaf size={19} /></div>
          <div className="chat-message-body"><div className="chat-message-content"><TypingIndicator /></div></div>
        </div>
      )}

      {error && (
        <div className="chat-error" role="alert">
          <AlertCircle size={18} />
          <div><strong>잠시 모험이 멈췄어요</strong><p>{error.message}</p></div>
          <button className="chat-error-retry" type="button" onClick={onRetry} disabled={isLoading || isInitializing}><RotateCcw size={14} /> 다시 시도</button>
          <button className="chat-error-dismiss" type="button" aria-label="오류 안내 닫기" onClick={onDismissError}><X size={16} /></button>
        </div>
      )}
      <div className="chat-scroll-anchor" ref={messagesEndRef} />
    </div>
  );
};

export default ChatMessages;
