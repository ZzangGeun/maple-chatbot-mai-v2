// Vitest 전역 테스트 setup 파일
// @testing-library/jest-dom matcher(toBeInTheDocument 등)를 Vitest의 expect에 등록한다.
import '@testing-library/jest-dom/vitest';

import { afterEach } from 'vitest';
import { cleanup } from '@testing-library/react';

// 각 테스트 후 렌더된 DOM을 정리하여 테스트 간 격리를 보장한다.
afterEach(() => {
  cleanup();
});
