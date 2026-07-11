import React, { useEffect, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import { useLocation } from 'react-router-dom';
import Layout from '../components/common/Layout';
import { useChat } from '../hooks/useChat';

import ChatSidebar from '../components/chat/ChatSidebar';
import ChatMessages from '../components/chat/ChatMessages';
import ChatInput from '../components/chat/ChatInput';
import ChatAdSidebar from '../components/chat/ChatAdSidebar';

import '../styles/pages/chat.css';

const ChatPage = () => {
  const { isLoggedIn } = useAuth();
  const location = useLocation();
  const messagesEndRef = useRef(null);

  const {
    sessions,
    currentSessionId,
    messages,
    isLoading,
    loadMessages,
    createNewChat,
    sendMessage
  } = useChat(isLoggedIn);

  // 스크롤 자동 이동
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <Layout
      leftSidebar={
        <ChatSidebar 
          sessions={sessions}
          currentSessionId={currentSessionId}
          handleNewChat={createNewChat}
          selectSession={loadMessages}
        />
      }
      rightSidebar={<ChatAdSidebar />}
      layoutClass="chatbot-layout"
    >
      <div className="chat-main">
        <div className="chat-header">
          <div className="chat-title">MAI HELP YOU</div>
          <div className="chat-subtitle">메이플스토리 AI 챗봇</div>
        </div>

        <ChatMessages 
          messages={messages} 
          isLoading={isLoading} 
          messagesEndRef={messagesEndRef} 
        />

        <ChatInput 
          onSend={sendMessage} 
          isLoading={isLoading} 
          currentSessionId={currentSessionId} 
          initialMessage={location.state?.initialMessage} 
        />
      </div>
    </Layout>
  );
};

export default ChatPage;
