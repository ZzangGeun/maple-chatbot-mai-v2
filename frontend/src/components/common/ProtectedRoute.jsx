import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import LoadingFallback from './LoadingFallback';

/**
 * 인증이 필요한 라우트를 보호하는 래퍼 컴포넌트입니다.
 *
 * - `AuthContext`의 `isLoading`이 참인 동안(인증 확인 전)에는 `LoadingFallback`을
 *   표시하여, 인증 상태가 확정되기 전에 잘못된 리다이렉트가 발생하지 않도록 한다.
 * - 로딩이 끝난 후 비로그인 상태이면 `/login`으로 이동(`replace`)한다.
 * - 로그인 상태이면 보호된 자식(children)을 렌더한다.
 *
 * (요구사항 10.4)
 *
 * @param {Object} props
 * @param {React.ReactNode} props.children - 인증된 사용자에게만 렌더할 자식 요소
 */
const ProtectedRoute = ({ children }) => {
  const { isLoggedIn, isLoading } = useAuth();

  if (isLoading) {
    return <LoadingFallback fullscreen />;
  }

  if (!isLoggedIn) {
    return <Navigate to="/login" replace />;
  }

  return children;
};

export default ProtectedRoute;
