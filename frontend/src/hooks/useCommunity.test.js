// Feature: frontend-integration-design-improvements, Property 4: 커뮤니티 목업 목록은 필터·정렬 계약을 만족한다
import { describe, it, expect } from 'vitest';
import fc from 'fast-check';
import { filterAndSortPosts } from './useCommunity';

const CATEGORY_IDS = ['free', 'question', 'guide', 'trade', 'guild'];
const SORT_CRITERIA = ['latest', 'popular', 'views'];

// 목업 게시글 형태를 따르는 임의 게시글 생성기.
// createdAt은 정렬 계약 검증을 위해 유효한 ISO 날짜 문자열로 제한한다.
const postArb = fc.record({
  id: fc.integer({ min: 1, max: 100000 }),
  category: fc.constantFrom(...CATEGORY_IDS),
  views: fc.integer({ min: 0, max: 1_000_000 }),
  likes: fc.integer({ min: 0, max: 1_000_000 }),
  comments: fc.integer({ min: 0, max: 1_000_000 }),
  createdAt: fc
    .date({ min: new Date('2000-01-01T00:00:00Z'), max: new Date('2030-12-31T23:59:59Z') })
    .map((d) => d.toISOString()),
});

// 다중 집합 관점의 부분집합 검사: result의 각 원소(참조)가 원본에 존재하고,
// 참조 등장 횟수가 원본을 초과하지 않아야 한다(원소 추가/복제 없음).
const isSubsetByReference = (result, original) => {
  const counts = new Map();
  for (const p of original) {
    counts.set(p, (counts.get(p) || 0) + 1);
  }
  for (const p of result) {
    const remaining = counts.get(p);
    if (!remaining || remaining <= 0) return false;
    counts.set(p, remaining - 1);
  }
  return true;
};

const sortKey = (post, sortBy) => {
  if (sortBy === 'latest') return new Date(post.createdAt).getTime();
  if (sortBy === 'popular') return post.likes + post.comments;
  if (sortBy === 'views') return post.views;
  return 0;
};

describe('filterAndSortPosts (Property 4)', () => {
  it('필터·정렬 계약을 만족한다: 부분집합 + 카테고리 일치 + 정렬', () => {
    fc.assert(
      fc.property(
        fc.array(postArb, { maxLength: 30 }),
        fc.constantFrom('all', ...CATEGORY_IDS),
        fc.constantFrom(...SORT_CRITERIA),
        (posts, category, sortBy) => {
          const result = filterAndSortPosts(posts, category, sortBy);

          // (a) 결과는 원본 집합의 부분집합이다.
          expect(isSubsetByReference(result, posts)).toBe(true);

          // (b) category != 'all'이면 모든 원소가 선택 카테고리와 일치한다.
          if (category !== 'all') {
            expect(result.every((p) => p.category === category)).toBe(true);
          } else {
            // 'all'이면 필터로 원소가 손실되지 않는다(개수 보존).
            expect(result.length).toBe(posts.length);
          }

          // (c) 선택된 정렬 기준에 따라 내림차순 정렬되어 있다.
          for (let i = 1; i < result.length; i++) {
            expect(sortKey(result[i - 1], sortBy)).toBeGreaterThanOrEqual(
              sortKey(result[i], sortBy)
            );
          }
        }
      ),
      { numRuns: 100 }
    );
  });
});
