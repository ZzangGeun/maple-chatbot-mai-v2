import React from 'react';
import { NavLink } from 'react-router-dom';
import { Home, Sparkles, Search, MessagesSquare, LogIn, LogOut, UserRound } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

const links = [
  { to: '/', label: '홈', Icon: Home },
  { to: '/chat', label: '메이와 대화', Icon: Sparkles },
  { to: '/character', label: '캐릭터 도감', Icon: Search },
  { to: '/community', label: '커뮤니티', Icon: MessagesSquare },
];
const Navigation = () => {
  const { user, isLoggedIn, logout, openLoginModal } = useAuth();
  return (
    <nav className="navigation" aria-label="주 메뉴">
      <div className="nav-left">
        {links.map(({ to, label, Icon }) => (
          <NavLink key={to} to={to} end={to === '/'} className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}>
            <Icon size={17} aria-hidden="true" /><span>{label}</span>
          </NavLink>
        ))}
      </div>
      <div className="nav-right">
        {isLoggedIn ? (
          <div className="nav-user-profile">
            <span className="nav-user-name"><UserRound size={16} aria-hidden="true" />{user?.maple_nickname || user?.nickname || user?.username || '모험가'}</span>
            <button type="button" className="nav-logout-btn" onClick={logout} aria-label="로그아웃"><LogOut size={17} aria-hidden="true" /></button>
          </div>
        ) : (
          <button type="button" className="nav-login-btn" onClick={openLoginModal}><LogIn size={16} aria-hidden="true" />로그인</button>
        )}
      </div>
    </nav>
  );
};
export default Navigation;
