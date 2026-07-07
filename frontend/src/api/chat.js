import client, { getCookie } from './client';

// 세션 생성
export const createSession = () =>
  client.post('/api/v1/chat/rooms/');

// 세션 목록 조회
export const getSessions = () =>
  client.get('/api/v1/chat/rooms/');

// 세션의 메시지 목록 조회
export const getMessages = (sessionId) =>
  client.get(`/api/v1/chat/rooms/${sessionId}/messages/`);

// 세션 삭제
export const deleteSession = (sessionId) =>
  client.delete(`/api/v1/chat/rooms/${sessionId}/`);

// SSE 데이터 조각 하나를 처리한다. '[DONE]' 종료 신호면 true를 반환한다.
const handleSSEData = (jsonStr, onChunk) => {
  if (jsonStr === '[DONE]') {
    return true; // 종료 신호
  }
  try {
    const data = JSON.parse(jsonStr);
    onChunk(data);
  } catch (e) {
    // JSON 파싱 실패 조각은 스트림 전체를 중단시키지 않고 건너뛴다(경고 로깅).
    console.warn('Failed to parse SSE JSON:', e);
  }
  return false;
};

// 스트리밍 메시지 전송
// 공용 API_Client(client.js)와 동일한 CSRF/자격 증명 정책을 적용한다.
export const streamMessage = async (sessionId, content, onChunk, onDone, onError) => {
  // '[DONE]' 수신과 스트림 종료 경로가 겹칠 수 있으므로 정확히 1회만 호출하도록 가드한다.
  let doneCalled = false;
  const callDone = () => {
    if (!doneCalled) {
      doneCalled = true;
      onDone();
    }
  };

  try {
    // client.js의 getCookie를 재사용하여 CSRF 토큰을 읽는다.
    const csrftoken = getCookie('csrftoken');
    const response = await fetch(`/api/v1/chat/rooms/${sessionId}/stream/`, {
      method: 'POST',
      credentials: 'include', // 자격 증명(쿠키) 포함 (요구사항 1.2)
      headers: {
        'Content-Type': 'application/json',
        // CSRF 토큰을 X-CSRFToken 헤더로 주입 (요구사항 1.1, 1.3)
        ...(csrftoken ? { 'X-CSRFToken': csrftoken } : {}),
      },
      body: JSON.stringify({ content }),
    });

    // 성공 범위(200-299)를 벗어나면 상태 코드를 포함한 오류로 onError 호출, onDone 미호출 (요구사항 1.4)
    if (!response.ok) {
      onError({ status: response.status, message: `HTTP error! status: ${response.status}` });
      return;
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const events = buffer.split('\n\n'); // SSE 이벤트는 이중 개행으로 구분
      buffer = events.pop(); // 마지막 미완성 조각은 버퍼에 유지

      for (const event of events) {
        const trimmedLine = event.trim();
        if (!trimmedLine.startsWith('data: ')) continue; // data: 접두사 없는 라인 무시

        const jsonStr = trimmedLine.substring(6).trim();
        const isDone = handleSSEData(jsonStr, onChunk);
        if (isDone) {
          callDone(); // 종료 신호 수신 시 정확히 1회 호출 (요구사항 1.5)
          return;
        }
      }
    }

    // 스트림 flush 후 남은 버퍼 처리
    const remaining = buffer.trim();
    if (remaining.startsWith('data: ')) {
      const jsonStr = remaining.substring(6).trim();
      handleSSEData(jsonStr, onChunk);
    }

    // '[DONE]' 없이 스트림이 끝난 경우에도 완료 콜백을 정확히 1회 호출 (요구사항 1.5)
    callDone();
  } catch (error) {
    onError(error);
  }
};
