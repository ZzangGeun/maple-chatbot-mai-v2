// 스키마 매핑 함수(chatSchema.js)에 대한 속성 기반 테스트.
// Feature: frontend-integration-design-improvements, Property 5: 계약을 따르는 응답은 정의된 단일 필드로 매핑된다
import { describe, it, expect } from 'vitest';
import fc from 'fast-check';
import {
  mapRoom,
  mapMessage,
  mapRoomsResponse,
  mapMessagesResponse,
} from './chatSchema';

// --- 스마트 제너레이터: 스키마 계약을 따르는 입력만 생성한다 ---

// 계약상 필수 값은 존재해야 하므로(undefined/null 아님) 비-공백 문자열을 사용한다.
const nonEmptyString = fc.string({ minLength: 1 }).filter((s) => s.trim().length > 0);

// 계약 Room: { id, room_name, created_at }
// 대체 필드 분기가 없음을 검증하기 위해, 폐기된 `updated_at`을 서로 다른 값으로 함께 주입한다.
const roomArb = fc.record({
  id: fc.uuid(),
  room_name: nonEmptyString,
  created_at: nonEmptyString,
  // decoy: 매핑은 이 값을 절대 사용해서는 안 된다(updated_at 대체 폐기).
  updated_at: fc.constant('DECOY_updated_at'),
});

// 계약 Message: { id, sender_type, message_content, thinking?, sent_at }
// 대체 필드(`role`, `content`) 분기가 없음을 검증하기 위해 decoy 값을 함께 주입한다.
const messageArb = fc.record(
  {
    id: fc.integer(),
    sender_type: fc.constantFrom('user', 'assistant'),
    message_content: fc.string(),
    thinking: fc.option(fc.string(), { nil: undefined }),
    sent_at: nonEmptyString,
    // decoy: 매핑은 이 대체 필드들을 절대 사용해서는 안 된다.
    role: fc.constant('DECOY_role'),
    content: fc.constant('DECOY_content'),
  },
  { requiredKeys: ['id', 'sender_type', 'message_content', 'sent_at', 'role', 'content'] }
);

describe('chatSchema 매핑 함수 (Property 5)', () => {
  it('계약을 따르는 Room/Message 응답은 대체 필드 분기 없이 단일 계약 필드로 매핑된다', () => {
    fc.assert(
      fc.property(
        fc.array(roomArb, { maxLength: 20 }),
        fc.array(messageArb, { maxLength: 20 }),
        (rooms, messages) => {
          // --- Room 매핑: 세션 타임스탬프는 created_at으로 단일화 ---
          const roomsResult = mapRoomsResponse({ rooms });
          expect(roomsResult).toHaveLength(rooms.length);
          rooms.forEach((room, i) => {
            const mapped = roomsResult[i];
            expect(mapped.id).toBe(room.id);
            expect(mapped.room_name).toBe(room.room_name);
            // 세션 타임스탬프 = created_at (updated_at 대체 사용 금지)
            expect(mapped.created_at).toBe(room.created_at);
            expect(mapped.created_at).not.toBe(room.updated_at);
            // 폐기된 대체 필드는 UI 모델에 포함되지 않는다.
            expect(mapped).not.toHaveProperty('updated_at');
            // 개별 mapRoom도 동일하게 동작한다.
            expect(mapRoom(room)).toEqual(mapped);
          });

          // --- Message 매핑: role = sender_type, content = message_content ---
          const messagesResult = mapMessagesResponse({ messages });
          expect(messagesResult).toHaveLength(messages.length);
          messages.forEach((message, i) => {
            const mapped = messagesResult[i];
            expect(mapped.id).toBe(message.id);
            // role은 sender_type에서만 매핑된다(role 대체 분기 금지).
            expect(mapped.role).toBe(message.sender_type);
            expect(mapped.role).not.toBe(message.role);
            // content는 message_content에서만 매핑된다(content 대체 분기 금지).
            expect(mapped.content).toBe(message.message_content);
            expect(mapped.content).not.toBe(message.content);
            expect(mapped.sent_at).toBe(message.sent_at);
            // thinking은 선택 필드: 없으면 빈 문자열.
            expect(mapped.thinking).toBe(
              message.thinking === undefined || message.thinking === null
                ? ''
                : message.thinking
            );
            // 개별 mapMessage도 동일하게 동작한다.
            expect(mapMessage(message)).toEqual(mapped);
          });

          return true;
        }
      ),
      { numRuns: 100 }
    );
  });
});
