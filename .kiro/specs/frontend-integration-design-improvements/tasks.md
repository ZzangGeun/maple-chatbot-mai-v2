# Implementation Plan: 프론트엔드-백엔드 연계 정합성 및 디자인/UX 개선

## Overview

이 계획은 설계 문서를 실제 코드 변경으로 옮기기 위한 점진적 작업 목록이다. 각 작업은 이전 작업 위에 쌓이며, 마지막에는 `App.jsx` 재구성으로 모든 공통 컴포넌트를 하나로 연결한다. 스택은 React + Vite(JavaScript)이며, 속성 기반 테스트(PBT)는 **Vitest + fast-check**, 렌더/상호작용 테스트는 **@testing-library/react**를 사용한다.

각 속성 테스트에는 다음 형식의 태그를 단다.
`// Feature: frontend-integration-design-improvements, Property {번호}: {속성 텍스트}`

## Tasks

- [x] 1. 테스트 인프라 및 스키마 계약 기반 마련
  - [x] 1.1 Vitest + fast-check + @testing-library/react 설정
    - `frontend/`에 Vitest 설정(`vitest.config.js` 또는 `vite.config.js`의 test 섹션), jsdom 환경, `@testing-library/react`/`@testing-library/jest-dom`/`fast-check` 의존성 추가
    - 테스트 setup 파일 작성(jest-dom matcher 등록)
    - _Requirements: 1.1, 3.1_

  - [x] 1.2 채팅 스키마 매핑/검증 모듈 작성
    - `frontend/src/api/chatSchema.js` 신설: 계약 필드(`rooms`/`room`/`messages`, Room `{id, room_name, created_at}`, Message `{id, sender_type, message_content, thinking?, sent_at}`)를 UI 모델(`role`/`content`/`thinking`)로 매핑하는 순수 함수 `mapRoom`, `mapMessage`, `mapRoomsResponse`, `mapMessagesResponse` 구현
    - 필수 필드 누락 시 `console.error` 기록 후 오류를 던지거나 오류 상태 반환(무음 실패 금지)
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

  - [x] 1.3 스키마 매핑 함수 속성 테스트
    - **Property 5: 계약을 따르는 응답은 정의된 단일 필드로 매핑된다**
    - **Validates: Requirements 3.1, 3.2, 3.3**

  - [x] 1.4 필수 필드 누락 처리 속성 테스트
    - **Property 6: 필수 필드가 누락되면 오류가 기록되고 오류 상태가 표시된다**
    - **Validates: Requirements 3.4**

- [ ] 2. 채팅 스트리밍 정합화 (Chat_Stream_Module)
  - [x] 2.1 `streamMessage`를 공용 CSRF/자격 증명 정책으로 정합화
    - `frontend/src/api/chat.js`의 `streamMessage`가 `client.js`의 `getCookie('csrftoken')`를 재사용하여 `X-CSRFToken` 헤더 주입, `credentials: 'include'` 설정
    - 응답이 200–299 범위를 벗어나면 상태 코드를 포함한 오류 객체로 `onError` 호출하고 `onDone` 미호출
    - `doneCalled` 가드로 `[DONE]` 수신/스트림 종료 시 `onDone`을 정확히 1회 호출
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

  - [~] 2.2 SSE 파서를 계약에 맞게 정리
    - `\n\n` 구분자로 이벤트 분리, 미완성 조각 버퍼 유지, `data: ` 접두사 없는 라인 무시, JSON 파싱 실패 조각은 경고 로깅 후 건너뛰기
    - `{"type":"token"}` → `onChunk`, `{"type":"error"}` → 오류 분기 로깅, `[DONE]` → 완료 처리
    - _Requirements: 1.5_

  - [~] 2.3 CSRF/자격 증명 속성 테스트
    - **Property 1: 스트리밍 요청은 쿠키의 CSRF 토큰을 헤더로 전송한다**
    - **Validates: Requirements 1.1, 1.2, 1.3**

  - [~] 2.4 비2xx 오류 처리 속성 테스트
    - **Property 2: 성공 범위를 벗어난 응답은 상태 코드와 함께 오류 콜백을 부른다**
    - **Validates: Requirements 1.4**

  - [~] 2.5 완료 콜백 1회 보장 속성 테스트
    - **Property 3: 종료 신호 수신 시 완료 콜백은 정확히 한 번 호출된다**
    - **Validates: Requirements 1.5**

- [ ] 3. 프론트엔드 스키마 계약 적용 및 방어 코드 제거
  - [~] 3.1 `useChat` 및 세션/메시지 소비 코드에서 대체 필드 분기 제거
    - `frontend/src/hooks/useChat.js`와 `frontend/src/api/chat.js`의 `response.data.rooms || response.data.data`, `msg.sender_type || msg.role`, `msg.message_content || msg.content`, `session.created_at || session.updated_at` 등을 1.2의 매핑 함수 호출로 대체
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

  - [x] 3.2 백엔드 세션 타임스탬프 필드 단일화
    - `apps/chat/services.py`(또는 해당 뷰)의 `get_sessions` 응답이 `updated_at` 대신 `created_at` 필드명으로 값을 반환하도록 수정하여 `create_session`과 계약 일치
    - _Requirements: 3.1, 3.3_

