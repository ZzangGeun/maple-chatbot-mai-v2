# 요구사항 문서

## 개요

이 문서는 `maple-chatbot-mai-v2` 프로젝트(Django + FastAPI 백엔드, React/Vite 프론트엔드)의 **프론트엔드-백엔드 연계 정합성** 및 **디자인/UX 개선**을 위한 요구사항을 정의한다. 사전 코드 분석에서 확인된 다음 문제들을 해결하는 것을 목표로 한다.

- 채팅 스트리밍 요청이 공용 API 클라이언트를 우회하여 인증/CSRF 헤더가 누락되는 문제
- 커뮤니티 기능이 프론트엔드 목업(mock) 상태이며, 관련 API 모듈(`community.js`)이 실제로는 호출되지 않는 죽은 코드로 존재하는 문제
- 프론트엔드-백엔드 간 API 응답 스키마 계약이 확정되지 않아 방어 코드로 임시 대응하는 문제
- 중복 정의 및 문서-코드 드리프트(예: `searchCharacter` 중복, `urls.py` docstring 불일치)
- 미구현 상태로 남아 `alert`로 처리된 UI(회원가입, 프로필 상세)
- 채팅 사이드바의 하드코딩된 가짜 프로필 데이터
- 중복된 CSS 파일 구조와 인라인 하드코딩 색상(디자인 토큰 미사용)
- 접근성(aria-label, 라벨, 모달 포커스 관리) 미비
- 라우트 코드 스플리팅·Error Boundary·보호 라우트 부재
- `index.html`의 AdSense 플레이스홀더 client id

이 스펙은 **프론트엔드 정합성과 디자인 개선**에 초점을 맞추며, 백엔드 신규 기능 구현(예: 커뮤니티 앱 신설)은 별도 결정 사항으로 다룬다. 각 요구사항은 이후 설계 단계에서 구체적 구현으로 이어진다.

## 용어 정의 (Glossary)

- **Frontend_Client**: React/Vite 기반의 클라이언트 애플리케이션 전체.
- **API_Client**: `frontend/src/api/client.js`에 정의된 axios 인스턴스. CSRF 토큰 주입 인터셉터와 `withCredentials: true`를 포함한다.
- **Chat_Stream_Module**: `frontend/src/api/chat.js`의 `streamMessage` 함수. 채팅 메시지를 SSE(Server-Sent Events)로 스트리밍한다.
- **Community_Module**: 커뮤니티 관련 프론트엔드 코드(`api/community.js`, `hooks/useCommunity.js`, `pages/CommunityPage.jsx` 등).
- **Chat_Sidebar**: `frontend/src/components/chat/ChatSidebar.jsx` 컴포넌트. 사용자 프로필과 채팅 기록을 표시한다.
- **Auth_Context**: `frontend/src/context/AuthContext.jsx`가 제공하는 인증 상태 및 사용자 정보.
- **Style_System**: 프로젝트의 CSS 자산 집합. `styles/globals`, `styles/pages`, `styles/components`의 신규 구조와 `styles/` 루트의 레거시 파일을 포함한다.
- **Design_Token**: `styles/globals/variables.css`에 정의된 CSS 커스텀 프로퍼티(색상, 간격 등).
- **Route_Manager**: `frontend/src/App.jsx`의 React Router 라우트 구성.
- **Error_Boundary**: 렌더링 중 발생한 예외를 포착하여 대체 UI를 표시하는 React 컴포넌트.
- **Protected_Route**: 로그인 여부에 따라 접근을 제어하는 라우트 래퍼 컴포넌트.
- **Schema_Contract**: 프론트엔드와 백엔드 간 합의된 API 요청/응답 필드 명세.
- **AdSense_Config**: `index.html` 및 관련 컴포넌트에 설정되는 Google AdSense client id 구성.

## 요구사항

### 요구사항 1: 채팅 스트리밍 요청의 인증/CSRF 일관성

**User Story:** 로그인한 사용자로서, 채팅 스트리밍 메시지가 일반 API 요청과 동일한 인증·CSRF 정책으로 전송되기를 원한다. 그래야 인증/CSRF가 활성화된 환경에서도 스트리밍이 정상 동작한다.

#### 승인 기준 (Acceptance Criteria)

1. WHEN Chat_Stream_Module이 스트리밍 요청을 전송하면, THE Chat_Stream_Module SHALL 쿠키에서 읽은 CSRF 토큰을 `X-CSRFToken` 요청 헤더에 포함한다.
2. WHEN Chat_Stream_Module이 스트리밍 요청을 전송하면, THE Chat_Stream_Module SHALL 자격 증명(쿠키)을 포함하여 요청을 전송한다.
3. THE Chat_Stream_Module SHALL API_Client와 동일한 방식으로 CSRF 토큰과 자격 증명 정책을 적용한다.
4. IF 스트리밍 응답의 HTTP 상태가 성공 범위(200-299)를 벗어나면, THEN THE Chat_Stream_Module SHALL 오류 콜백을 호출하고 상태 코드를 포함한 오류 정보를 전달한다.
5. WHEN 스트리밍 응답이 `[DONE]` 종료 신호를 전달하면, THE Chat_Stream_Module SHALL 완료 콜백을 정확히 한 번 호출한다.

