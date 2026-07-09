import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

// 값이 없는 프로필 항목에 대해 표시할 대체 문자열
export const PROFILE_FALLBACK = '미설정';

/**
 * 프로필 필드 값을 표시용으로 정규화하는 순수 헬퍼.
 * 값이 없으면(null/undefined/빈 문자열) 대체 표시(PROFILE_FALLBACK)를 반환하고,
 * 값이 있으면 그대로 반환한다.
 * @param {*} value - AuthContext.user에서 읽은 원본 프로필 값
 * @returns {string} 표시할 값 또는 대체 표시
 */
export const resolveProfileField = (value) => {
  if (value === null || value === undefined) {
    return PROFILE_FALLBACK;
  }
  if (typeof value === 'string' && value.trim() === '') {
    return PROFILE_FALLBACK;
  }
  return value;
};

const ChatSidebar = ({
  sessions,
  currentSessionId,
  handleNewChat,
  selectSession
}) => {
  const { user, logout, isLoggedIn } = useAuth();
  const navigate = useNavigate();

  return (
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
                <span className="server-icon"></span>
                {isLoggedIn ? resolveProfileField(user?.server) : PROFILE_FALLBACK}
              </div>
            </div>
            <div className="divider"></div>
            {isLoggedIn ? (
              <div className="profile-stats">
                <div className="stat-row">
                  <span className="stat-label">Lv.</span>
                  <span className="stat-value">{resolveProfileField(user?.level)}</span>
                </div>
                <div className="stat-row">
                  <span className="stat-label">직업</span>
                  <span className="stat-value">{resolveProfileField(user?.job)}</span>
                </div>
                <div className="stat-row">
                  <span className="stat-label">길드</span>
                  <span className="stat-value">{resolveProfileField(user?.guild)}</span>
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
            <div className="detail-link" onClick={() => navigate('/character')}>
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
                  {new Date(session.created_at || session.updated_at).toLocaleDateString()}
                  {session.id === currentSessionId && ' (현재)'}
                </div>
                <div className="history-text">
                  {session.room_name || session.title || `채팅 #${session.id.substring(0, 8)}`}
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </>
  );
};

export default ChatSidebar;
