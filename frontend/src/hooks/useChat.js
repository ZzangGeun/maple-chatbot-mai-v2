import { useCallback, useEffect, useRef, useState } from 'react';
import * as chatApi from '../api/chat';
import { mapMessagesResponse, mapRoom, mapRoomsResponse } from '../api/chatSchema';

export const useChat = (isLoggedIn, isAuthReady = true) => {
  const [sessions, setSessions] = useState([]);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isInitializing, setIsInitializing] = useState(true);
  const [error, setError] = useState(null);
  const [initializationAttempt, setInitializationAttempt] = useState(0);
  const operationRef = useRef(0);
  const busyRef = useRef(false);
  const messageIdRef = useRef(0);

  const clearError = useCallback(() => setError(null), []);
  const retryInitialization = useCallback(() => setInitializationAttempt(value => value + 1), []);

  // 이전 계정·대화방의 응답이나 페이지를 떠난 뒤의 응답은 현재 대화를 덮어쓰지 않습니다.
  // 대화 작업이 진행 중일 때는 전송과 방 변경을 함께 차단합니다.
  const loadMessages = useCallback(async (sessionId) => {
    if (busyRef.current || !sessionId) return;
    busyRef.current = true;
    const operation = ++operationRef.current;
    setCurrentSessionId(sessionId);
    setMessages([]);
    setError(null);
    setIsLoading(true);
    try {
      const response = await chatApi.getMessages(sessionId);
      const loadedMessages = mapMessagesResponse(response.data);
      if (operation === operationRef.current) setMessages(loadedMessages);
    } catch (loadError) {
      if (operation !== operationRef.current) return;
      console.error('Failed to load messages:', loadError);
      setError({ kind: 'history', message: '이전 대화를 불러오지 못했어요. 잠시 후 다시 시도해 주세요.' });
    } finally {
      if (operation === operationRef.current) {
        busyRef.current = false;
        setIsLoading(false);
      }
    }
  }, []);

  const createNewChat = useCallback(async () => {
    if (busyRef.current) return null;
    busyRef.current = true;
    const operation = ++operationRef.current;
    setIsLoading(true);
    setError(null);
    try {
      const response = await chatApi.createSession();
      const newSession = mapRoom(response.data.room);
      if (operation !== operationRef.current) return null;
      setSessions(previous => [newSession, ...previous]);
      setCurrentSessionId(newSession.id);
      setMessages([]);
      return newSession.id;
    } catch (createError) {
      if (operation !== operationRef.current) return null;
      console.error('Failed to create session:', createError);
      const temporaryId = 'temp-' + Date.now();
      setCurrentSessionId(temporaryId);
      setMessages([]);
      setError({ kind: 'create', message: '대화에 연결하지 못했어요. 연결을 확인하고 다시 시도해 주세요.' });
      return temporaryId;
    } finally {
      if (operation === operationRef.current) {
        busyRef.current = false;
        setIsLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    const operation = ++operationRef.current;
    busyRef.current = true;
    setIsInitializing(true);
    setIsLoading(false);
    setError(null);
    setMessages([]);
    setSessions([]);
    setCurrentSessionId(null);

    const invalidateOperation = () => {
      operationRef.current += 1;
      busyRef.current = false;
    };

    // 최초 로그인 상태 확인이 끝나기 전에는 빈 대화방을 생성하지 않습니다.
    if (!isAuthReady) return invalidateOperation;

    const initializeChat = async () => {
      try {
        const roomResponse = isLoggedIn ? await chatApi.getSessions() : null;
        if (operation !== operationRef.current) return;
        const roomList = roomResponse ? mapRoomsResponse(roomResponse.data) : [];
        setSessions(roomList);
        if (roomList.length > 0) {
          const sessionId = roomList[0].id;
          setCurrentSessionId(sessionId);
          const response = await chatApi.getMessages(sessionId);
          const loadedMessages = mapMessagesResponse(response.data);
          if (operation === operationRef.current) setMessages(loadedMessages);
        } else {
          const response = await chatApi.createSession();
          const newSession = mapRoom(response.data.room);
          if (operation !== operationRef.current) return;
          setSessions([newSession]);
          setCurrentSessionId(newSession.id);
        }
      } catch (initializationError) {
        if (operation !== operationRef.current) return;
        console.error('Chat initialization failed:', initializationError);
        setCurrentSessionId('temp-' + Date.now());
        setError({ kind: 'initialize', message: '가이드에 연결하지 못했어요. 잠시 후 다시 시도해 주세요.' });
      } finally {
        if (operation === operationRef.current) {
          busyRef.current = false;
          setIsInitializing(false);
        }
      }
    };

    initializeChat();
    return invalidateOperation;
  }, [isLoggedIn, isAuthReady, initializationAttempt]);

  const sendMessage = useCallback(async (question, isRetry = false) => {
    const userMessageText = question.trim();
    if (!userMessageText || busyRef.current || !currentSessionId) return;
    busyRef.current = true;
    const operation = ++operationRef.current;
    const messageId = `client-${Date.now()}-${messageIdRef.current++}`;
    const assistantId = `${messageId}-answer`;
    const userMessage = { id: messageId, role: 'user', content: userMessageText };
    const assistantMessage = { id: assistantId, role: 'assistant', content: '', thinking: '' };
    setError(null);
    setIsLoading(true);
    setMessages(previous => {
      if (isRetry) {
        let lastQuestionIndex = previous.length - 1;
        while (lastQuestionIndex >= 0 && previous[lastQuestionIndex].role !== 'user') lastQuestionIndex -= 1;
        return [...previous.slice(0, Math.max(0, lastQuestionIndex)), userMessage, assistantMessage];
      }
      return [...previous, userMessage, assistantMessage];
    });

    let activeSessionId = currentSessionId;
    let accumulatedContent = '';
    let failed = false;

    const markFailed = (sendError) => {
      if (operation !== operationRef.current || failed) return;
      failed = true;
      console.error('Send error:', sendError);
      setError({
        kind: 'send',
        message: sendError?.status === 401 || sendError?.status === 403
          ? '로그인 상태를 확인한 뒤 다시 질문해 주세요.'
          : '답변을 가져오지 못했어요. 연결을 확인하고 다시 시도해 주세요.',
      });
      setMessages(previous => previous.map(message => message.id === assistantId ? { ...message, isError: true } : message));
    };

    try {
      if (typeof activeSessionId === 'string' && activeSessionId.startsWith('temp-')) {
        const response = await chatApi.createSession();
        const newSession = mapRoom(response.data.room);
        if (operation !== operationRef.current) return;
        activeSessionId = newSession.id;
        setCurrentSessionId(activeSessionId);
        setSessions(previous => [newSession, ...previous]);
      }

      await chatApi.streamMessage(
        activeSessionId,
        userMessageText,
        chunk => {
          if (operation !== operationRef.current || failed) return;
          if (chunk.type === 'token') {
            accumulatedContent += chunk.content;
            setMessages(previous => previous.map(message => message.id === assistantId ? { ...message, content: accumulatedContent } : message));
          } else if (chunk.type === 'error') {
            markFailed(chunk);
          }
        },
        () => {},
        markFailed,
      );
      if (!accumulatedContent && !failed) markFailed(new Error('The stream finished without an answer.'));
    } catch (sendError) {
      markFailed(sendError);
    } finally {
      if (operation === operationRef.current) {
        busyRef.current = false;
        setIsLoading(false);
      }
    }
  }, [currentSessionId]);

  return {
    sessions, currentSessionId, messages, isLoading, isInitializing, error,
    clearError, retryInitialization, loadMessages, createNewChat, sendMessage,
  };
};
