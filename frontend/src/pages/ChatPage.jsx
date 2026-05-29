import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate, useLocation } from 'react-router-dom';
import Layout from '../components/common/Layout';
import * as chatApi from '../api/chat';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import '../styles/pages/chat.css';

const ChatPage = () => {
  const { user, logout, isLoggedIn } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [sessions, setSessions] = useState([]);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  // eslint-disable-next-line no-unused-vars
  const [isInitializing, setIsInitializing] = useState(true);
  // Thinking 표시 상태 관리 (메시지 인덱스별로 확장 여부 저장)
  const [expandedThinking, setExpandedThinking] = useState({});

  const messagesEndRef = useRef(null);

  // 홈에서 전달된 초기 메시지 처리
  useEffect(() => {
    if (location.state?.initialMessage) {
      setInput(location.state.initialMessage);
    }
  }, [location.state]);

  // 1. 초기 세션 로드 및 생성
  useEffect(() => {
    const initializeChat = async () => {
      // 세션 선택 함수 (내부 정의)
      const loadSession = async (sessionId) => {
        setCurrentSessionId(sessionId);
        setIsLoading(true);
        try {
          const response = await chatApi.getMessages(sessionId);
          const formattedMessages = response.data.data.map(msg => ({
            role: msg.role,  // 백엔드가 이제 role을 직접 반환
            content: msg.content,
            thinking: msg.thinking || ''  // thinking 필드 추가
          }));
          setMessages(formattedMessages);
        } catch (error) {
          console.error("Failed to load messages:", error);
        } finally {
          setIsLoading(false);
        }
      };

      // 새 채팅 생성 함수 (내부 정의)
      const createNewChat = async () => {
        try {
          const response = await chatApi.createSession();
          const newSession = response.data.data;
          setSessions(prev => [newSession, ...prev]);
          setCurrentSessionId(newSession.id);
          setMessages([]);
        } catch (error) {
          console.error("Failed to create session:", error);
          // 세션 생성 실패 시에도 임시 ID로 채팅 가능하도록 설정
          const tempSessionId = 'temp-' + Date.now();
          setCurrentSessionId(tempSessionId);
        }
      };

      try {
        let sessionList = [];

        // 로그인 상태일 때만 이전 세션 목록을 가져옴
        if (isLoggedIn) {
          try {
            const response = await chatApi.getSessions();
            sessionList = response.data.data;
          } catch (error) {
            console.error("Failed to load sessions:", error);
          }
        }
        // 비로그인 상태면 sessionList는 빈 배열 유지 -> 위 로직에 의해 createNewChat() 호출됨

        setSessions(sessionList);

        if (isLoggedIn && sessionList.length > 0) {
          await loadSession(sessionList[0].id);
        } else {
          // 세션이 없거나 비로그인 상태면 무조건 새 채팅 시작 (이전 세션 복구 안 함)
          await createNewChat();
        }
      } catch (error) {
        console.error("Chat initialization failed:", error);
        // 초기화 실패 시에도 임시 세션 ID 설정
        const tempSessionId = 'temp-' + Date.now();
        setCurrentSessionId(tempSessionId);
      } finally {
        setIsInitializing(false);
      }
    };

    initializeChat();
  }, [isLoggedIn]);

  // 2. 스크롤 자동 이동
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // 세션 선택 함수
  const selectSession = async (sessionId) => {
    setCurrentSessionId(sessionId);
    setIsLoading(true);
    try {
      const response = await chatApi.getMessages(sessionId);
      const formattedMessages = response.data.data.map(msg => ({
        role: msg.role,  // 백엔드가 이제 role을 직접 반환
        content: msg.content,
        thinking: msg.thinking || ''  // thinking 필드 추가
      }));
      setMessages(formattedMessages);
      setExpandedThinking({});  // 세션 변경 시 thinking 상태 초기화
    } catch (error) {
      console.error("Failed to load messages:", error);
    } finally {
      setIsLoading(false);
    }
  };

  // 새 채팅 시작 함수
  const handleNewChat = async () => {
    try {
      const response = await chatApi.createSession();
      const newSession = response.data.data;
      setSessions(prev => [newSession, ...prev]);
      setCurrentSessionId(newSession.id);
      setMessages([]);
    } catch (error) {
      console.error("Failed to create session:", error);
      // 세션 생성 실패 시에도 임시 ID로 채팅 가능하도록 설정
      const tempSessionId = 'temp-' + Date.now();
      setCurrentSessionId(tempSessionId);
    }
  };

  // 메시지 전송 함수
  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim() || isLoading || !currentSessionId) return;

    const userMessageText = input;
    const userMessage = { role: 'user', content: userMessageText };

    // 1. 사용자 메시지 즉시 표시
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    // 임시 세션 ID인 경우, 먼저 실제 세션을 생성
    let activeSessionId = currentSessionId;
    if (typeof activeSessionId === 'string' && activeSessionId.startsWith('temp-')) {
      try {
        const response = await chatApi.createSession();
        const newSession = response.data.data;
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

    // 2. AI 메시지 플레이스홀더 추가
    setMessages(prev => [...prev, { role: 'assistant', content: '', thinking: '' }]);

    let accumulatedContent = '';

    // 3. 스트리밍 요청
    await chatApi.streamMessage(
      activeSessionId,
      userMessageText,
      (chunk) => {
        if (chunk.type === 'token') {
          accumulatedContent += chunk.content;

          // 마지막 메시지(AI) 업데이트
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
      () => {
        // onDone
        setIsLoading(false);
      },
      (error) => {
        // onError
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
  };

  // --- Left Sidebar (Chat Specific) ---
  const leftSidebar = (
    <>
      {/* User Profile */}
      <div className="user-profile-container">
        <div className="profile-section">
          <div className="profile-avatar">
            {isLoggedIn ? '👤' : 'G'}
          </div>
          <div className="profile-info">
            <div className="profile-name-section">
              <div className="profile-name">
                {isLoggedIn ? (user?.maple_nickname || user?.username || 'User') : 'Guest'}
              </div>
              <div className="profile-server">
                <span className="server-icon"></span>LUNA
              </div>
            </div>
            <div className="divider"></div>
            {isLoggedIn ? (
              <div className="profile-stats">
                <div className="stat-row">
                  <span className="stat-label">Lv.</span>
                  <span className="stat-value">285</span>
                </div>
                <div className="stat-row">
                  <span className="stat-label">직업</span>
                  <span className="stat-value">아델</span>
                </div>
                <div className="stat-row">
                  <span className="stat-label">길드</span>
                  <span className="stat-value">MAI</span>
                </div>
              </div>
            ) : (
              <div className="profile-stats">
                <div className="stat-row">
                  <span className="stat-label">상태</span>
                  <span className="stat-value">비로그인</span>
                </div>
              </div>
            )}
          </div>
          {isLoggedIn && (
            <div className="detail-link" onClick={() => alert('상세 정보 기능 구현 예정')}>
              상세
            </div>
          )}
        </div>
        <div className="profile-actions">
          {isLoggedIn ? (
            <button className="logout-btn" onClick={logout}>로그아웃</button>
          ) : (
            <button className="logout-btn" onClick={() => navigate('/login')}>로그인</button>
          )}
        </div>
      </div>

      {/* Chat History */}
      <div className="chat-history-container">
        <div className="chat-history-header">
          채팅 기록
        </div>
        <div className="chat-history-content">
          <button
            className="btn btn-outline"
            style={{ width: '100%', marginBottom: '10px' }}
            onClick={handleNewChat}
          >
            + 새 채팅
          </button>

          {!isLoggedIn ? (
            <div className="guest-history-placeholder" style={{ textAlign: 'center', marginTop: '20px', color: 'var(--text-secondary)' }}>
              <p style={{ fontSize: '0.9rem', marginBottom: '10px' }}>로그인하면 대화 기록을<br />저장하고 볼 수 있습니다.</p>
              <button
                className="btn btn-primary"
                style={{ fontSize: '0.85rem', padding: '5px 15px' }}
                onClick={() => navigate('/login')}
              >
                로그인하기
              </button>
            </div>
          ) : (
            sessions.map(session => (
              <div
                key={session.id}
                className="history-item"
                onClick={() => selectSession(session.id)}
                style={{
                  cursor: 'pointer',
                  opacity: session.id === currentSessionId ? 1 : 0.7
                }}
              >
                <div className="history-date">
                  {new Date(session.created_at).toLocaleDateString()}
                  {session.id === currentSessionId && ' (현재)'}
                </div>
                <div className="history-text">
                  {/* 제목(첫 대화 요약) 사용 */}
                  {session.title || `채팅 #${session.id.substring(0, 8)}`}
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </>
  );

  // --- Right Sidebar (Ad) ---
  const rightSidebar = (
    <div className="sidebar-ad-long">
      <div className="ad-header">ADVERTISEMENT</div>
      <div className="ad-content">
        <div className="ad-text">
          <div className="ad-title">메이플스토리</div>
          <div className="ad-subtitle">지금 시작하세요!</div>
        </div>
      </div>
    </div>
  );

  return (
    <Layout
      leftSidebar={leftSidebar}
      rightSidebar={rightSidebar}
      layoutClass="chatbot-layout"
    >
      <div className="chat-header">
        <div className="chat-title">MAI HELP YOU</div>
        <div className="chat-subtitle">메이플스토리 AI 챗봇</div>
      </div>

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
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {msg.content}
              </ReactMarkdown>
              {/* AI 메시지이고 thinking이 있을 경우 토글 표시 */}
              {msg.role === 'assistant' && msg.thinking && (
                <div className="thinking-container">
                  <button
                    className="thinking-toggle"
                    onClick={() => setExpandedThinking(prev => ({
                      ...prev,
                      [idx]: !prev[idx]
                    }))}
                  >
                    <span className={`thinking-toggle-icon ${expandedThinking[idx] ? 'expanded' : ''}`}>
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

        {isLoading && (
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

      <div className="chat-input-container">
        <form className="chat-input-wrapper" onSubmit={handleSend}>
          <textarea
            className="chat-input-main"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="메시지를 입력하세요..."
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSend(e);
              }
            }}
          />
          <button
            type="submit"
            className="chat-send-main"
            disabled={isLoading || !currentSessionId}
          >
            ➤
          </button>
        </form>
      </div>
    </Layout>
  );
};

export default ChatPage;
