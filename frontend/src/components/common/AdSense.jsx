import React, { useEffect, useRef } from 'react';
import { isValidAdSenseClientId, isValidAdSenseSlotId } from '../../utils/adsense';

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
const getAdSenseConfig = () => {
  const runtimeConfig = typeof window !== 'undefined' ? window.__ADS_CONFIG__ : null;
  if (runtimeConfig) {
    return runtimeConfig;
  }

  return {
    enabled: import.meta.env.VITE_ADSENSE_ENABLED !== 'false',
    clientId: import.meta.env.VITE_ADSENSE_CLIENT_ID || '',
    slots: {
      leaderboard: import.meta.env.VITE_ADSENSE_SLOT_LEADERBOARD || '',
      medium_rectangle: import.meta.env.VITE_ADSENSE_SLOT_MEDIUM_RECT || '',
      skyscraper: import.meta.env.VITE_ADSENSE_SLOT_SKYSCRAPER || '',
    },
  };
};

const AdSense = ({
  slot,
  slotName,
  className,
  style,
  format = 'auto',
  responsive = 'true',
}) => {
  const config = getAdSenseConfig();
  const clientId = config.clientId;
  const resolvedSlot = slot || config.slots?.[slotName] || '';
  const isValid = config.enabled === true
    && isValidAdSenseClientId(clientId)
    && isValidAdSenseSlotId(resolvedSlot);
  const hasRequestedAd = useRef(false);

  useEffect(() => {
    if (!isValid || hasRequestedAd.current) {
      return;
    }

    try {
      ensureAdSenseScript(clientId);
      (window.adsbygoogle = window.adsbygoogle || []).push({});
      hasRequestedAd.current = true;
    } catch (e) {
      console.error('AdSense 로드 중 오류 발생:', e);
    }
  }, [isValid, clientId]);

  if (!isValid) {
    return null;
  }

  const adUnit = (
    <ins
      className="adsbygoogle"
      style={{ display: 'block', ...style }}
      data-ad-client={clientId}
      data-ad-slot={resolvedSlot}
      data-ad-format={format}
      data-full-width-responsive={responsive}
    />
  );

  if (!className) {
    return adUnit;
  }

  return (
    <aside className={className} aria-label="광고">
      <span className="ad-disclosure">광고</span>
      {adUnit}
    </aside>
  );
};

export default AdSense;
