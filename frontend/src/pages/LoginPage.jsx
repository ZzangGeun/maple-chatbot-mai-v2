import React, { useState } from 'react';
import { ArrowRight, BookOpen, Leaf, Loader2, MessageCircle, Sparkles } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import Layout from '../components/common/Layout';
import '../styles/components/auth.css';

const LoginPage = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const { login, isLoading, error, openSignupModal } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (isLoading) return;
    const result = await login(username, password);
    if (result.success) navigate('/');
  };

  return (
    <Layout layoutClass="narrow-layout">
      <section className="auth-page" aria-labelledby="auth-page-title">
        <div className="auth-page-story">
          <span className="auth-eyebrow"><Leaf size={15} aria-hidden="true" /> MY MAPLE JOURNEY</span>
          <h1 id="auth-page-title">함께하는 모험,<br />이어서 시작해요.</h1>
          <p>메이에게 궁금한 이야기를 물어보고,<br />나만의 모험 기록을 차곡차곡 쌓아보세요.</p>
          <div className="auth-page-illustration" aria-hidden="true">
            <span className="auth-illustration-spark">✦</span>
            <div className="auth-journal"><BookOpen size={62} strokeWidth={1.4} /><span>MY ADVENTURE</span></div>
            <span className="auth-illustration-bubble"><MessageCircle size={27} /></span>
            <span className="auth-illustration-leaf"><Leaf size={23} /></span>
          </div>
          <span className="auth-page-note"><Sparkles size={15} aria-hidden="true" /> 오늘의 모험도 메이가 함께할게요.</span>
        </div>

        <div className="auth-page-card">
          <div className="auth-card-heading"><span className="auth-brand-mark" aria-hidden="true"><Leaf size={23} /></span><h2>반가워요, 모험가님!</h2><p>로그인하고 지난 이야기를 이어가세요.</p></div>
          {error && <div className="auth-error" role="alert">{error}</div>}
          <form className="login-popup-form" onSubmit={handleSubmit} aria-busy={isLoading}>
            <div className="login-input-group">
              <label htmlFor="page-login-username">아이디</label>
              <input id="page-login-username" name="username" type="text" className="login-popup-input" placeholder="아이디를 입력하세요" autoComplete="username" value={username} onChange={(event) => setUsername(event.target.value)} required />
            </div>
            <div className="login-input-group">
              <label htmlFor="page-login-password">비밀번호</label>
              <input id="page-login-password" name="password" type="password" className="login-popup-input" placeholder="비밀번호를 입력하세요" autoComplete="current-password" value={password} onChange={(event) => setPassword(event.target.value)} required />
            </div>
            <button type="submit" className="login-popup-btn" disabled={isLoading}>
              {isLoading ? <Loader2 className="auth-loading-icon" size={18} aria-hidden="true" /> : <ArrowRight size={18} aria-hidden="true" />}{isLoading ? '로그인 중…' : '모험 이어가기'}
            </button>
          </form>
          <div className="auth-signup-prompt"><span>아직 계정이 없으신가요?</span><button type="button" className="login-link" onClick={openSignupModal}>회원가입 <ArrowRight size={13} aria-hidden="true" /></button></div>
        </div>
      </section>
    </Layout>
  );
};

export default LoginPage;
