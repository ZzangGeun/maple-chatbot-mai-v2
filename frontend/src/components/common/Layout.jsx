import React from 'react';
import Header from './Header';
import Navigation from './Navigation';
import LoginPopup from '../auth/LoginPopup';
import SignupPopup from '../auth/SignupPopup';
import '../../styles/globals/common.css';

const Layout = ({ children, leftSidebar, rightSidebar, layoutClass }) => {
  // 사이드바가 있는 경우 커스텀 레이아웃 사용
  if (leftSidebar || rightSidebar) {
    return (
      <>
        <Header />
        <Navigation />
        <div className={layoutClass || 'default-layout'}>
          {leftSidebar && <aside className="layout-sidebar-left">{leftSidebar}</aside>}
          <main className="layout-main-content">{children}</main>
          {rightSidebar && <aside className="layout-sidebar-right">{rightSidebar}</aside>}
        </div>
        <LoginPopup />
        <SignupPopup />
      </>
    );
  }

  // 기본 레이아웃 (사이드바 없음)
  return (
    <>
      <Header />
      <Navigation />
      {children}
      <LoginPopup />
      <SignupPopup />
    </>
  );
};

export default Layout;