### 요구사항 2: 커뮤니티 기능의 목업 상태 명확화 및 죽은 코드 제거

**User Story:** 개발자로서, 커뮤니티 기능이 목업 데이터로 동작함을 코드에 명확히 표기하고 호출되지 않는 죽은 코드를 제거하기를 원한다. 그래야 커뮤니티의 실제 상태가 코드에 일관되게 반영된다.

**결정:** 이번 스펙에서 커뮤니티는 목업 데이터 소스를 유지하며, 백엔드 커뮤니티 앱 신설은 범위에 포함하지 않는다. 미사용 API 모듈(`api/community.js`)은 제거한다.

#### 승인 기준 (Acceptance Criteria)

1. THE Community_Module SHALL 목업 데이터 소스를 사용함을 코드 주석으로 명시한다.
2. THE Frontend_Client SHALL 어떤 모듈에서도 호출되지 않는 `api/community.js`를 제거한다.
3. WHEN 사용자가 커뮤니티 게시글 목록을 요청하면, THE Community_Module SHALL 목업 데이터 소스로부터 게시글 목록을 반환한다.

### 요구사항 3: 채팅 API 응답 스키마 계약 확정

**User Story:** 개발자로서, 채팅 세션 및 메시지 API의 응답 필드 명세를 확정하기를 원한다. 그래야 프론트엔드가 다중 대체 필드(`||`) 방어 코드 없이 단일 계약에 따라 데이터를 처리할 수 있다.

#### 승인 기준 (Acceptance Criteria)

1. THE Schema_Contract SHALL 채팅 세션 목록 응답의 세션 배열 필드명을 단일 이름으로 정의한다.
2. THE Schema_Contract SHALL 메시지 객체의 발신자 구분 필드명과 본문 내용 필드명을 각각 단일 이름으로 정의한다.
3. WHEN Frontend_Client가 확정된 Schema_Contract를 따르는 응답을 수신하면, THE Frontend_Client SHALL 대체 필드 분기 없이 정의된 필드명으로 데이터를 읽는다.
4. IF 수신한 응답에 Schema_Contract에서 정의한 필수 필드가 없으면, THEN THE Frontend_Client SHALL 오류를 기록하고 사용자에게 오류 상태를 표시한다.

### 요구사항 4: 중복 정의 및 문서-코드 드리프트 제거

**User Story:** 개발자로서, 중복 정의된 함수와 코드와 불일치하는 문서를 정리하기를 원한다. 그래야 단일 정의 원칙이 유지되고 문서가 실제 동작을 반영한다.

#### 승인 기준 (Acceptance Criteria)

1. THE Frontend_Client SHALL `searchCharacter` 함수를 단일 모듈에서만 정의하고 다른 모듈은 해당 정의를 재사용한다.
2. THE `apps/chat/urls.py` 문서 주석 SHALL 실제 라우팅 경로(`/rooms/`)와 일치하는 설명을 포함한다.
3. WHEN 개발자가 `frontend/src/STYLES_STRUCTURE.md`를 참조하면, THE 문서 SHALL 실제 존재하는 CSS 파일 구조와 일치하는 내용을 제공한다.

### 요구사항 5: 미구현 UI의 실제 기능 연결

**User Story:** 사용자로서, 회원가입과 프로필 상세 보기가 `alert` 안내 대신 실제 기능으로 동작하기를 원한다. 그래야 안내된 기능을 실제로 사용할 수 있다.

#### 승인 기준 (Acceptance Criteria)

1. WHEN 사용자가 로그인 화면에서 회원가입을 시도하면, THE Frontend_Client SHALL 기존 SignupPopup 컴포넌트를 표시한다.
2. WHEN 사용자가 채팅 사이드바에서 프로필 상세 링크를 선택하면, THE Frontend_Client SHALL 프로필 상세 화면 또는 상세 정보 뷰로 이동한다.
3. THE Frontend_Client SHALL 기능이 연결된 UI 요소에서 `alert('구현 예정')` 형태의 임시 안내를 사용하지 않는다.

### 요구사항 6: 채팅 사이드바의 실제 프로필 데이터 표시

**User Story:** 로그인한 사용자로서, 채팅 사이드바에 내 실제 프로필 정보가 표시되기를 원한다. 그래야 고정된 가짜 데이터 대신 내 정보를 확인할 수 있다.

#### 승인 기준 (Acceptance Criteria)

