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

---

## 5. 메시지 전송 및 답변 스트리밍 (Send Message & Stream AI Reply, SSE)

웹 채팅 화면이 사용하는 엔드포인트입니다. 답변을 토큰 단위로 Server-Sent Events(SSE)로 전송합니다.

* **Endpoint:** `POST /rooms/{room_id}/stream`
* **Response Content-Type:** `text/event-stream`

### Request Body
```json
{
  "content": "스타포스 강화가 뭐야?"
}
```

### Response (SSE)
모든 이벤트는 `data: <JSON>` 한 줄과 빈 줄로 구분되며, 스트림은 항상 `data: [DONE]`으로 끝납니다.

```
data: {"type": "status", "content": "질문을 살펴보고 있어요"}

data: {"type": "route", "route": "knowledge"}

data: {"type": "status", "content": "관련 문서를 찾고 있어요"}

data: {"type": "token", "content": "스타포스 강화는 장비의 성능을"}

data: {"type": "token", "content": " 올려주는 시스템이담. [1]"}

data: {"type": "sources", "sources": [{"index": 1, "title": "스타포스 강화 안내", "url": "https://...", "category": "guide", "date": "2026-10-01"}]}

data: [DONE]
```

| type | 설명 |
| :--- | :--- |
| `status` | 진행 상태 문구 (질문 분석, 문서 검색, 캐릭터 조회, 답변 작성) |
| `route` | 질문 분류 결과: `chat` / `knowledge` / `character` / `character_knowledge` |
| `token` | 답변 텍스트 조각. 순서대로 이어 붙이면 전체 답변이 됩니다. |
| `sources` | 답변 근거 문서 목록 (지식 검색을 거친 경우에만, 답변 뒤에 1회). `index`는 답변 본문의 `[n]` 표시와 대응합니다. |
| `error` | 처리 실패. 현재 프론트엔드는 이 이벤트를 화면에 표시하지 않으므로, 서버가 안내 문구를 `token`으로도 함께 보냅니다. (안내 문구는 대화 기록에 저장되지 않습니다) |

* 사용자 메시지는 AI 응답 성공 여부와 관계없이 저장되며, 답변은 받은 내용이 있을 때만 저장됩니다.
* 메시지 목록 조회(3번)의 assistant 메시지에는 근거 문서 `sources` 배열이 함께 포함됩니다.
