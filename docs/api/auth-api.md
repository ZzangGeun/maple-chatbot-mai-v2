# 인증 및 캐릭터 연동 API 명세서 (Auth & Character APIs)

본 문서는 `maple-chatbot-mai-v2` 서비스의 사용자 인증(Signup/Login) 및 메이플스토리 캐릭터 연동 API 스펙을 정의합니다.

* **Base URL:** `/api/v1/auth`

---

## 1. 회원가입 (Signup)

* **Endpoint:** `POST /signup`
* **Content-Type:** `application/json`

### Request Body
```json
{
  "username": "mapleuser123",
  "password": "SecurePassword123!",
  "email": "user@example.com"
}
```

### Response Body (201 Created)
```json
{
  "success": true,
  "message": "회원가입이 완료되었습니다.",
  "user": {
    "id": 45,
    "username": "mapleuser123",
    "email": "user@example.com"
  }
}
```

### Error Responses
* **400 Bad Request (중복 아이디 존재 등):**
```json
{
  "success": false,
  "error_code": "DUPLICATE_USERNAME",
  "message": "이미 존재하는 아이디입니다."
}
```

---

## 2. 로그인 (Login)

* **Endpoint:** `POST /login`
* **Content-Type:** `application/json`

### Request Body
```json
{
  "username": "mapleuser123",
  "password": "SecurePassword123!"
}
```

### Response Body (200 OK)
```json
{
  "success": true,
  "access_token": "eyJhbGciOiJIUzI1NiIsIn...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5...",
  "expires_in": 3600
}
```

---

## 3. 메이플스토리 캐릭터 연동 요청 (Character Link Request)

* **Endpoint:** `POST /character/link`
* **Headers:** `Authorization: Bearer <access_token>`

### Request Body
```json
{
  "character_name": "아델은최강"
}
```

### Response Body (200 OK)
```json
{
  "success": true,
  "verification_code": "MAI-9824",
  "message": "캐릭터 인증 코드 발급 완료. 인게임 캐릭터 소개글에 위 인증 코드를 삽입한 후 /verify 엔드포인트를 호출하세요."
}
```

---

## 4. 메이플스토리 캐릭터 인증 확인 (Character Verification Confirm)

* **Endpoint:** `POST /character/verify`
* **Headers:** `Authorization: Bearer <access_token>`

### Request Body
```json
{
  "character_name": "아델은최강",
  "verification_code": "MAI-9824"
}
```

### Response Body (200 OK)
```json
{
  "success": true,
  "message": "캐릭터 본인 인증이 성공적으로 완료되었습니다.",
  "character": {
    "character_name": "아델은최강",
    "world_name": "루나",
    "ocid": "cf64a856fdbdfd...",
    "is_main": true
  }
}
```

### Error Responses
* **400 Bad Request (인증 코드 불일치):**
```json
{
  "success": false,
  "error_code": "VERIFICATION_FAILED",
  "message": "인게임 소개글에서 인증 코드를 확인할 수 없거나 일치하지 않습니다."
}
```
