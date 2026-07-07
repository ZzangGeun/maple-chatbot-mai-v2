/**
 * 채팅 스키마 매핑/검증 모듈 (Schema_Contract)
 *
 * 백엔드가 실제로 내보내는 단일 필드 계약을 UI 정규화 모델로 매핑한다.
 * 대체 필드(`||`) 방어 코드 없이 아래 계약 필드만 읽는다.
 *
 * 계약 (Requirements 3.1, 3.2, 3.3):
 *   - 세션 목록 응답: { success, rooms: Room[] }
 *   - 세션 생성 응답:  { success, room: Room }
 *   - 메시지 목록 응답: { success, messages: Message[] }
 *   - Room:    { id, room_name, created_at }
 *   - Message: { id, sender_type, message_content, thinking?, sent_at }
 *
 * UI 정규화 모델:
 *   - UIMessage: { id, role, content, thinking, sent_at }
 *       role    <- sender_type
 *       content <- message_content
 *   - UIRoom:    { id, room_name, created_at }
 *
 * 필수 필드 누락 시 무음 실패를 금지한다(Requirements 3.4):
 *   console.error로 기록한 뒤 SchemaValidationError를 던진다.
 */

/**
 * 스키마 계약 위반(필수 필드 누락 등)을 나타내는 오류.
 */
export class SchemaValidationError extends Error {
  constructor(message, { context, missingFields } = {}) {
    super(message);
    this.name = 'SchemaValidationError';
    this.context = context;
    this.missingFields = missingFields;
  }
}

// Room 필수 필드
const ROOM_REQUIRED_FIELDS = ['id', 'room_name', 'created_at'];
// Message 필수 필드 (thinking은 선택 필드이므로 제외)
const MESSAGE_REQUIRED_FIELDS = ['id', 'sender_type', 'message_content', 'sent_at'];

/**
 * 필드가 존재하는지 검사한다. undefined/null은 누락으로 간주한다.
 * (빈 문자열 ''은 유효한 값으로 허용한다.)
 */
function isMissing(value) {
  return value === undefined || value === null;
}

/**
 * 객체에서 누락된 필수 필드 목록을 반환한다.
 * 객체가 아니면 모든 필수 필드가 누락된 것으로 취급한다.
 */
function findMissingFields(obj, requiredFields) {
  if (obj === null || typeof obj !== 'object' || Array.isArray(obj)) {
    return [...requiredFields];
  }
  return requiredFields.filter((field) => isMissing(obj[field]));
}

/**
 * 누락 필드가 있으면 console.error로 기록하고 SchemaValidationError를 던진다.
 */
function assertNoMissingFields(obj, requiredFields, context) {
  const missingFields = findMissingFields(obj, requiredFields);
  if (missingFields.length > 0) {
    // 무음 실패 금지: 오류를 반드시 기록한다.
    console.error(
      `[chatSchema] ${context} 응답에 필수 필드가 누락되었습니다: ${missingFields.join(', ')}`,
      obj
    );
    throw new SchemaValidationError(
      `${context}: 필수 필드 누락 (${missingFields.join(', ')})`,
      { context, missingFields }
    );
  }
}

/**
 * 계약 Room 객체를 UI Room 모델로 매핑한다.
 * @param {{id: string, room_name: string, created_at: string}} room
 * @returns {{id: string, room_name: string, created_at: string}}
 */
export function mapRoom(room) {
  assertNoMissingFields(room, ROOM_REQUIRED_FIELDS, 'Room');
  return {
    id: room.id,
    room_name: room.room_name,
    created_at: room.created_at,
  };
}

/**
 * 계약 Message 객체를 UI 정규화 메시지 모델로 매핑한다.
 * role <- sender_type, content <- message_content.
 * thinking은 선택 필드이며 없으면 빈 문자열로 채운다.
 * @param {{id: number, sender_type: string, message_content: string, thinking?: string, sent_at: string}} message
 * @returns {{id: number, role: string, content: string, thinking: string, sent_at: string}}
 */
export function mapMessage(message) {
  assertNoMissingFields(message, MESSAGE_REQUIRED_FIELDS, 'Message');
  return {
    id: message.id,
    role: message.sender_type,
    content: message.message_content,
    thinking: isMissing(message.thinking) ? '' : message.thinking,
    sent_at: message.sent_at,
  };
}

/**
 * 세션 목록 응답({ rooms: Room[] })을 UI Room 배열로 매핑한다.
 * `rooms` 필드가 없거나 배열이 아니면 오류를 기록하고 던진다.
 * @param {{rooms: Array}} response
 * @returns {Array}
 */
export function mapRoomsResponse(response) {
  if (isMissing(response) || !Array.isArray(response.rooms)) {
    console.error(
      "[chatSchema] 세션 목록 응답에 필수 필드 'rooms'(배열)가 없습니다.",
      response
    );
    throw new SchemaValidationError("세션 목록 응답: 필수 필드 누락 (rooms)", {
      context: 'RoomsResponse',
      missingFields: ['rooms'],
    });
  }
  return response.rooms.map(mapRoom);
}

/**
 * 메시지 목록 응답({ messages: Message[] })을 UI 메시지 배열로 매핑한다.
 * `messages` 필드가 없거나 배열이 아니면 오류를 기록하고 던진다.
 * @param {{messages: Array}} response
 * @returns {Array}
 */
export function mapMessagesResponse(response) {
  if (isMissing(response) || !Array.isArray(response.messages)) {
    console.error(
      "[chatSchema] 메시지 목록 응답에 필수 필드 'messages'(배열)가 없습니다.",
      response
    );
    throw new SchemaValidationError("메시지 목록 응답: 필수 필드 누락 (messages)", {
      context: 'MessagesResponse',
      missingFields: ['messages'],
    });
  }
  return response.messages.map(mapMessage);
}
