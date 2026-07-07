# 프론트엔드 스타일 구조 가이드

이 문서는 `frontend/src/styles/`의 **실제 현재 CSS 파일 구조**를 설명합니다.

> ⚠️ **현재 상태 안내**: 신규 구조(`globals`, `pages`, `components`)로의 이전이 진행되었으나,
> 일부 레거시 루트 CSS 파일이 아직 물리적으로 남아 있습니다. 이 문서는 그 실제 상태를
> 있는 그대로 기록합니다. 레거시 파일 통합/제거는 별도 작업(레거시 CSS 통합)에서 처리됩니다.

## 📁 실제 폴더 구조

```
styles/
├── globals/                    # 전역 스타일
│   ├── variables.css           # 색상, 그림자, 테마 변수 (Design Token)
│   ├── reset.css               # 초기화 스타일, 유틸리티 클래스
│   └── common.css              # Header, Nav, Layout 등 공통 스타일
│                               #   (variables.css, reset.css를 @import)
│
├── components/                 # 컴포넌트별 스타일
│   ├── auth.css                # 인증 관련 (Login, Signup 팝업)
│   └── common.css              # (현재 import되는 곳 없음 — 미사용)
│
├── pages/                      # 페이지별 스타일
│   ├── home.css                # 홈 페이지 스타일
│   ├── chat.css                # 채팅 페이지 스타일
│   ├── character.css           # 캐릭터 페이지 스타일
│   └── community.css           # 커뮤니티 페이지 스타일
│
└── (레거시 루트 파일 — 아직 존재)
    ├── common.css              # ⚠️ Navigation.jsx에서 여전히 import 중
    ├── home.css                # 🗑️ 미사용 (import되는 곳 없음)
    ├── chat.css                # 🗑️ 미사용 (import되는 곳 없음)
    ├── character.css           # 🗑️ 미사용 (import되는 곳 없음)
    └── community.css           # 🗑️ 미사용 (import되는 곳 없음)
```

### 범례
- `⚠️` : 레거시 파일이지만 아직 import되어 사용 중 → 통합 시 참조 경로 교체 필요
- `🗑️` : 어디에서도 import되지 않는 고아(orphan) 파일 → 통합 작업에서 제거 대상

## 🎨 CSS 파일별 내용

### globals/variables.css
CSS 커스텀 속성으로 테마 색상, 그림자, 테두리 반경 등 정의 (Design Token).
```css
:root {
    --primary-color: #ff9800;
    --text-primary: #1a1a1a;
    --shadow-medium: 0 4px 15px rgba(255, 152, 0, 0.1);
    /* ... */
}
```

### globals/reset.css
- 모든 요소 리셋 (margin, padding, box-sizing)
- 기본 타이포그래피
- 유틸리티 클래스 (.flex, .gap-small, .text-center 등)

### globals/common.css
- 파일 상단에서 `@import './variables.css';` 와 `@import './reset.css';` 로 전역 자산을 로드
- Header, Navigation 스타일
- Main Container, Sidebar 레이아웃
- 버튼, 카드 기본 스타일
- 반응형 디자인

### components/auth.css
- Login/Signup 팝업 스타일
- 인증 관련 모달 및 폼

### components/common.css
- 현재 어떤 모듈에서도 import되지 않음 (미사용)

### pages/home.css
- 홈 페이지 배너, 검색창, 섹션 카드, 랭킹, 공지사항, 광고 배너

### pages/chat.css
- 채팅 메인 컨테이너, 메시지(user/bot), 입력창, 사고 과정 표시, Markdown 렌더링

### pages/character.css
- 캐릭터 정보 컨테이너, 탭 네비게이션, 장비 그리드, 통계 표시

### pages/community.css
- 게시물 리스트, 카테고리 탭, 글쓰기 모달, 검색 및 정렬

### 레거시 루트 파일
- `styles/common.css` — Navigation.jsx가 아직 참조하는 공통 스타일. 통합 시 참조 경로 교체 후 제거 예정.
- `styles/home.css`, `styles/chat.css`, `styles/character.css`, `styles/community.css` — 신규 `pages/`
  구조로 대체되었으며 현재 어디에서도 import되지 않는 고아 파일.

## � 실제 Import 현황

| 파일 | import하는 CSS |
| --- | --- |
| `main.jsx` | `./styles/globals/common.css` |
| `pages/HomePage.jsx` | `../styles/pages/home.css` |
| `pages/ChatPage.jsx` | `../styles/pages/chat.css` |
| `pages/CharacterPage.jsx` | `../styles/pages/character.css`, `../styles/globals/common.css` |
| `pages/CommunityPage.jsx` | `../styles/pages/community.css` |
| `pages/LoginPage.jsx` | `../styles/globals/common.css` |
| `components/common/Header.jsx` | `../../styles/globals/common.css` |
| `components/common/Layout.jsx` | `../../styles/globals/common.css` |
| `components/common/Navigation.jsx` | `../../styles/common.css`  ⚠️ (레거시 루트) |
| `components/auth/LoginPopup.jsx` | `../../styles/components/auth.css` |
| `components/auth/SignupPopup.jsx` | `../../styles/components/auth.css` |

> 참고: `main.jsx`가 `globals/common.css`를 전역 로드하므로, 이 파일은 `@import`를 통해
> `variables.css`(Design Token)와 `reset.css`를 모든 페이지에 전파합니다.

## 🚀 사용 팁

### 새 스타일 추가 시
1. **전역 스타일**: `styles/globals/` (색상 토큰, reset 등)
2. **컴포넌트 스타일**: `styles/components/` (재사용 가능한 컴포넌트)
3. **페이지 스타일**: `styles/pages/` (특정 페이지만 필요)

### 색상 변경
모든 색상은 `globals/variables.css`에서 관리합니다:
```css
/* 지양 */
background: #ff9800;

/* 권장 */
background: var(--primary-color);
```

## 🔍 정리(통합) 예정 항목

레거시 CSS 통합 작업에서 다음을 처리합니다:
- `styles/common.css` → 내용 통합 후 `Navigation.jsx` import 경로를 신규 구조로 교체하고 제거
- `styles/home.css`, `styles/chat.css`, `styles/character.css`, `styles/community.css` → 고아 파일 제거
- `styles/components/common.css` → 사용처 확인 후 미사용이면 제거

---

**최종 갱신**: 실제 파일 구조 반영 (Requirement 4.3)
