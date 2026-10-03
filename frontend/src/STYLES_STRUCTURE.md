# 프론트엔드 스타일 구조 가이드

메이플 모험 노트를 닮은 크림 배경, 오렌지 포인트와 초록 카드로 구성합니다.
작은 숲·버섯 일러스트는 SVG와 CSS로 표현하여 외부 이미지 요청 없이 표시합니다.

## 스타일 구조

- `styles/globals/variables.css`: 색상, 그림자, 모서리, 전환 속도 토큰
- `styles/globals/reset.css`: 글꼴, 기본 요소, 포커스 표시, 유틸리티, 모션 감소
- `styles/globals/common.css`: 로고, 메뉴, 공통 레이아웃, 버튼, 카드, 푸터
- `styles/components/auth.css`: 로그인 페이지와 로그인·회원가입 모달
- `styles/pages/home.css`: 모험 배너, 질문 입력, 캐릭터 조회, 가이드, 소식 카드
- `styles/pages/chat.css`: 대화 목록, 버섯 가이드, 메시지, 입력창, 오류, 모바일 서랍
- `styles/pages/character.css`: 캐릭터 도감과 프로필, 스탯·장비·상세 탭
- `styles/pages/community.css`: 길드 게시판, 검색·정렬, 게시글, 작성 모달
- `styles/components/common.css`: 기존 LoadingFallback·ErrorBoundary의 보조 스타일

전역 스타일은 `main.jsx`에서 로드합니다. 각 페이지는 해당 CSS만 가져옵니다.
캐릭터·커뮤니티 스타일은 페이지 루트 아래로 범위를 제한해 다른 화면과의 충돌을 막습니다.

## 공통 규칙

- 색상·카드 형태를 조정할 때는 먼저 `variables.css`의 토큰을 확인합니다.
- 흰 글자 버튼에는 충분히 진한 `--primary-dark`를 사용합니다.
- `Layout`이 본문 `main`과 건너뛰기 링크를 제공하므로 페이지에서 `main`을 중첩하지 않습니다.
- 사이드바 없는 내부 화면은 `layoutClass="narrow-layout"`으로 최대 너비와 여백을 적용합니다.
- 기능이 있는 항목은 `button`, 경로 이동은 `Link`, 외부 공지는 `a`를 사용합니다.
- 입력에는 라벨을 제공하고 한글 조합 중 Enter 전송을 차단합니다.
- 모달은 `useModalA11y`로 Escape, 포커스 순환과 복귀를 처리합니다.
- 실패한 요청은 오류·재시도를 표시하고 빈 목록과 구분합니다.
- 로그인 확인이 끝나야 채팅방을 초기화합니다. 전송 중에는 세션 변경을 차단합니다.

## 개발과 검증

`frontend` 디렉터리에서 실행합니다.

```powershell
npm run dev
npm test
npm run build
```

개발 주소는 `http://localhost:5173`이며 `/api` 요청은 Django의 8000번 포트로 전달합니다.
AI 대화·캐릭터 조회·로그인 등 실제 데이터 기능에는 해당 백엔드와 인프라가 필요합니다.
빌드 결과는 `static/dist`에 생성되어 Django가 사용하므로 배포 전 다시 빌드합니다.

기존 ESLint 설정 파일이 없어 `npm run lint`는 설정 추가가 필요합니다.
훅 규칙을 별도 CLI 옵션으로 검사할 수 있으며 기능·라우팅 검증은 Vitest 테스트에 있습니다.
화면 최종 확인 시 홈·대화·도감·커뮤니티·인증을 데스크톱과 320~390px 모바일 너비에서 살펴봅니다.
