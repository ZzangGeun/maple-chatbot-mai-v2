// Feature: frontend-integration-design-improvements, Property 6: 필수 필드가 누락되면 오류가 기록되고 오류 상태가 표시된다
//
// Validates: Requirements 3.4
//
// 계약을 따르는 Room/Message/응답에서 필수 필드 중 하나를 제거하면,
// 매핑/검증 로직은 (a) console.error로 오류를 기록하고,
// (b) SchemaValidationError를 던져 오류 상태를 표시해야 한다(무음 실패 금지).

import { describe, it, expect, vi, afterEach } from 'vitest';
import fc from 'fast-check';
import {
  mapRoom,
  mapMessage,
  mapRoomsResponse,
  mapMessagesResponse,
  SchemaValidationError,
} from './chatSchema';

const ROOM_REQUIRED_FIELDS = ['id', 'room_name', 'created_at'];
const MESSAGE_REQUIRED_FIELDS = ['id', 'sender_type', 'message_content', 'sent_at'];

// 계약을 완전히 만족하는 유효한 Room 생성기.
const validRoomArb = fc.record({
  id: fc.string(),
  room_name: fc.string(),
  created_at: fc.string(),
});

// 계약을 완전히 만족하는 유효한 Message 생성기(thinking은 선택 필드).
const validMessageArb = fc.record(
  {
    id: fc.integer(),
    sender_type: fc.constantFrom('user', 'assistant'),
    message_content: fc.string(),
    thinking: fc.string(),
    sent_at: fc.string(),
  },
  { requiredKeys: ['id', 'sender_type', 'message_content', 'sent_at'] }
);

// 필드를 "제거"하는 방식: 키 자체 삭제, 또는 null/undefined 할당.
// chatSchema는 undefined/null을 누락으로 간주하므로 세 경우 모두 누락이어야 한다.
function removeField(obj, field, mode) {
  const copy = { ...obj };
  if (mode === 'delete') {
    delete copy[field];
  } else if (mode === 'null') {
    copy[field] = null;
  } else {
    copy[field] = undefined;
  }
  return copy;
}

const removalModeArb = fc.constantFrom('delete', 'null', 'undefined');

// 누락 시: console.error 기록 + SchemaValidationError throw 를 동시에 검증한다.
function expectLoggedAndThrew(fn, missingField) {
  const errorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
  try {
    let thrown;
    expect(() => {
      try {
        fn();
      } catch (e) {
        thrown = e;
        throw e;
      }
    }).toThrow(SchemaValidationError);

    // (a) 오류 상태 표시: 누락 필드 정보를 포함해야 한다(무음 실패 금지).
    expect(thrown).toBeInstanceOf(SchemaValidationError);
    expect(thrown.missingFields).toContain(missingField);

    // (b) 오류 기록: console.error가 최소 1회 호출되어야 한다.
    expect(errorSpy).toHaveBeenCalled();
  } finally {
    errorSpy.mockRestore();
  }
}

describe('Property 6: 필수 필드 누락 시 오류 기록 + 오류 상태 표시', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('mapRoom: Room 필수 필드가 하나라도 누락되면 기록하고 던진다', () => {
    fc.assert(
      fc.property(
        validRoomArb,
        fc.constantFrom(...ROOM_REQUIRED_FIELDS),
        removalModeArb,
        (room, field, mode) => {
          const broken = removeField(room, field, mode);
          expectLoggedAndThrew(() => mapRoom(broken), field);
        }
      ),
      { numRuns: 100 }
    );
  });

  it('mapMessage: Message 필수 필드가 하나라도 누락되면 기록하고 던진다', () => {
    fc.assert(
      fc.property(
        validMessageArb,
        fc.constantFrom(...MESSAGE_REQUIRED_FIELDS),
        removalModeArb,
        (message, field, mode) => {
          const broken = removeField(message, field, mode);
          expectLoggedAndThrew(() => mapMessage(broken), field);
        }
      ),
      { numRuns: 100 }
    );
  });

  it('mapRoomsResponse: 배열 내 Room의 필수 필드가 누락되면 기록하고 던진다', () => {
    fc.assert(
      fc.property(
        fc.array(validRoomArb, { minLength: 1, maxLength: 5 }),
        fc.constantFrom(...ROOM_REQUIRED_FIELDS),
        removalModeArb,
        fc.nat(),
        (rooms, field, mode, idxSeed) => {
          const idx = idxSeed % rooms.length;
          const brokenRooms = rooms.map((r, i) =>
            i === idx ? removeField(r, field, mode) : r
          );
          expectLoggedAndThrew(
            () => mapRoomsResponse({ success: true, rooms: brokenRooms }),
            field
          );
        }
      ),
      { numRuns: 100 }
    );
  });

  it('mapMessagesResponse: 배열 내 Message의 필수 필드가 누락되면 기록하고 던진다', () => {
    fc.assert(
      fc.property(
        fc.array(validMessageArb, { minLength: 1, maxLength: 5 }),
        fc.constantFrom(...MESSAGE_REQUIRED_FIELDS),
        removalModeArb,
        fc.nat(),
        (messages, field, mode, idxSeed) => {
          const idx = idxSeed % messages.length;
          const brokenMessages = messages.map((m, i) =>
            i === idx ? removeField(m, field, mode) : m
          );
          expectLoggedAndThrew(
            () => mapMessagesResponse({ success: true, messages: brokenMessages }),
            field
          );
        }
      ),
      { numRuns: 100 }
    );
  });

  it('mapRoomsResponse: 최상위 rooms 필드가 누락되면 기록하고 던진다', () => {
    fc.assert(
      fc.property(removalModeArb, (mode) => {
        const response = removeField({ success: true, rooms: [] }, 'rooms', mode);
        expectLoggedAndThrew(() => mapRoomsResponse(response), 'rooms');
      }),
      { numRuns: 100 }
    );
  });

  it('mapMessagesResponse: 최상위 messages 필드가 누락되면 기록하고 던진다', () => {
    fc.assert(
      fc.property(removalModeArb, (mode) => {
        const response = removeField({ success: true, messages: [] }, 'messages', mode);
        expectLoggedAndThrew(() => mapMessagesResponse(response), 'messages');
      }),
      { numRuns: 100 }
    );
  });
});
