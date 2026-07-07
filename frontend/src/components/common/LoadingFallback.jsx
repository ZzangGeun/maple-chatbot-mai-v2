import React from 'react';
import '../../styles/components/common.css';

/**
 * 공통 로딩 표시 컴포넌트입니다.
 *
 * Suspense의 fallback 또는 페이지/데이터 로딩 중 표시에 사용합니다.
 * 스크린 리더 사용자를 위해 `role="status"`와 `aria-live`로 로딩 상태를 알립니다.
 *
 * @param {Object} props
 * @param {string} [props.message='로딩 중...'] - 로딩 표시 문구
 * @param {boolean} [props.fullscreen=false] - 전체 화면 높이로 표시할지 여부
 */
const LoadingFallback = ({ message = '로딩 중...', fullscreen = false }) => {
  const className = fullscreen
    ? 'loading-fallback loading-fallback--fullscreen'
    : 'loading-fallback';

  return (
    <div className={className} role="status" aria-live="polite">
      <span className="loading-fallback__spinner" aria-hidden="true" />
      <span className="loading-fallback__message">{message}</span>
    </div>
  );
};

export default LoadingFallback;
