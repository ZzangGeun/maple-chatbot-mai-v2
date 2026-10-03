import React, { useEffect, useRef, useState } from 'react';
import { Leaf, PanelLeft, Plus, Sparkles } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useLocation } from 'react-router-dom';
import Layout from '../components/common/Layout';
import { useChat } from '../hooks/useChat';
import ChatSidebar from '../components/chat/ChatSidebar';
import ChatMessages from '../components/chat/ChatMessages';
import ChatInput from '../components/chat/ChatInput';
import '../styles/pages/chat.css';

const ChatPage = () => {
  const { isLoggedIn, isAuthReady } = useAuth();
  const location = useLocation();
  const messagesEndRef = useRef(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const {
    sessions, currentSessionId, messages, isLoading, isInitializing,
    error, clearError, retryInitialization, loadMessages, createNewChat, sendMessage,
  } = useChat(isLoggedIn, isAuthReady);

  useEffect(() => {
    if (messages.length || isLoading) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  }, [messages, isLoading]);

  useEffect(() => {
    if (!isSidebarOpen) return undefined;
    const previousFocus = document.activeElement;
    const sidebar = document.getElementById('chatSidebar');
    const getFocusableButtons = () => [...(sidebar?.querySelectorAll('button:not([disabled])') || [])]
      .filter(button => button.getClientRects().length > 0);
    getFocusableButtons()[0]?.focus();
    const handleKeyDown = (event) => {
      if (event.key === 'Escape') {
        setIsSidebarOpen(false);
      } else if (event.key === 'Tab') {
        const buttons = getFocusableButtons();
        const first = buttons[0];
        const last = buttons[buttons.length - 1];
        if (event.shiftKey && document.activeElement === first) {
          event.preventDefault();
          last?.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault();
          first?.focus();
        }
      }
    };
    const handleResize = () => {
      if (window.innerWidth > 820) setIsSidebarOpen(false);
    };
    document.addEventListener('keydown', handleKeyDown);
    window.addEventListener('resize', handleResize);
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('resize', handleResize);
      previousFocus?.focus();
    };
  }, [isSidebarOpen]);

  const startNewChat = () => {
    if (isLoading || isInitializing) return;
    setIsSidebarOpen(false);
    createNewChat();
  };

  const selectSession = (sessionId) => {
    if (isLoading || isInitializing) return;
    setIsSidebarOpen(false);
    loadMessages(sessionId);
  };

  const retryError = () => {
    if (error?.kind === 'initialize') {
      retryInitialization();
    } else if (error?.kind === 'history') {
      loadMessages(currentSessionId);
    } else if (error?.kind === 'send') {
      const lastQuestion = [...messages].reverse().find(message => message.role === 'user');
      if (lastQuestion) sendMessage(lastQuestion.content, true);
    } else {
      createNewChat();
    }
  };

  return (
    <Layout
      leftSidebar={(
        <ChatSidebar
          sessions={sessions}
          currentSessionId={currentSessionId}
          handleNewChat={startNewChat}
          selectSession={selectSession}
          isBusy={isLoading || isInitializing}
          isOpen={isSidebarOpen}
          onClose={() => setIsSidebarOpen(false)}
        />
      )}
      rightSidebar={null}
      layoutClass={`chatbot-layout${isSidebarOpen ? ' chat-sidebar-open' : ''}`}
    >
      {isSidebarOpen && (
        <button
          className="chat-sidebar-backdrop"
          type="button"
          aria-label="대화 목록 닫기"
          onClick={() => setIsSidebarOpen(false)}
        />
      )}
      <section className="chat-main" aria-label="메이플 AI와 대화">
        <header className="chat-header">
          <div className="chat-header-identity">
            <button
              type="button"
              className="chat-icon-button chat-mobile-menu"
              aria-label="대화 목록 열기"
              aria-expanded={isSidebarOpen}
              aria-controls="chatSidebar"
              onClick={() => setIsSidebarOpen(true)}
            >
              <PanelLeft size={20} />
            </button>
            <div className="chat-guide-avatar" aria-hidden="true"><Leaf size={21} /></div>
            <div>
              <h1 className="chat-title">메이플 AI 가이드</h1>
              <p className="chat-subtitle">모험가의 든든한 AI 파티원</p>
            </div>
          </div>
          <div className="chat-header-actions">
            <span className="chat-ready-badge"><Sparkles size={13} /> AI 도우미</span>
            <button
              type="button"
              className="chat-icon-button"
              aria-label="새 대화 시작"
              title="새 대화 시작"
              disabled={isLoading || isInitializing}
              onClick={startNewChat}
            >
              <Plus size={20} />
            </button>
          </div>
        </header>

        <ChatMessages
          messages={messages}
          isLoading={isLoading}
          isInitializing={isInitializing}
          messagesEndRef={messagesEndRef}
          onSuggest={sendMessage}
          canSend={Boolean(currentSessionId) && !isLoading && !isInitializing}
          error={error}
          onRetry={retryError}
          onDismissError={clearError}
        />

        <ChatInput
          onSend={sendMessage}
          isLoading={isLoading}
          isInitializing={isInitializing}
          currentSessionId={currentSessionId}
          initialMessage={location.state?.initialMessage}
        />
      </section>
    </Layout>
  );
};

export default ChatPage;
