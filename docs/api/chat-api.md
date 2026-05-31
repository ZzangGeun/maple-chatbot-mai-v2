# 대화방 및 메시지 API 명세서 (Chat APIs)

본 문서는 사용자의 챗봇 채널 혹은 웹 대시보드에서 대화방 세션을 관리하고 메시지를 송수신하기 위한 API 스펙을 정의합니다.

* **Base URL:** `/api/v1/chat`

---

## 1. 대화방 생성 (Create Chat Room)

* **Endpoint:** `POST /rooms`
* **Headers:** `Authorization: Bearer <access_token>`

### Request Body
```json
{
  "room_name": "메이플 강화 질문방"
}
```

### Response Body (210 Created)
```json
{
  "success": true,
  "room": {
    "id": 102,
    "room_name": "메이플 강화 질문방",
    "created_at": "2026-05-31T03:10:00Z"
  }
}
```

---

## 2. 대화방 목록 조회 (Get Chat Rooms)

* **Endpoint:** `GET /rooms`
* **Headers:** `Authorization: Bearer <access_token>`

### Response Body (200 OK)
```json
{
  "success": true,
  "rooms": [
    {
      "id": 102,
      "room_name": "메이플 강화 질문방",
      "updated_at": "2026-05-31T03:15:00Z"
    },
    {
      "id": 99,
      "room_name": "기본 대화방",
      "updated_at": "2026-05-30T12:00:00Z"
    }
  ]
}
```

---

## 3. 특정 대화방 메시지 내역 조회 (Get Messages)

* **Endpoint:** `GET /rooms/{room_id}/messages`
* **Headers:** `Authorization: Bearer <access_token>`
* **Query Parameters:**
  - `limit`: (Optional) 반환할 메시지 개수 (기본값: 20)
  - `before_id`: (Optional) 커서 기반 페이지네이션용 메시지 ID

### Response Body (200 OK)
```json
{
  "success": true,
  "messages": [
    {
      "id": 5012,
      "sender_type": "user",
      "message_content": "스타포스 15성 갈 때 파괴방지 해야해?",
      "sent_at": "2026-05-31T03:14:00Z"
    },
    {
      "id": 5013,
      "sender_type": "assistant",
      "message_content": "스타포스 15성 -> 16성 강화 시 파괴 확률이 존재하므로 파괴 방지를 설정하는 것이 안전합니다. 단, 이벤트 기간 여부나 템 가격에 따라 효율이 달라질 수 있습니다.",
      "sent_at": "2026-05-31T03:14:05Z"
    }
  ]
}
```

---

## 4. 메시지 전송 및 답변 생성 (Send Message & AI Reply)

* **Endpoint:** `POST /rooms/{room_id}/messages`
* **Headers:** `Authorization: Bearer <access_token>`

### Request Body
```json
{
  "message_content": "앱솔랩스 무기 17성 강화 비용은 대략 얼마야?"
}
```

### Response Body (200 OK)
```json
{
  "success": true,
  "user_message": {
    "id": 5014,
    "sender_type": "user",
    "message_content": "앱솔랩스 무기 17성 강화 비용은 대략 얼마야?",
    "sent_at": "2026-05-31T03:15:00Z"
  },
  "assistant_message": {
    "id": 5015,
    "sender_type": "assistant",
    "message_content": "앱솔랩스 무기 17성까지의 평균 강화 비용은 1+1 이벤트가 아닐 때 약 2억 ~ 3억 메소 수준입니다 (기대값 기준). 단, 스타캐치 성공 여부 및 파괴 횟수에 따라 오차가 존재합니다.",
    "sent_at": "2026-05-31T03:15:03Z"
  }
}
```

* **비동기 스트리밍(Streaming) 지원 여부:** 대화 인터페이스에서 실시간으로 답변이 타이핑되듯 보여주는 기능(Streaming)이 필요할 경우 HTTP Server-Sent Events (SSE) 혹은 Websocket 엔드포인트 `/ws/chat/{room_id}`로 변경하여 설계해야 합니다.
