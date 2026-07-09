import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import Layout from '../components/common/Layout';
import '../styles/globals/common.css';

const LoginPage = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const { login, isLoading, error, openSignupModal } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    const result = await login(username, password);
    if (result.success) {
      navigate('/'); // 로그인 후 홈으로 이동
    }
  };

  const loginContent = (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '50vh' }}>
      <div className="login-status-card" style={{ width: '100%', maxWidth: '400px', padding: '30px' }}>
        <div className="login-header">
          <h3>로그인</h3>
          <p>서비스를 이용하려면 로그인해주세요.</p>
        </div>
        
        {error && <div style={{ color: 'var(--error-color)', marginBottom: '15px', fontSize: '14px' }}>{error}</div>}
        
        <form className="login-form" onSubmit={handleSubmit}>
          <input
            type="text"
            className="login-input"
            placeholder="아이디"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
            style={{ width: '100%' }}
          />
          <input
            type="password"
            className="login-input"
            placeholder="비밀번호"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            style={{ width: '100%' }}
          />
          <button 
            type="submit" 
            className="login-btn" 
            style={{ width: '100%', marginTop: '10px' }}
            disabled={isLoading}
          >
            {isLoading ? '로그인 중...' : '로그인'}
          </button>
        </form>
        
        <div style={{ marginTop: '20px', fontSize: '13px', color: 'var(--text-light-gray)' }}>
          계정이 없으신가요? <span style={{ color: 'var(--link-pink)', cursor: 'pointer' }} onClick={openSignupModal}>회원가입</span>
        </div>
      </div>
    </div>
  );

  return (
    <Layout>
      {loginContent}
    </Layout>
  );
};

export default LoginPage;
