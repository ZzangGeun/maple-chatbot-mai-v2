import client from './client';

// 세션 생성
export const createSession = () =>
  client.post('/api/v1/chat/sessions/create/');

// 세션 목록 조회
export const getSessions = () =>
  client.get('/api/v1/chat/sessions/');

// 세션의 메시지 목록 조회
export const getMessages = (sessionId) =>
  client.get(`/api/v1/chat/sessions/${sessionId}/messages/`);

// 세션 삭제
export const deleteSession = (sessionId) =>
  client.delete(`/api/v1/chat/sessions/${sessionId}/delete/`);

// 스트리밍 메시지 전송
export const streamMessage = async (sessionId, content, onChunk, onDone, onError) => {
  try {
    const response = await fetch(`/api/v1/chat/sessions/${sessionId}/stream/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ content })
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n\n'); // SSE messages are separated by double newline
      buffer = lines.pop(); // Keep the last incomplete chunk

      for (const line of lines) {
        const trimmedLine = line.trim();
        if (!trimmedLine.startsWith('data: ')) continue;

        const jsonStr = trimmedLine.substring(6).trim();
        if (jsonStr === '[DONE]') {
          onDone();
          return;
        }

        try {
          const data = JSON.parse(jsonStr);
          onChunk(data);
        } catch (e) {
          console.warn('Failed to parse SSE JSON:', e);
        }
      }
    }

    // Process remaining buffer if any (unlikely for SSE but good practice)
    if (buffer.trim().startsWith('data: ')) {
      const jsonStr = buffer.trim().substring(6).trim();
      if (jsonStr !== '[DONE]') {
        try { onChunk(JSON.parse(jsonStr)); } catch (e) { }
      }
    }

    onDone();
  } catch (error) {
    onError(error);
  }
};
