import { act, renderHook } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { useCharacterSearch } from './useCharacterSearch';
import { searchCharacter } from '../api/character';

vi.mock('../api/character', () => ({ searchCharacter: vi.fn() }));

describe('홈 캐릭터 검색', () => {
  beforeEach(() => vi.resetAllMocks());

  it('검색창 입력 중 자동검색 콜백을 유지하고 현재 API 성공 응답을 표시한다', async () => {
    const character = { basic_info: { character_name: '메이의친구' } };
    searchCharacter.mockResolvedValue({ data: { success: true, data: character } });
    const { result } = renderHook(() => useCharacterSearch());
    const originalSearch = result.current.handleCharacterSearch;

    act(() => result.current.setCharSearchText('  메이의친구  '));
    expect(result.current.handleCharacterSearch).toBe(originalSearch);
    await act(async () => { await result.current.handleCharacterSearch(); });

    expect(searchCharacter).toHaveBeenCalledWith('메이의친구');
    expect(result.current.characterInfo).toEqual(character);
    expect(result.current.characterError).toBe('');
    expect(result.current.isCharLoading).toBe(false);
  });

  it('조회 실패 메시지를 화면에 표시할 상태로 반환한다', async () => {
    searchCharacter.mockRejectedValue({
      response: { data: { error: { code: 'CHARACTER_NOT_FOUND', message: '캐릭터를 찾을 수 없습니다.' } } },
    });
    const { result } = renderHook(() => useCharacterSearch());
    await act(async () => { await result.current.handleCharacterSearch('없는캐릭터'); });

    expect(result.current.characterError).toBe('캐릭터를 찾을 수 없습니다.');
    expect(result.current.characterInfo).toBeNull();
    expect(result.current.isCharLoading).toBe(false);
  });

  it('이전 검색 응답이 늦게 도착해도 최신 캐릭터를 유지한다', async () => {
    let resolveFirst;
    searchCharacter.mockImplementationOnce(() => new Promise(resolve => { resolveFirst = resolve; }));
    searchCharacter.mockResolvedValueOnce({ data: { success: true, data: { name: '두번째' } } });
    const { result } = renderHook(() => useCharacterSearch());
    let firstSearch;
    act(() => { firstSearch = result.current.handleCharacterSearch('첫번째'); });
    await act(async () => { await result.current.handleCharacterSearch('두번째'); });
    await act(async () => {
      resolveFirst({ data: { success: true, data: { name: '첫번째' } } });
      await firstSearch;
    });

    expect(result.current.characterInfo).toEqual({ name: '두번째' });
  });
});
