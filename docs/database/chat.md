# 대화 및 로그 스키마 설계서 (Chat & Logs)

본 문서는 사용자의 챗봇 대화 기록을 관리하는 `ChatRoom`, `ChatMessage` 테이블 및 API 남용 방지를 위한 `ApiCallLog` 테이블 스펙을 정의합니다.

## 1. 물리 테이블 명세

### 1) `chat_room` 테이블 (대화 세션)

사용자별로 격리된 대화 세션(채널 또는 대화방)을 나타냅니다.

| 컬럼명 | 데이터 타입 | Nullable | Key | 기본값 | 설명 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | BIGINT | N | PK | Auto | 대화방 일련번호 |
| `user_id` | BIGINT | N | FK | - | `auth_user.id` 참조 (비회원 질문 시 Nullable 설정 가능) |
| `room_name` | VARCHAR(100) | N | - | '새 대화' | 대화방의 메타 이름 |
| `created_at` | TIMESTAMP | N | - | CURRENT_TIMESTAMP | 생성 시간 |
| `updated_at` | TIMESTAMP | N | - | CURRENT_TIMESTAMP | 최종 대화 발생 시간 |

---

### 2) `chat_message` 테이블 (대화 메시지 내역)

사용자와 챗봇이 주고받은 텍스트 데이터가 저장되는 핵심 테이블입니다.

| 컬럼명 | 데이터 타입 | Nullable | Key | 기본값 | 설명 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | BIGINT | N | PK | Auto | 메시지 일련번호 |
| `chat_room_id` | BIGINT | N | FK | - | `chat_room.id` 참조 |
| `sender_type` | VARCHAR(10) | N | - | - | 송신자 구분 ('user' 또는 'assistant') |
| `message_content` | TEXT | N | - | - | 대화 텍스트 내용 |
| `sent_at` | TIMESTAMP | N | - | CURRENT_TIMESTAMP | 전송 시간 |

* **대화 세션 윈도우(Memory Window):** LLM 호출 시 이전 대화 내역(Context)을 전달하기 위해, 해당 테이블에서 최근 N개의 대화(예: `sender_type`에 따른 최근 10개 메시지)를 조회하여 프롬프트 빌더로 인가합니다.

---

### 3) `api_call_log` 테이블 (API 트래픽 및 Rate Limit 트래킹)

넥슨 Open API 호출 이력 및 챗봇 AI 요청 빈도를 제어하기 위해 기록하는 트래픽 로그 테이블입니다.

| 컬럼명 | 데이터 타입 | Nullable | Key | 기본값 | 설명 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | BIGINT | N | PK | Auto | 로그 일련번호 |
| `user_id` | BIGINT | Y | FK | NULL | `auth_user.id` 참조 (비로그인 사용자 트래킹용) |
| `api_name` | VARCHAR(50) | N | - | - | 호출 대상 명칭 (예: `nexon_character_stat`, `openai_completion`) |
| `status_code` | INT | N | - | - | HTTP 응답 상태 코드 (200, 429, 500 등) |
| `ip_address` | VARCHAR(45) | Y | - | - | 클라이언트 IP (IPv4 & IPv6 대응) |
| `called_at` | TIMESTAMP | N | - | CURRENT_TIMESTAMP | 호출 시간 |

---

## 2. API Rate Limit 및 모니터링 설계 의도

1. **넥슨 Open API 호출 제한 대응**
   * 넥슨 Open API는 API 키당 초당/분당 호출 제한이 존재합니다.
   * `ApiCallLog` 테이블은 최근 1분 이내 특정 유저 혹은 IP가 유발한 API 호출 수를 실시간으로 계산하는 기준이 됩니다.
   * 실시간성이 중요한 차단 메커니즘은 **Redis**에 우선 기록하여 처리하고, 사후 분석 및 통계 산출을 위해 `ApiCallLog` DB 테이블에 비동기(Celery Task 등)로 저장할 것을 추천합니다.

2. **메시지 히스토리 압축**
   * 대화가 길어질 경우 RDB에서 매번 많은 텍스트 데이터를 로드하는 것은 성능 저하를 야기합니다.
   * 향후 대화방이 비활성화되거나 30일이 경과한 데이터는 배치(Batch) 스케줄러를 통해 콜드 스토리지(Cold Storage)로 이관하거나 압축 및 백업하는 정책을 수립해야 합니다.
