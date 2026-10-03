import { act, renderHook, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import * as chatApi from '../api/chat';
import { useChat } from './useChat';

vi.mock('../api/chat', () => ({
  createSession: vi.fn(),
  getSessions: vi.fn(),
  getMessages: vi.fn(),
  streamMessage: vi.fn(),
}));

const room = id => ({ id, room_name: '모험 이야기', created_at: '2026-10-03T00:00:00Z' });
const savedMessage = content => ({ id: 1, sender_type: 'assistant', message_content: content, sent_at: '2026-10-03T00:00:00Z' });
const deferred = () => {
  let resolve;
  const promise = new Promise(done => { resolve = done; });
  return { promise, resolve };
};

beforeEach(() => {
  vi.resetAllMocks();
  vi.spyOn(console, 'error').mockImplementation(() => {});
  chatApi.createSession.mockResolvedValue({ data: { room: room('guest-room') } });
  chatApi.getSessions.mockResolvedValue({ data: { rooms: [room('account-room')] } });
  chatApi.getMessages.mockResolvedValue({ data: { messages: [savedMessage('저장된 답변')] } });
  chatApi.streamMessage.mockImplementation(async (_session, _question, onChunk, onDone) => {
    onChunk({ type: 'token', content: '모험을 도와드릴게요.' });
    onDone();
  });
});

afterEach(() => { vi.restoreAllMocks(); });

describe('useChat conversation safeguards', () => {
  it('최초 인증 확인 전에는 방을 생성하지 않고 확인 후 기존 로그인 대화를 불러온다', async () => {
    const { result, rerender } = renderHook(
      ({ loggedIn, authReady }) => useChat(loggedIn, authReady),
      { initialProps: { loggedIn: false, authReady: false } },
    );
    expect(result.current.isInitializing).toBe(true);
    expect(result.current.currentSessionId).toBeNull();
    expect(chatApi.createSession).not.toHaveBeenCalled();
    expect(chatApi.getSessions).not.toHaveBeenCalled();

    rerender({ loggedIn: true, authReady: true });
    await waitFor(() => expect(result.current.isInitializing).toBe(false));
    expect(result.current.currentSessionId).toBe('account-room');
    expect(result.current.messages[0].content).toBe('저장된 답변');
    expect(chatApi.getSessions).toHaveBeenCalledTimes(1);
    expect(chatApi.createSession).not.toHaveBeenCalled();
  });

  it('shows a stream error and retries the failed turn without duplicating the question', async () => {
    const { result } = renderHook(() => useChat(false));
    await waitFor(() => expect(result.current.isInitializing).toBe(false));
    chatApi.streamMessage.mockImplementationOnce(async (_session, _question, onChunk, onDone) => {
      onChunk({ type: 'error', content: 'temporary failure' });
      onDone();
    });

    await act(async () => { await result.current.sendMessage('사냥터를 추천해줘'); });
    expect(result.current.error.kind).toBe('send');
    expect(result.current.messages[1].isError).toBe(true);
    expect(result.current.isLoading).toBe(false);

    await act(async () => { await result.current.sendMessage('사냥터를 추천해줘', true); });
    expect(result.current.error).toBeNull();
    expect(result.current.messages).toHaveLength(2);
    expect(result.current.messages[0].content).toBe('사냥터를 추천해줘');
    expect(result.current.messages[1].content).toBe('모험을 도와드릴게요.');
    expect(chatApi.streamMessage).toHaveBeenCalledTimes(2);
  });

  it('blocks simultaneous sends and session changes while an answer is streaming', async () => {
    const stream = deferred();
    chatApi.streamMessage.mockImplementation(() => stream.promise);
    const { result } = renderHook(() => useChat(false));
    await waitFor(() => expect(result.current.isInitializing).toBe(false));
    let firstSend;

    act(() => {
      firstSend = result.current.sendMessage('첫 질문');
      result.current.sendMessage('중복 질문');
      result.current.createNewChat();
      result.current.loadMessages('another-room');
    });
    expect(chatApi.streamMessage).toHaveBeenCalledTimes(1);
    expect(chatApi.createSession).toHaveBeenCalledTimes(1);
    expect(chatApi.getMessages).not.toHaveBeenCalled();
    expect(result.current.messages.filter(message => message.role === 'user')).toHaveLength(1);

    await act(async () => { stream.resolve(); await firstSend; });
    expect(result.current.isLoading).toBe(false);
  });

  it('ignores a previous guest stream after switching to a signed-in account', async () => {
    const stream = deferred();
    let receiveOldChunk;
    chatApi.streamMessage.mockImplementation((_session, _question, onChunk) => {
      receiveOldChunk = onChunk;
      return stream.promise;
    });
    const { result, rerender } = renderHook(({ loggedIn }) => useChat(loggedIn), { initialProps: { loggedIn: false } });
    await waitFor(() => expect(result.current.isInitializing).toBe(false));
    let firstSend;
    act(() => { firstSend = result.current.sendMessage('게스트 질문'); });

    rerender({ loggedIn: true });
    await waitFor(() => {
      expect(result.current.isInitializing).toBe(false);
      expect(result.current.currentSessionId).toBe('account-room');
    });
    await act(async () => {
      receiveOldChunk({ type: 'token', content: '늦은 게스트 답변' });
      stream.resolve();
      await firstSend;
    });
    expect(result.current.messages.map(message => message.content)).toEqual(['저장된 답변']);
    expect(result.current.error).toBeNull();
  });

  it('ignores a stale history response after an account change', async () => {
    const history = deferred();
    const { result, rerender } = renderHook(({ loggedIn }) => useChat(loggedIn), { initialProps: { loggedIn: false } });
    await waitFor(() => expect(result.current.isInitializing).toBe(false));
    chatApi.getMessages.mockImplementation(sessionId => sessionId === 'old-room'
      ? history.promise
      : Promise.resolve({ data: { messages: [savedMessage('현재 계정의 답변')] } }));
    let oldLoad;
    act(() => { oldLoad = result.current.loadMessages('old-room'); });

    rerender({ loggedIn: true });
    await waitFor(() => expect(result.current.currentSessionId).toBe('account-room'));
    await waitFor(() => expect(result.current.isInitializing).toBe(false));
    await act(async () => {
      history.resolve({ data: { messages: [savedMessage('이전 계정의 답변')] } });
      await oldLoad;
    });
    expect(result.current.messages[0].content).toBe('현재 계정의 답변');
    expect(result.current.currentSessionId).toBe('account-room');
  });

  it('ends loading and exposes an error when a stream finishes without an answer', async () => {
    chatApi.streamMessage.mockImplementation(async (_session, _question, _onChunk, onDone) => { onDone(); });
    const { result } = renderHook(() => useChat(false));
    await waitFor(() => expect(result.current.isInitializing).toBe(false));

    await act(async () => { await result.current.sendMessage('보스 준비는 어떻게 해?'); });
    expect(result.current.isLoading).toBe(false);
    expect(result.current.error.kind).toBe('send');
    expect(result.current.messages[1].isError).toBe(true);
  });
});