1. WHILE 사용자가 로그인 상태인 동안, THE Chat_Sidebar SHALL Auth_Context가 제공하는 사용자 프로필 데이터를 표시한다.
2. IF 특정 프로필 항목(레벨, 직업, 길드, 서버) 값이 존재하지 않으면, THEN THE Chat_Sidebar SHALL 해당 항목에 대해 미설정 상태를 나타내는 대체 표시를 제공한다.
3. THE Chat_Sidebar SHALL 로그인 사용자와 무관한 고정 프로필 값(예: Lv.285, 아델, 길드 MAI, 서버 LUNA)을 하드코딩하지 않는다.
4. WHILE 사용자가 비로그인 상태인 동안, THE Chat_Sidebar SHALL 게스트 상태 표시를 제공한다.

### 요구사항 7: CSS 파일 구조 정리

**User Story:** 개발자로서, 중복된 레거시 CSS 파일을 정리하고 단일한 스타일 구조를 유지하기를 원한다. 그래야 스타일 소스가 예측 가능하고 문서와 일치한다.

#### 승인 기준 (Acceptance Criteria)

1. THE Style_System SHALL 각 페이지·컴포넌트 스타일을 단일한 위치 구조(`styles/globals`, `styles/pages`, `styles/components`)로 유지한다.
2. IF 레거시 CSS 파일(`styles/home.css`, `styles/chat.css`, `styles/character.css`, `styles/community.css`, `styles/common.css`)이 신규 구조와 중복되면, THEN THE Style_System SHALL 중복 레거시 파일을 제거하거나 신규 구조로 통합한다.
3. WHEN CSS 파일 구조가 변경되면, THE Frontend_Client SHALL 변경된 구조를 참조하도록 모든 import 경로를 갱신한다.

### 요구사항 8: 디자인 토큰 일관 적용

**User Story:** 개발자로서, 인라인으로 하드코딩된 색상 대신 디자인 토큰을 사용하기를 원한다. 그래야 색상 변경이 한 곳에서 관리되고 시각적 일관성이 유지된다.

#### 승인 기준 (Acceptance Criteria)

1. THE Frontend_Client SHALL 색상 값을 인라인 하드코딩(예: `#c62828`, `#ffb7c5`) 대신 Design_Token(CSS 변수)으로 참조한다.
2. WHERE 특정 색상 값이 Design_Token에 정의되어 있지 않은 경우, THE Style_System SHALL 해당 색상에 대응하는 Design_Token을 새로 정의한다.
3. WHEN 컴포넌트가 색상 스타일을 적용하면, THE 컴포넌트 SHALL Design_Token을 통해 색상을 참조한다.

### 요구사항 9: 접근성 기준 준수

**User Story:** 보조 기술을 사용하는 사용자로서, 아이콘 버튼·입력 요소·모달이 접근 가능하기를 원한다. 그래야 키보드와 스크린 리더로 애플리케이션을 사용할 수 있다.

#### 승인 기준 (Acceptance Criteria)

1. THE Frontend_Client SHALL 텍스트 라벨이 없는 아이콘·이모지 전용 버튼(예: `➤`, `🧠`)에 접근성 이름(`aria-label`)을 제공한다.
2. THE Frontend_Client SHALL 채팅 입력 `textarea`에 연관된 접근성 라벨을 제공한다.
3. WHILE 모달이 열려 있는 동안, THE Frontend_Client SHALL 키보드 포커스를 모달 내부로 제한(포커스 트랩)한다.
4. WHEN 사용자가 모달이 열린 상태에서 ESC 키를 누르면, THE Frontend_Client SHALL 해당 모달을 닫는다.

### 요구사항 10: 라우트 안정성 및 공통 UI 확보

**User Story:** 사용자로서, 페이지 로딩·오류·접근 제어가 일관되게 처리되기를 원한다. 그래야 오류 발생 시에도 애플리케이션이 중단되지 않고 안정적으로 동작한다.

#### 승인 기준 (Acceptance Criteria)

1. THE Route_Manager SHALL 각 페이지 컴포넌트를 코드 스플리팅(지연 로딩)으로 로드한다.
2. WHILE 지연 로딩된 페이지가 로드되는 동안, THE Frontend_Client SHALL 공통 로딩 표시 UI를 표시한다.
3. IF 페이지 렌더링 중 예외가 발생하면, THEN THE Error_Boundary SHALL 대체 오류 UI를 표시하고 애플리케이션 전체 중단을 방지한다.
4. WHEN 비로그인 사용자가 인증이 필요한 라우트에 접근하면, THE Protected_Route SHALL 사용자를 로그인 화면으로 이동시킨다.

### 요구사항 11: AdSense 구성 값 처리

**User Story:** 운영자로서, AdSense client id 플레이스홀더가 실제 값 또는 환경 구성으로 대체되기를 원한다. 그래야 잘못된 플레이스홀더가 배포되지 않는다.

#### 승인 기준 (Acceptance Criteria)

1. THE AdSense_Config SHALL client id를 플레이스홀더 문자열(`ca-pub-XXXXXXXXXXXXXXXX`) 대신 구성 가능한 값으로 관리한다.
2. IF AdSense client id가 유효한 값으로 설정되어 있지 않으면, THEN THE Frontend_Client SHALL AdSense 스크립트를 로드하지 않는다.
