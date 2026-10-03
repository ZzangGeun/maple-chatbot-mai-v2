import React, { useState, useEffect } from 'react';
import { ArrowRight, Leaf, Loader2, X } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useModalA11y } from '../../hooks/useModalA11y';
import '../../styles/components/auth.css';

const LoginPopup = () => {
  const { isLoginModalOpen, closeLoginModal, login, error, isLoading, openSignupModal } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const modalRef = useModalA11y(isLoginModalOpen, closeLoginModal);

  useEffect(() => {
    if (isLoginModalOpen) {
      setUsername('');
      setPassword('');
    }
  }, [isLoginModalOpen]);

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (isLoading) return;
    await login(username, password);
  };

  const switchToSignup = () => {
    closeLoginModal();
    openSignupModal();
  };

  if (!isLoginModalOpen) return null;

  return (
    <div className="login-popup-overlay" onClick={closeLoginModal}>
      <div className="login-popup-modal" ref={modalRef} role="dialog" aria-modal="true" aria-labelledby="login-modal-title" aria-describedby="login-modal-description" onClick={(event) => event.stopPropagation()}>
        <div className="login-popup-header">
          <div><span className="auth-eyebrow"><Leaf size={14} aria-hidden="true" /> MAI HELP YOU</span><h2 id="login-modal-title">모험을 이어가볼까요?</h2></div>
          <button type="button" className="login-popup-close" onClick={closeLoginModal} aria-label="로그인 닫기"><X size={19} aria-hidden="true" /></button>
        </div>
        <div className="login-popup-content">
          <p className="auth-modal-description" id="login-modal-description">로그인하고 메이와 나눈 이야기를 기록해보세요.</p>
          {error && <div className="auth-error" role="alert">{error}</div>}
          <form className="login-popup-form" onSubmit={handleSubmit} aria-busy={isLoading}>
            <div className="login-input-group">
              <label htmlFor="loginId">아이디</label>
              <input type="text" id="loginId" name="username" className="login-popup-input" placeholder="아이디를 입력하세요" autoComplete="username" value={username} onChange={(event) => setUsername(event.target.value)} required />
            </div>
            <div className="login-input-group">
              <label htmlFor="loginPassword">비밀번호</label>
              <input type="password" id="loginPassword" name="password" className="login-popup-input" placeholder="비밀번호를 입력하세요" autoComplete="current-password" value={password} onChange={(event) => setPassword(event.target.value)} required />
            </div>
            <button type="submit" className="login-popup-btn" disabled={isLoading}>
              {isLoading ? <Loader2 className="auth-loading-icon" size={18} aria-hidden="true" /> : <ArrowRight size={18} aria-hidden="true" />}{isLoading ? '로그인 중…' : '로그인'}
            </button>
          </form>
          <div className="auth-signup-prompt"><span>처음 오셨나요?</span><button type="button" className="login-link" onClick={switchToSignup}>회원가입 <ArrowRight size={13} aria-hidden="true" /></button></div>
        </div>
      </div>
    </div>
  );
};

export default LoginPopup;
