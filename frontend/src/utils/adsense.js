/**
 * AdSense client id 유효성 검사 유틸리티.
 *
 * 유효 조건 (요구사항 11.1, 11.2):
 * - 비어있지 않은 문자열이어야 한다.
 * - `ca-pub-` 접두사로 시작해야 한다.
 * - 접두사 뒤에는 실제 숫자열만 와야 한다(1자리 이상).
 * - 플레이스홀더(`ca-pub-XXXXXXXXXXXXXXXX`)처럼 `X`(또는 숫자가 아닌 문자)가
 *   포함된 값은 무효로 취급한다.
 *
 * @param {unknown} id - 검사할 client id 값.
 * @returns {boolean} 유효한 AdSense client id이면 true.
 */
export const isValidAdSenseClientId = (id) => {
  if (typeof id !== 'string') {
    return false;
  }

  const trimmed = id.trim();
  if (trimmed.length === 0) {
    return false;
  }

  // `ca-pub-` 접두사 + 1자리 이상의 숫자열만 허용.
  return /^ca-pub-\d+$/.test(trimmed);
};

export default isValidAdSenseClientId;
