import React from 'react';
import { ArrowUpRight, BookOpen, ChevronRight, History, Leaf, LogIn, LogOut, MessageSquare, Plus, Shield, UserRound, X } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

export const PROFILE_FALLBACK = '미설정';

export const resolveProfileField = (value) => {
  if (value === null || value === undefined || (typeof value === 'string' && !value.trim())) {
    return PROFILE_FALLBACK;
  }
  return value;
};

const formatSessionDate = (value) => {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? '대화 기록' : date.toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' });
};

const ChatSidebar = ({ sessions, currentSessionId, handleNewChat, selectSession, isBusy, isOpen, onClose }) => {
  const { user, logout, isLoggedIn, openLoginModal } = useAuth();
  const navigate = useNavigate();
  const username = user?.maple_nickname || user?.username || user?.user?.username || '모험가';
  const login = () => {
    onClose?.();
    if (openLoginModal) openLoginModal();
    else navigate('/login');
  };

  return (
    <div className="chat-sidebar" id="chatSidebar" role={isOpen ? 'dialog' : undefined} aria-modal={isOpen ? 'true' : undefined} aria-label="나의 모험 노트">
      <div className="chat-sidebar-heading">
        <span><Leaf size={18} /> 나의 모험 노트</span>
        <button type="button" className="chat-icon-button chat-mobile-close" aria-label="대화 목록 닫기" onClick={onClose}>
          <X size={18} />
        </button>
      </div>

      <button className="chat-new-button" type="button" onClick={handleNewChat} disabled={isBusy}>
        <Plus size={18} /> 새 대화 시작 <span className="chat-new-shortcut">NEW</span>
      </button>

      <section className="chat-history" aria-label="대화 기록">
        <h2 className="chat-sidebar-label"><History size={14} /> 최근 대화</h2>
        {!isLoggedIn ? (
          <div className="chat-history-empty">
            <div className="chat-history-empty-icon"><BookOpen size={22} /></div>
            <p>모험의 기록을 남겨보세요</p>
            <span>로그인하면 이전 대화를<br />언제든 다시 볼 수 있어요.</span>
            <button type="button" onClick={login}>로그인하기 <ArrowUpRight size={13} /></button>
          </div>
        ) : sessions.length === 0 ? (
          <div className="chat-history-empty">
            <MessageSquare size={24} />
            <p>아직 대화 기록이 없어요</p>
            <span>첫 번째 이야기를 시작해 보세요.</span>
          </div>
        ) : (
          <div className="chat-session-list">
            {sessions.map(session => (
              <button
                type="button"
                key={session.id}
                className={`chat-session${session.id === currentSessionId ? ' is-current' : ''}`}
                onClick={() => selectSession(session.id)}
                disabled={isBusy}
                aria-current={session.id === currentSessionId ? 'true' : undefined}
              >
                <MessageSquare size={15} />
                <span className="chat-session-info">
                  <span className="chat-session-title">{session.room_name || '새로운 모험 이야기'}</span>
                  <span className="chat-session-date">{formatSessionDate(session.created_at)}</span>
                </span>
                {session.id === currentSessionId && <span className="chat-session-dot" aria-label="현재 대화" />}
              </button>
            ))}
          </div>
        )}
      </section>

      <div className="chat-sidebar-tip">
        <Shield size={17} />
        <p><strong>함께라면 더 쉬운 모험</strong><span>육성, 보스, 장비 고민까지<br />가이드에게 편하게 물어보세요.</span></p>
      </div>

      <section className="chat-profile" aria-label="모험가 프로필">
        <div className="chat-profile-top">
          <div className="chat-profile-avatar"><UserRound size={20} /></div>
          <div className="chat-profile-name">
            <strong>{isLoggedIn ? username : '게스트 모험가'}</strong>
            <span>{isLoggedIn ? resolveProfileField(user?.server) : '반가워요, 모험가님!'}</span>
          </div>
          {isLoggedIn && (
            <button type="button" className="chat-profile-details" aria-label="캐릭터 상세 보기" onClick={() => { onClose?.(); navigate('/character'); }}>
              <ChevronRight size={17} />
            </button>
          )}
        </div>
        {isLoggedIn && (
          <dl className="chat-profile-stats">
            <div><dt>레벨</dt><dd>{resolveProfileField(user?.level)}</dd></div>
            <div><dt>직업</dt><dd>{resolveProfileField(user?.job)}</dd></div>
            <div><dt>길드</dt><dd>{resolveProfileField(user?.guild)}</dd></div>
          </dl>
        )}
        <button type="button" className="chat-profile-action" onClick={isLoggedIn ? () => { onClose?.(); logout(); } : login}>
          {isLoggedIn ? <LogOut size={14} /> : <LogIn size={14} />}
          {isLoggedIn ? '로그아웃' : '로그인하고 기록 저장하기'}
        </button>
      </section>
    </div>
  );
};

export default ChatSidebar;
