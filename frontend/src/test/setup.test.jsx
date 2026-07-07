// 테스트 인프라(Vitest + fast-check + @testing-library/react)가
// 올바르게 구성되었는지 확인하는 스모크 테스트.
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import fc from 'fast-check';

describe('test infrastructure', () => {
  it('runs a basic Vitest assertion', () => {
    expect(1 + 1).toBe(2);
  });

  it('registers jest-dom matchers and renders with @testing-library/react', () => {
    render(<button aria-label="send">➤</button>);
    const button = screen.getByRole('button', { name: 'send' });
    expect(button).toBeInTheDocument();
  });

  it('runs fast-check property-based assertions', () => {
    fc.assert(
      fc.property(fc.integer(), fc.integer(), (a, b) => {
        return a + b === b + a;
      }),
      { numRuns: 100 }
    );
  });
});
