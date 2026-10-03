import { act, renderHook, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { AuthProvider, normalizeAuthUser, useAuth } from './AuthContext';
import * as authApi from '../api/auth';

vi.mock('../api/auth', () => ({
  getUserInfo: vi.fn(),
  login: vi.fn(),
  signup: vi.fn(),
  logout: vi.fn(),
}));

const account = { id: 7, username: 'mapler7', email: '' };

describe('인증 API 응답 호환', () => {
  beforeEach(() => vi.resetAllMocks());

  it.each([
    { user: account, maple_nickname: '메이의친구' },
    { ...account, profile: { maple_nickname: '메이의친구' } },
  ])('로그인 직후와 새로고침 후에도 같은 계정과 캐릭터를 표시한다', (response) => {
    expect(normalizeAuthUser(response)).toMatchObject({
      id: 7,
      username: 'mapler7',
      maple_nickname: '메이의친구',
    });
  });

  it('가입 후 로그인 폼을 사용할 수 있도록 로딩 상태를 해제한다', async () => {
    authApi.getUserInfo.mockRejectedValue({ response: { status: 401 } });
    authApi.signup.mockResolvedValue({ data: { message: '가입 완료' } });
    const { result } = renderHook(() => useAuth(), { wrapper: AuthProvider });
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    let signupResult;
    await act(async () => {
      signupResult = await result.current.register({ username: 'mapler7' });
    });

    expect(signupResult.success).toBe(true);
    expect(result.current.isLoading).toBe(false);
    expect(result.current.isLoggedIn).toBe(false);
  });
});
