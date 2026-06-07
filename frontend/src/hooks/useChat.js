import { useState, useEffect, useCallback } from 'react';
import * as chatApi from '../api/chat';

export const useChat = (isLoggedIn) => {
  const [sessions, setSessions] = useState([]);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isInitializing, setIsInitializing] = useState(true);

  // 세션의 메시지 가져오기
  const loadMessages = useCallback(async (sessionId) => {
    setCurrentSessionId(sessionId);
    setIsLoading(true);
    try {
      const response = await chatApi.getMessages(sessionId);
      const messageData = response.data.messages || response.data.data || [];
      const formattedMessages = messageData.map(msg => ({
        role: msg.sender_type || msg.role,
        content: msg.message_content || msg.content,
        thinking: msg.thinking || ''
      }));
      setMessages(formattedMessages);
    } catch (error) {
      console.error("Failed to load messages:", error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // 새 채팅방 생성
  const createNewChat = useCallback(async () => {
    try {
      const response = await chatApi.createSession();
      const newSession = response.data.room || response.data.data;
      setSessions(prev => [newSession, ...prev]);
      setCurrentSessionId(newSession.id);
      setMessages([]);
      return newSession.id;
    } catch (error) {
      console.error("Failed to create session:", error);
      const tempSessionId = 'temp-' + Date.now();
      setCurrentSessionId(tempSessionId);
      setMessages([]);
      return tempSessionId;
    }
  }, []);

  // 초기 로드: 세션 목록 가져오기 및 처리
  useEffect(() => {
    const initializeChat = async () => {
      try {
        let sessionList = [];

        if (isLoggedIn) {
          try {
            const response = await chatApi.getSessions();
            sessionList = response.data.rooms || response.data.data || [];
          } catch (error) {
            console.error("Failed to load sessions:", error);
          }
        }

        setSessions(sessionList);

        if (isLoggedIn && sessionList.length > 0) {
          await loadMessages(sessionList[0].id);
        } else {
          await createNewChat();
        }
      } catch (error) {
        console.error("Chat initialization failed:", error);
        const tempSessionId = 'temp-' + Date.now();
        setCurrentSessionId(tempSessionId);
      } finally {
        setIsInitializing(false);
      }
    };

    initializeChat();
  }, [isLoggedIn, loadMessages, createNewChat]);

  // 스트리밍 메시지 전송
  const sendMessage = useCallback(async (userMessageText) => {
    if (!userMessageText.trim() || isLoading || !currentSessionId) return;

    const userMessage = { role: 'user', content: userMessageText };
    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    let activeSessionId = currentSessionId;
    
    // 임시 세션일 경우 실제 세션 생성
    if (typeof activeSessionId === 'string' && activeSessionId.startsWith('temp-')) {
      try {
        const response = await chatApi.createSession();
        const newSession = response.data.room || response.data.data;
        activeSessionId = newSession.id;
        setCurrentSessionId(activeSessionId);
        setSessions(prev => [newSession, ...prev]);
      } catch (error) {
        console.error("세션 생성 실패:", error);
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: '세션 생성에 실패했습니다. 페이지를 새로고침해주세요.',
          thinking: ''
        }]);
        setIsLoading(false);
        return;
      }
    }

    setMessages(prev => [...prev, { role: 'assistant', content: '', thinking: '' }]);

    let accumulatedContent = '';

    await chatApi.streamMessage(
      activeSessionId,
      userMessageText,
      (chunk) => {
        if (chunk.type === 'token') {
          accumulatedContent += chunk.content;
          setMessages(prev => {
            const newMessages = [...prev];
            const lastIdx = newMessages.length - 1;
            if (newMessages[lastIdx].role === 'assistant') {
              newMessages[lastIdx] = {
                ...newMessages[lastIdx],
                content: accumulatedContent
              };
            }
            return newMessages;
          });
        } else if (chunk.type === 'error') {
          console.error("Stream error:", chunk.content);
        }
      },
      () => { setIsLoading(false); },
      (error) => {
        console.error("Send error:", error);
        setMessages(prev => {
          const newMessages = [...prev];
          const lastIdx = newMessages.length - 1;
          newMessages[lastIdx] = {
            ...newMessages[lastIdx],
            content: newMessages[lastIdx].content + "\n[오류가 발생했습니다]"
          };
          return newMessages;
        });
        setIsLoading(false);
      }
    );
  }, [currentSessionId, isLoading]);

  return {
    sessions,
    currentSessionId,
    messages,
    isLoading,
    isInitializing,
    loadMessages,
    createNewChat,
    sendMessage
  };
};
