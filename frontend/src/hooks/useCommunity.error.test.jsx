import { act, renderHook, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { createCommunityPost, getCommunityPosts } from '../api/community';
import { useCommunity } from './useCommunity';

vi.mock('../api/community', () => ({
    getCommunityPosts: vi.fn(),
    createCommunityPost: vi.fn()
}));

describe('커뮤니티 오류 및 재시도', () => {
    beforeEach(() => {
        vi.resetAllMocks();
        getCommunityPosts.mockResolvedValue({ data: { posts: [], categoryCounts: {} } });
        vi.spyOn(console, 'error').mockImplementation(() => {});
    });

    afterEach(() => vi.restoreAllMocks());

    it('목록 요청 실패를 빈 목록과 구분하고 재시도하면 실제 응답을 표시한다', async () => {
        const post = { id: 1, category: 'free', title: '첫 이야기' };
        getCommunityPosts.mockRejectedValueOnce(new Error('offline'));
        const { result } = renderHook(() => useCommunity());

        await waitFor(() => expect(result.current.isLoading).toBe(false));
        expect(result.current.error).toBeTruthy();
        expect(result.current.posts).toEqual([]);

        getCommunityPosts.mockResolvedValueOnce({ data: { posts: [post], categoryCounts: { all: 1, free: 1 } } });
        act(() => result.current.retryPosts());

        await waitFor(() => expect(result.current.posts).toEqual([post]));
        expect(result.current.error).toBeNull();
        expect(result.current.categories.find(category => category.id === 'all').count).toBe(1);
        expect(getCommunityPosts).toHaveBeenCalledTimes(2);
    });

    it('등록 실패 시 입력을 보존하고 다시 등록하면 모달을 닫는다', async () => {
        const { result } = renderHook(() => useCommunity());
        await waitFor(() => expect(result.current.isLoading).toBe(false));
        const draft = { title: '도움이 필요해요', content: '질문 내용', category: 'question' };
        act(() => {
            result.current.setWriteForm(draft);
            result.current.setShowWriteModal(true);
        });

        createCommunityPost.mockRejectedValueOnce(new Error('offline'));
        await act(async () => result.current.handleSubmitPost({ preventDefault: vi.fn() }));

        expect(result.current.submitError).toBeTruthy();
        expect(result.current.writeForm).toEqual(draft);
        expect(result.current.showWriteModal).toBe(true);

        createCommunityPost.mockResolvedValueOnce({ data: { success: true } });
        await act(async () => result.current.handleSubmitPost({ preventDefault: vi.fn() }));

        expect(result.current.submitError).toBeNull();
        expect(result.current.showWriteModal).toBe(false);
        expect(result.current.writeForm).toEqual({ title: '', content: '', category: 'free' });
        expect(createCommunityPost).toHaveBeenLastCalledWith(draft);
    });
});
