import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import '../../styles/common.css';

const Navigation = () => {
  const { user, isLoggedIn, logout, openLoginModal } = useAuth();
  const location = useLocation();

  const isActive = (path) => location.pathname === path ? 'active' : '';

  return (
    <nav className="navigation">
      <div className="nav-content">
        <div className="nav-left">
          <Link to="/" className={`nav-item ${isActive('/')}`}>메인</Link>
          <Link to="/chat" className={`nav-item ${isActive('/chat')}`}>챗봇</Link>
          <Link to="/character" className={`nav-item ${isActive('/character')}`}>캐릭터 검색</Link>
          <Link to="/community" className={`nav-item ${isActive('/community')}`}>커뮤니티</Link>
        </div>
        
        <div className="nav-right">
          {!isLoggedIn ? (
            <div className="nav-login-section">
              <button className="nav-login-btn" onClick={openLoginModal}>로그인</button>
            </div>
          ) : (
            <div className="nav-user-profile">
              <span className="nav-user-name">{user?.nickname || user?.username || '사용자'}</span>
              <button className="nav-logout-btn" onClick={logout}>로그아웃</button>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
};

export default Navigation;