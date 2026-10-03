import React from 'react';
import { Link } from 'react-router-dom';
import { Leaf } from 'lucide-react';
import Header from './Header';
import LoginPopup from '../auth/LoginPopup';
import SignupPopup from '../auth/SignupPopup';
import AdSense from './AdSense';
import '../../styles/globals/common.css';

const Layout = ({ children, leftSidebar, rightSidebar, layoutClass }) => (
  <div className="app-shell">
    <a className="skip-link" href="#main-content">본문으로 바로가기</a>
    <Header />
    <AdSense slotName="leaderboard" className="global-ad global-ad--leaderboard" style={{ minHeight: '90px' }} />
    <main id="main-content" tabIndex={-1} className="site-main">
      {leftSidebar || rightSidebar ? (
        <div className={`main-container ${layoutClass || 'default-layout'}`}>
          {leftSidebar && <aside className="sidebar-left">{leftSidebar}</aside>}
          <div className="main-content">{children}</div>
          {rightSidebar && <aside className="sidebar-right">{rightSidebar}</aside>}
        </div>
      ) : layoutClass ? <div className={`page-container ${layoutClass}`}>{children}</div> : children}
    </main>
    <footer className="site-footer">
      <div className="footer-brand"><Leaf size={17} aria-hidden="true" /><strong>MAI HELP YOU</strong><span>모험의 모든 순간을 함께.</span></div>
      <div className="footer-links"><Link to="/chat">메이와 대화</Link><Link to="/community">모험가들의 이야기</Link><span>MapleStory · Fan Project</span></div>
    </footer>
    <LoginPopup />
    <SignupPopup />
  </div>
);
export default Layout;
