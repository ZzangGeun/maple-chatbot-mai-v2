// AdSense client id 유효성 헬퍼(adsense.js)에 대한 속성 기반 테스트.
// Feature: frontend-integration-design-improvements, Property 10: AdSense는 유효한 client id일 때만 로드된다
import { describe, it, expect } from 'vitest';
import fc from 'fast-check';
import { isValidAdSenseClientId, isValidAdSenseSlotId } from './adsense';

// --- 스마트 제너레이터 ---

// 유효한 client id: `ca-pub-` + 1자리 이상의 순수 숫자열.
const validClientIdArb = fc
  .stringMatching(/^[0-9]+$/)
  .filter((s) => s.length >= 1)
  .map((digits) => `ca-pub-${digits}`);

// 무효한 client id 후보: 빈 값, 플레이스홀더, 접두사 누락, 숫자 아닌 문자 포함 등.
const invalidClientIdArb = fc.oneof(
  fc.constant(''),
  fc.constant('   '),
  fc.constant('ca-pub-XXXXXXXXXXXXXXXX'), // 플레이스홀더
  fc.constant('ca-pub-'), // 숫자열 없음
  fc.constant('ca-pub-123abc'), // 숫자 아닌 문자 포함
  fc.constant('pub-123456'), // 접두사 누락
  fc.constant('ca-pub123456'), // 하이픈 누락
  // 접두사 뒤에 숫자가 아닌 문자를 최소 하나 포함하는 임의 문자열.
  fc.string().map((s) => `ca-pub-${s}`).filter((s) => !/^ca-pub-\d+$/.test(s)),
);

// 문자열이 아닌 임의 값(number, boolean, null, undefined, object 등).
const nonStringArb = fc
  .anything()
  .filter((v) => typeof v !== 'string');

describe('isValidAdSenseClientId (Property 10)', () => {
  // Validates: Requirements 11.1, 11.2
  it('유효한 ca-pub-<digits> client id에 대해서만 true를 반환한다', () => {
    fc.assert(
      fc.property(validClientIdArb, (id) => {
        expect(isValidAdSenseClientId(id)).toBe(true);
      }),
      { numRuns: 100 },
    );
  });

  // Validates: Requirements 11.1, 11.2
  it('무효한 client id(빈 값/플레이스홀더/형식 위반)에 대해 false를 반환한다', () => {
    fc.assert(
      fc.property(invalidClientIdArb, (id) => {
        expect(isValidAdSenseClientId(id)).toBe(false);
      }),
      { numRuns: 100 },
    );
  });

  // Validates: Requirements 11.1, 11.2
  it('문자열이 아닌 값에 대해 false를 반환한다', () => {
    fc.assert(
      fc.property(nonStringArb, (value) => {
        expect(isValidAdSenseClientId(value)).toBe(false);
      }),
      { numRuns: 100 },
    );
  });
});

describe('isValidAdSenseSlotId', () => {
  it('숫자로만 구성된 광고 슬롯 ID만 허용한다', () => {
    fc.assert(
      fc.property(fc.stringMatching(/^[0-9]+$/), (id) => {
        expect(isValidAdSenseSlotId(id)).toBe(true);
      }),
      { numRuns: 100 },
    );
  });

  it('빈 값, 플레이스홀더, 문자열이 아닌 값은 거부한다', () => {
    expect(isValidAdSenseSlotId('')).toBe(false);
    expect(isValidAdSenseSlotId('YOUR_SLOT_ID')).toBe(false);
    expect(isValidAdSenseSlotId(1234567890)).toBe(false);
  });
});