- [x] 4. 커뮤니티 목업 명시 및 죽은 코드 제거 (Community_Module)
  - [x] 4.1 커뮤니티 목업 상태 주석 명시 및 `api/community.js` 제거
    - `frontend/src/hooks/useCommunity.js`, `frontend/src/pages/CommunityPage.jsx` 상단에 목업 데이터 소스 사용 주석 추가
    - 어떤 모듈에서도 import되지 않는 `frontend/src/api/community.js` 삭제
    - _Requirements: 2.1, 2.2_

  - [x] 4.2 커뮤니티 목업 필터/정렬 속성 테스트
    - **Property 4: 커뮤니티 목업 목록은 필터·정렬 계약을 만족한다**
    - **Validates: Requirements 2.3**

- [x] 5. 중복 정의 및 문서-코드 드리프트 정리
  - [x] 5.1 `searchCharacter` 단일 정의화
    - `frontend/src/api/character.js`를 정본으로 두고 `frontend/src/api/home.js`의 중복 정의 제거(또는 재-export), `frontend/src/hooks/useCharacterSearch.js`가 `characterApi.searchCharacter`를 사용하도록 갱신
    - _Requirements: 4.1_

  - [x] 5.2 `urls.py` docstring 갱신
    - `apps/chat/urls.py`의 docstring을 실제 `/rooms/` 라우팅에 맞게 수정
    - _Requirements: 4.2_

- [x] 6. 미구현 UI 실제 기능 연결
  - [x] 6.1 회원가입 진입점을 SignupPopup으로 연결
    - `frontend/src/pages/LoginPage.jsx`/LoginPopup의 회원가입 진입점이 `AuthContext.openSignupModal()`을 호출하여 기존 `SignupPopup`을 표시하도록 연결, 관련 `alert('구현 예정')` 제거
    - _Requirements: 5.1, 5.3_

  - [x] 6.2 프로필 상세 네비게이션 연결
    - `frontend/src/components/chat/ChatSidebar.jsx`의 `alert('상세 정보 기능 구현 예정')`을 실제 프로필 상세 뷰/라우트 네비게이션으로 대체
    - _Requirements: 5.2, 5.3_

- [ ] 7. 채팅 사이드바 실제 프로필 표시 (Chat_Sidebar)
  - [x] 7.1 하드코딩 프로필을 Auth_Context 데이터로 교체
    - `frontend/src/components/chat/ChatSidebar.jsx`에서 `Lv.285/아델/MAI/LUNA` 하드코딩 제거, `AuthContext.user`의 필드로 프로필 항목 렌더
    - 값이 없는(null/undefined/'') 항목은 `미설정` 대체 표시, 비로그인 시 게스트 상태 표시
    - 프로필 필드 표시를 순수 헬퍼(예: `resolveProfileField(value)`)로 분리하여 테스트 가능하게 함
    - _Requirements: 6.1, 6.2, 6.3, 6.4_

  - [~] 7.2 프로필 대체 표시 속성 테스트
    - **Property 7: 부재한 프로필 항목은 대체 표시로 렌더된다**
    - **Validates: Requirements 6.2**

- [ ] 8. 접근성 개선 (aria-label, 라벨, 모달 처리)
  - [x] 8.1 아이콘 버튼 및 채팅 입력 접근성 이름 부여
    - 이모지/아이콘 전용 버튼(`➤` 전송, `🧠` 사고 등)에 `aria-label` 추가, 채팅 입력 `textarea`에 연관 라벨(`aria-label` 또는 시각적 숨김 `<label htmlFor>`) 부여
    - _Requirements: 9.1, 9.2_

  - [x] 8.2 공통 모달 접근성 훅 `useModalA11y` 구현 및 적용
    - `frontend/src/hooks/useModalA11y.js` 신설: 포커스 트랩(첫/마지막 포커서블 간 Tab 순환), `Escape` 시 `onClose`, 열림 시 첫 포커서블 포커스/닫힘 시 트리거 복귀
    - Login/Signup Popup, CommunityWriteModal 등 모달에 적용
    - _Requirements: 9.3, 9.4_

  - [~] 8.3 모달 포커스 트랩 속성 테스트
    - **Property 8: 모달은 열려 있는 동안 포커스를 내부에 가둔다**
    - **Validates: Requirements 9.3**

- [~] 9. Checkpoint - 여기까지의 테스트 통과 확인
  - Ensure all tests pass, ask the user if questions arise.

