import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useModalA11y } from '../../hooks/useModalA11y';
import '../../styles/components/auth.css';

const LoginPopup = () => {
  const { isLoginModalOpen, closeLoginModal, login, error, isLoading, openSignupModal } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  // 모달 접근성: 포커스 트랩 + Escape 닫기 + 포커스 복귀 (요구사항 9.3, 9.4)
  const modalRef = useModalA11y(isLoginModalOpen, closeLoginModal);

  // 모달이 열릴 때 입력창 초기화
  useEffect(() => {
    if (isLoginModalOpen) {
      setUsername('');
      setPassword('');
    }
  }, [isLoginModalOpen]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    await login(username, password);
  };

  if (!isLoginModalOpen) return null;

  return (
    <div className="login-popup-overlay" onClick={closeLoginModal}>
      <div className="login-popup-modal" ref={modalRef} role="dialog" aria-modal="true" aria-label="로그인" onClick={(e) => e.stopPropagation()}>
        <div className="login-popup-header">
          <h3>로그인</h3>
          <button className="login-popup-close" onClick={closeLoginModal}>&times;</button>
        </div>

        <div className="login-popup-content">
          {error && <div style={{ color: '#dc3545', marginBottom: '15px', fontSize: '14px', textAlign: 'center' }}>{error}</div>}

          <form className="login-popup-form" onSubmit={handleSubmit}>
            <div className="login-input-group">
              <label htmlFor="loginId">아이디</label>
              <input
                type="text"
                id="loginId"
                className="login-popup-input"
                placeholder="아이디를 입력하세요"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
              />
            </div>

            <div className="login-input-group">
              <label htmlFor="loginPassword">비밀번호</label>
              <input
                type="password"
                id="loginPassword"
                className="login-popup-input"
                placeholder="비밀번호를 입력하세요"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>

            <div className="login-popup-options">
              <label className="login-checkbox">
                <input type="checkbox" />
                <span>로그인 상태 유지</span>
              </label>
            </div>

            <button type="submit" className="login-popup-btn" disabled={isLoading}>
              {isLoading ? '로그인 중...' : '로그인'}
            </button>
          </form>

          <div className="login-popup-links">
            <a href="#" className="login-link">아이디 찾기</a>
            <span>|</span>
            <a href="#" className="login-link">비밀번호 찾기</a>
            <span>|</span>
            <a href="#" className="login-link" onClick={(e) => { e.preventDefault(); closeLoginModal(); openSignupModal(); }}>회원가입</a>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPopup;
