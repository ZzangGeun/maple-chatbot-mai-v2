import React, { useEffect } from 'react';

/**
 * Google AdSense 광고를 표시하는 컴포넌트입니다.
 * 
 * @param {Object} props
 * @param {string} props.slot - Google AdSense 광고 단위 ID (필수)
 * @param {Object} [props.style] - 광고 영역 스타일 (선택)
 * @param {string} [props.format='auto'] - 광고 형식 (기본값: 'auto')
 * @param {string} [props.responsive='true'] - 반응형 여부 (기본값: 'true')
 */
const AdSense = ({ slot, style, format = 'auto', responsive = 'true' }) => {
  // 개발 환경에서는 AdSense를 표시하지 않음
  if (!import.meta.env.VITE_ADSENSE_CLIENT_ID) {
    return null;
  }

  useEffect(() => {
    try {
      // 광고 스크립트 실행: 광고를 로드하여 표시합니다.
      // window.adsbygoogle 배열에 빈 객체를 푸시하면 스크립트가 <ins> 태그를 찾아 광고를 채웁니다.
      (window.adsbygoogle = window.adsbygoogle || []).push({});
    } catch (e) {
      console.error('AdSense 로드 중 오류 발생:', e);
    }
  }, []); // 컴포넌트가 마운트될 때 한 번만 실행

  if (!slot) {
    return <div style={{ color: 'red' }}>AdSense Slot ID가 필요합니다.</div>;
  }

  return (
    <ins
      className="adsbygoogle"
      style={{ display: 'block', ...style }}
      data-ad-client={import.meta.env.VITE_ADSENSE_CLIENT_ID}
      data-ad-slot={slot}
      data-ad-format={format}
      data-full-width-responsive={responsive}
    />
  );
};

export default AdSense;