- [x] 10. AdSense 구성화 (AdSense_Config)
  - [x] 10.1 유효성 헬퍼 및 조건부 로딩 구현
    - `isValidAdSenseClientId(id)` 헬퍼 구현(비어있지 않고 `ca-pub-` + 실제 숫자열, 플레이스홀더 `X` 아님)
    - `frontend/index.html`의 하드코딩 AdSense 스크립트(`ca-pub-XXXXXXXXXXXXXXXX`) 제거, `frontend/src/components/common/AdSense.jsx`가 `import.meta.env.VITE_ADSENSE_CLIENT_ID`를 `isValidAdSenseClientId`로 검사해 유효할 때만 스크립트/광고 로드
    - _Requirements: 11.1, 11.2_

  - [x] 10.2 AdSense 유효성 속성 테스트
    - **Property 10: AdSense는 유효한 client id일 때만 로드된다**
    - **Validates: Requirements 11.1, 11.2**

- [ ] 11. 공통 라우팅/UI 컴포넌트 구현
  - [x] 11.1 LoadingFallback 및 ErrorBoundary 구현
    - `frontend/src/components/common/LoadingFallback.jsx`(Suspense/페이지 로딩 표시), `frontend/src/components/common/ErrorBoundary.jsx`(`getDerivedStateFromError`/`componentDidCatch`로 대체 UI) 구현
    - _Requirements: 10.2, 10.3_

  - [x] 11.2 ProtectedRoute 구현
    - `frontend/src/components/common/ProtectedRoute.jsx` 신설: `AuthContext`의 `isLoading` 동안 `LoadingFallback` 표시, 로딩 종료 후 비로그인 시 `<Navigate to="/login" replace />`, 로그인 시 자식 렌더
    - _Requirements: 10.4_

  - [~] 11.3 ProtectedRoute 속성 테스트
    - **Property 9: 비로그인 사용자는 보호 라우트에서 로그인으로 이동한다**
    - **Validates: Requirements 10.4**

- [ ] 12. CSS 구조 정리 및 디자인 토큰 적용
  - [-] 12.1 레거시 CSS 통합 및 import 경로 갱신
    - 루트 레거시 파일(`styles/home.css`, `chat.css`, `character.css`, `community.css`, `common.css`) 중 신규 구조(`styles/globals`, `styles/pages`, `styles/components`)와 중복되는 것을 제거/통합하고 모든 import 경로를 신규 구조로 갱신
    - _Requirements: 7.1, 7.2, 7.3_

  - [~] 12.2 인라인 하드코딩 색상을 디자인 토큰으로 치환
    - 인라인/JSX `style` 하드코딩 색상(예: `#c62828`, `#ffb7c5`)을 `styles/globals/variables.css`의 CSS 변수(`var(--...)`)로 치환, 토큰에 없는 색은 새 토큰 정의
    - _Requirements: 8.1, 8.2, 8.3_

  - [x] 12.3 STYLES_STRUCTURE.md 갱신
    - `frontend/src/STYLES_STRUCTURE.md`를 최종 CSS 파일 구조와 일치하도록 갱신
    - _Requirements: 4.3_

- [ ] 13. App.jsx 재구성 및 전체 연결
  - [~] 13.1 페이지 lazy 로딩 + Suspense + ErrorBoundary + ProtectedRoute 통합
    - `frontend/src/App.jsx`에서 각 페이지를 `React.lazy`로 로드, `ErrorBoundary`로 감싼 `Suspense`(fallback=`LoadingFallback`) 안에 `Routes` 구성, 인증 전제 라우트에 `ProtectedRoute` 적용
    - _Requirements: 10.1, 10.2, 10.3, 10.4_

  - [~] 13.2 라우팅/공통 UI 통합 렌더 테스트
    - lazy 로딩 중 LoadingFallback 표시, 렌더 예외 시 ErrorBoundary 대체 UI 표시, 비로그인 보호 라우트 리다이렉트 예시 검증
    - _Requirements: 10.1, 10.2, 10.3, 10.4_

- [~] 14. 최종 Checkpoint - 전체 테스트 및 빌드 확인
  - Ensure all tests pass, ask the user if questions arise. Vite 빌드로 import 경로/CSS 구조 회귀를 검증한다.

## Notes

- `*`로 표시된 작업은 선택 사항(테스트)이며 빠른 MVP를 위해 건너뛸 수 있다.
- 각 작업은 추적성을 위해 특정 요구사항을 참조한다.
- Checkpoint는 점진적 검증을 보장한다.
- 속성 테스트는 설계의 정확성 속성을 검증하고, 단위/예시 테스트는 특정 예시·엣지 케이스를 검증한다.
- CSS 구조(요구사항 7, 8), 문서 드리프트(요구사항 4.2, 4.3), 목업 주석(요구사항 2.1), 죽은 코드 제거(요구사항 2.2)는 PBT 대상이 아니며 코드 리뷰·린트·빌드·스냅샷으로 검증한다.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2", "3.2", "4.1", "5.1", "5.2", "8.1", "10.1", "11.1", "12.3"] },
    { "id": 1, "tasks": ["1.3", "1.4", "2.1", "4.2", "6.1", "6.2", "7.1", "8.2", "10.2", "11.2", "12.1", "12.2"] },
    { "id": 2, "tasks": ["2.2", "3.1", "7.2", "8.3", "11.3", "13.1"] },
    { "id": 3, "tasks": ["2.3", "2.4", "2.5", "13.2"] }
  ]
}
```
