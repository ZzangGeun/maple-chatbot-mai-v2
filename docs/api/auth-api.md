# 인증 API 명세서 (Auth APIs)

본 문서는 `maple-chatbot-mai-v2` 서비스의 사용자 인증(회원가입/로그인/로그아웃/내 정보 조회) API 스펙을 정의합니다. 본 API는 Django의 **세션 기반 인증**을 사용합니다.

* **Base URL:** `http://127.0.0.1:8000/api/v1/auth`

---

## 1. 회원가입 (Signup)

* **Endpoint:** `POST /signup/`
* **Content-Type:** `application/json`

### Request Body (JSON)
```json
{
  "username": "testuser123",
  "password": "testpass123",
  "confirm_password": "testpass123",
  "maple_nickname": "테스트캐릭",
  "nexon_api_key": "test_c3a1c9dd9898748983795717d4054a737fc120e7a3a13c44c825904cd7953ea7efe8d04e6d233bd35cf2fabdeb93fb0d"
}
```
* **아이디 규칙:** 6~20자의 영문자, 숫자, 밑줄(_)만 가능
* **비밀번호 규칙:** 최소 8자 이상, `confirm_password`와 완전히 일치해야 함

### Response Body

#### 성공 (201 Created)
```json
{
  "message": "회원가입이 완료되었습니다.",
  "username": "testuser123",
  "maple_nickname": "테스트캐릭"
}
```

#### 실패 (400 Bad Request - 유효성 검사 실패 등)
```json
{
  "detail": "비밀번호는 최소 8자 이상이어야 합니다."
}
```
또는
```json
{
  "detail": "이미 존재하는 아이디입니다."
}
```

---

## 2. 로그인 (Login)

* **Endpoint:** `POST /login/`
* **Content-Type:** `application/json`
* **참고:** 로그인 성공 시 응답 헤더의 `Set-Cookie`를 통해 세션 쿠키(`sessionid`)가 브라우저 및 Postman에 저장됩니다. 이후 요청 시 Postman이 자동으로 해당 쿠키를 동봉하여 전송합니다.

### Request Body (JSON)
```json
{
  "username": "testuser123",
  "password": "testpass123"
}
```

### Response Body

#### 성공 (200 OK)
```json
{
  "message": "testuser123님, 환영합니다!",
  "user": {
    "id": 1,
    "username": "testuser123",
    "email": ""
  },
  "maple_nickname": "테스트캐릭"
}
```

#### 실패 (401 Unauthorized - 아이디 없음)
```json
{
  "detail": "존재하지 않는 아이디입니다."
}
```

#### 실패 (401 Unauthorized - 비밀번호 불일치)
```json
{
  "detail": "비밀번호가 일치하지 않습니다."
}
```

---

## 3. 로그아웃 (Logout)

* **Endpoint:** `POST /logout/`
* **참고:** 세션 인증이 필요하므로, 로그인이 완료된 Postman 세션에서 호출해야 합니다.

### Request Body
없음 (비어있음)

### Response Body

#### 성공 (200 OK)
```json
{
  "message": "로그아웃되었습니다."
}
```

#### 실패 (401 Unauthorized - 로그인하지 않은 상태)
```json
{
  "detail": "로그인 상태가 아닙니다."
}
```

---

## 4. 내 정보 조회 (User Info)

* **Endpoint:** `GET /user/`
* **참고:** 세션 인증이 필요합니다. 로그인된 사용자 본인의 정보를 반환합니다.

### Request Body
없음

### Response Body

#### 성공 (200 OK)
```json
{
  "id": 1,
  "username": "testuser123",
  "email": "",
  "profile": {
    "maple_nickname": "테스트캐릭"
  }
}
```

#### 실패 (401 Unauthorized - 로그인 정보 없음)
```json
{
  "detail": "로그인이 필요합니다."
}
```

---

## 💡 Postman 테스트 팁

1. **세션 유지:** Postman은 로그인(`POST /login/`) 시 반환받은 `sessionid` 쿠키를 자동으로 저장하고, 동일한 도메인의 다음 요청(`GET /user/`, `POST /logout/`)에 자동으로 쿠키 헤더를 담아 보냅니다. 별도로 Bearer Token 설정을 하실 필요가 없습니다.
2. **CSRF 데코레이터:** 현재 `signup/`, `login/`, `logout/` 엔드포인트에는 `@csrf_exempt` 데코레이터가 설정되어 있어, CSRF 토큰 없이도 편리하게 Postman으로 POST 테스트를 진행하실 수 있습니다.
