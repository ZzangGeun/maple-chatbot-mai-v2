# API 명세 (API Specification)

본 프로젝트는 Django 기반의 RESTful API를 제공합니다. 모든 응답은 `common/schemas/response.py`에 정의된 규격을 따릅니다.

## 공통 응답 구조 (Common Response)
```json
{
  "success": true,
  "data": { ... },
  "error": null
}
```
실패 시 `success: false` 이며, `error` 객체 안에 `code`와 `message`가 포함됩니다.

---

## 1. 계정 및 인증 (auth)

### `POST /api/v1/auth/signup/`
- **역할**: 새로운 사용자 가입 및 메이플스토리 닉네임 연동.
- **Request Body**: `username`, `password`, `maple_nickname`, `nexon_api_key` (옵션)
- **Response**: 가입된 유저 프로필 정보.

### `POST /api/v1/auth/login/`
- **역할**: 사용자 로그인 및 세션 생성.
- **Response**: 로그인 성공 메시지 및 세션 쿠키 발급.

---

## 2. 채팅 (Chat)

### `GET /api/v1/chat/sessions/`
- **역할**: 현재 로그인한 유저의 대화방(Session) 목록 조회.
- **Response**: 세션 ID, 생성일, 타이틀 목록.

### `POST /api/v1/chat/sessions/create/`
- **역할**: 새로운 빈 대화방(Session) 생성.
- **Response**: 생성된 세션 ID.

### `POST /api/v1/chat/sessions/<session_id>/stream/`
- **역할**: AI 서버에 메시지를 전달하고 **SSE(Server-Sent Events)**로 답변을 스트리밍 수신.
- **Response (SSE)**: `data: {"type": "token", "content": "..."}` 의 스트림 연속. 종료 시 `[DONE]`.

---

## 3. 캐릭터 정보 (Character)

### `GET /api/v1/character/search/?name={캐릭터명}`
- **역할**: 넥슨 Open API를 호출하여 캐릭터의 종합 정보(스탯, 장비, 유니온 등)를 가져옵니다.
- **Response**: 넥슨 API에서 추출 및 가공된 캐릭터 종합 정보.

---

## 4. 코어 (Core)

### `GET /api/v1/core/home/data/`
- **역할**: 홈 화면 구성에 필요한 배너, 랭킹 요약, 최신 공지사항 등을 한 번에 가져옵니다.
- **Response**: 홈 화면 구성용 종합 JSON 객체.
