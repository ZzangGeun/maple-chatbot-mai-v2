import React from 'react';
import { act, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import App from './App';
import * as authApi from './api/auth';
import * as homeApi from './api/home';
import * as characterApi from './api/character';
import * as chatApi from './api/chat';
import * as communityApi from './api/community';

vi.mock('./api/auth', () => ({
  getUserInfo: vi.fn(), login: vi.fn(), signup: vi.fn(), logout: vi.fn(),
}));
vi.mock('./api/home', () => ({ getHomeData: vi.fn() }));
vi.mock('./api/character', () => ({ searchCharacter: vi.fn() }));
vi.mock('./api/chat', () => ({
  createSession: vi.fn(), getSessions: vi.fn(), getMessages: vi.fn(),
  deleteSession: vi.fn(), streamMessage: vi.fn(),
}));
vi.mock('./api/community', () => ({
  getCommunityPosts: vi.fn(), createCommunityPost: vi.fn(),
}));

const character = {
  basic_info: {
    character_name: '메이의친구', world_name: '스카니아', character_level: 260,
    character_class: '비숍', character_class_level: '6', character_gender: '여',
    character_guild_name: '모험가', character_popularity: 25,
  },
  stat_info: { '전투력': '1234567', 'INT': '12345' },
  item_info: { item_equipment: {} },
};

// 입력 이벤트와 API 응답으로 생기는 상태 변경을 함께 기다립니다.
const setupUser = () => {
  const user = userEvent.setup();
  return {
    type: (...args) => act(async () => { await user.type(...args); }),
    click: (...args) => act(async () => { await user.click(...args); }),
  };
};
const renderApp = () => act(async () => { render(<App />); });

describe('주요 화면의 사용자 흐름', () => {
  beforeEach(() => {
    vi.resetAllMocks();
    window.history.replaceState({}, '', '/');
    authApi.getUserInfo.mockRejectedValue({ response: { status: 401 } });
    authApi.signup.mockResolvedValue({ data: { message: '회원가입이 완료되었습니다.' } });
    homeApi.getHomeData.mockResolvedValue({
      data: { notices: { updates: [], events: [], cashshop: [] }, ranking: [] },
    });
    characterApi.searchCharacter.mockResolvedValue({ data: { success: true, data: character } });
    chatApi.createSession.mockResolvedValue({
      data: {
        success: true,
        room: {
          id: '550e8400-e29b-41d4-a716-446655440000',
          room_name: '새로운 대화', created_at: '2026-10-03T09:00:00+09:00',
        },
      },
    });
    chatApi.getSessions.mockResolvedValue({ data: { success: true, rooms: [] } });
    chatApi.getMessages.mockResolvedValue({ data: { success: true, messages: [] } });
    communityApi.getCommunityPosts.mockResolvedValue({ data: { posts: [], categoryCounts: { all: 0 } } });
  });

  it('홈에서 작성한 질문을 대화 화면에 전달하고 전송 전에 확인할 수 있다', async () => {
    const user = setupUser();
    await renderApp();
    await user.type(screen.getByRole('textbox', { name: '메이에게 물어볼 질문' }), '200레벨 사냥터 추천해줘');
    await user.click(screen.getByRole('button', { name: '메이에게 질문하기' }));

    expect(window.location.pathname).toBe('/chat');
    const chatInput = await screen.findByRole('textbox', { name: '메이플 AI에게 질문하기' });
    expect(chatInput).toHaveValue('200레벨 사냥터 추천해줘');
    await waitFor(() => expect(chatInput).toBeEnabled());
    expect(screen.getByRole('button', { name: '질문 보내기' })).toBeEnabled();
    expect(chatApi.streamMessage).not.toHaveBeenCalled();
  });

  it('로그인에서 회원가입으로 이동해 서버가 요구하는 필드를 제출한다', async () => {
    const user = setupUser();
    await renderApp();
    await user.click(screen.getByRole('button', { name: '로그인', exact: true }));
    const loginDialog = await screen.findByRole('dialog', { name: '모험을 이어가볼까요?' });
    expect(within(loginDialog).getByLabelText('아이디')).toBeRequired();
    expect(within(loginDialog).getByLabelText('비밀번호')).toHaveAttribute('autoComplete', 'current-password');
    await user.click(within(loginDialog).getByRole('button', { name: /회원가입/ }));

    const signupDialog = await screen.findByRole('dialog', { name: '나만의 모험 노트 만들기' });
    expect(screen.queryByRole('dialog', { name: '모험을 이어가볼까요?' })).not.toBeInTheDocument();
    for (const label of ['아이디', '비밀번호', '비밀번호 확인', '캐릭터 닉네임', '넥슨 API 키']) {
      expect(within(signupDialog).getByLabelText(label, { exact: true })).toBeRequired();
    }
    expect(within(signupDialog).getByLabelText('비밀번호', { exact: true })).toHaveAttribute('minLength', '8');
    expect(within(signupDialog).getByLabelText('넥슨 API 키')).toHaveAttribute('type', 'password');

    await user.type(within(signupDialog).getByLabelText('아이디', { exact: true }), 'mapler7');
    await user.type(within(signupDialog).getByLabelText('비밀번호', { exact: true }), 'password123');
    await user.type(within(signupDialog).getByLabelText('비밀번호 확인'), 'password123');
    await user.type(within(signupDialog).getByLabelText('캐릭터 닉네임'), '메이의친구');
    await user.type(within(signupDialog).getByLabelText('넥슨 API 키'), 'test-api-key');
    await user.click(within(signupDialog).getByRole('button', { name: '회원가입', exact: true }));

    await waitFor(() => expect(authApi.signup).toHaveBeenCalledWith({
      username: 'mapler7', password: 'password123', confirm_password: 'password123',
      maple_nickname: '메이의친구', nexon_api_key: 'test-api-key',
    }));
    expect(await screen.findByRole('dialog', { name: '모험을 이어가볼까요?' })).toBeInTheDocument();
  });

  it('홈 검색 결과에서 도감으로 이동하면 같은 캐릭터를 자동으로 조회한다', async () => {
    const user = setupUser();
    await renderApp();
    await user.type(screen.getByLabelText('캐릭터 닉네임'), '메이의친구');
    await user.click(screen.getByRole('button', { name: '캐릭터 검색', exact: true }));
    expect(await screen.findByText('메이의친구')).toBeInTheDocument();
    expect(characterApi.searchCharacter).toHaveBeenCalledTimes(1);

    await user.click(screen.getByRole('link', { name: '스탯과 장비 자세히 보기' }));

    expect(window.location.pathname).toBe('/character');
    expect(window.history.state.usr).toEqual({ characterName: '메이의친구' });
    expect(screen.getByLabelText('캐릭터 닉네임')).toHaveValue('메이의친구');
    expect(await screen.findByRole('heading', { name: '메이의친구', level: 2 })).toBeInTheDocument();
    expect(characterApi.searchCharacter).toHaveBeenCalledTimes(2);
    expect(characterApi.searchCharacter).toHaveBeenNthCalledWith(2, '메이의친구');
    expect(screen.getByRole('tab', { name: '기본 정보' })).toHaveAttribute('aria-selected', 'true');
  });
});
