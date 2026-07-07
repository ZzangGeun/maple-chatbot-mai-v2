import React, { useEffect } from 'react';
import { isValidAdSenseClientId } from '../../utils/adsense';

const ADSENSE_SCRIPT_ID = 'google-adsense-script';

/**
 * 유효한 client id가 구성된 경우에만 AdSense 스크립트를 동적으로 주입합니다.
 * 이미 주입되어 있으면 중복 삽입하지 않습니다.
 *
 * @param {string} clientId - 유효성 검사를 통과한 AdSense client id
 */
const ensureAdSenseScript = (clientId) => {
  if (typeof document === 'undefined') {
    return;
  }

  if (document.getElementById(ADSENSE_SCRIPT_ID)) {
    return;
  }

  const script = document.createElement('script');
  script.id = ADSENSE_SCRIPT_ID;
  script.async = true;
  script.crossOrigin = 'anonymous';
  script.src = `https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=${encodeURIComponent(
    clientId
  )}`;
  document.head.appendChild(script);
};

/**
 * Google AdSense 광고를 표시하는 컴포넌트입니다.
 *
 * `import.meta.env.VITE_ADSENSE_CLIENT_ID`가 유효한 client id일 때만
 * 스크립트/광고를 로드합니다. 값이 없거나 플레이스홀더면 아무것도 렌더하지 않습니다.
 *
 * @param {Object} props
 * @param {string} props.slot - Google AdSense 광고 단위 ID (필수)
 * @param {Object} [props.style] - 광고 영역 스타일 (선택)
 * @param {string} [props.format='auto'] - 광고 형식 (기본값: 'auto')
 * @param {string} [props.responsive='true'] - 반응형 여부 (기본값: 'true')
 */
const AdSense = ({ slot, style, format = 'auto', responsive = 'true' }) => {
  const clientId = import.meta.env.VITE_ADSENSE_CLIENT_ID;
  const isValid = isValidAdSenseClientId(clientId);

  useEffect(() => {
    if (!isValid) {
      return;
    }

    try {
      // 유효한 client id일 때만 스크립트를 주입하고 광고를 로드합니다.
      ensureAdSenseScript(clientId);
      // window.adsbygoogle 배열에 빈 객체를 푸시하면 스크립트가 <ins> 태그를 찾아 광고를 채웁니다.
      (window.adsbygoogle = window.adsbygoogle || []).push({});
    } catch (e) {
      console.error('AdSense 로드 중 오류 발생:', e);
    }
  }, [isValid, clientId]);

  // 유효한 client id가 없으면 스크립트/광고를 로드하지 않는다(요구사항 11.2).
  if (!isValid) {
    return null;
  }

  if (!slot) {
    return <div style={{ color: 'red' }}>AdSense Slot ID가 필요합니다.</div>;
  }

  return (
    <ins
      className="adsbygoogle"
      style={{ display: 'block', ...style }}
      data-ad-client={clientId}
      data-ad-slot={slot}
      data-ad-format={format}
      data-full-width-responsive={responsive}
    />
  );
};

export default AdSense;
