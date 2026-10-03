# 공략 문서 (RAG 지식 베이스)

챗봇이 게임 지식 질문에 답할 때 검색하는 공략 문서입니다. `python -m ai_server.rag.ingest`가 이 폴더의 `*.md`를 읽어 벡터 DB에 적재합니다. 이 README는 적재하지 않습니다.

## 문서 형식

각 문서는 YAML 머리말(front matter)로 시작합니다.

```markdown
---
id: starforce            # 고유 ID (파일을 옮겨도 바꾸지 않습니다)
title: 스타포스 강화 가이드
category: guide
status: draft            # draft | reviewed
updated: 2026-10-03      # 마지막으로 내용을 확인한 날짜
aliases: [스포, 별, 강화] # 검색에 도움이 되는 동의어·줄임말
sources:
  - https://maplestory.nexon.com
---

## 섹션 제목
본문...
```

- 본문은 `##` 섹션 단위로 나뉘어 검색됩니다. 섹션 하나가 질문 하나에 답할 수 있게 쓰는 것이 좋습니다.
- 확률, 비용, 최대 단계처럼 패치로 바뀌는 수치는 공식 홈페이지의 확률 정보·업데이트 공지에서 확인한 값만 적고, 확인한 날짜를 `updated`에 남깁니다.

## 검토 절차

1. `status: draft` 문서는 기본적으로 적재하지 않습니다. 개발 중 확인할 때만 `--include-drafts`로 적재합니다.
2. 내용을 공식 자료와 대조하고, `> ⚠️ 검토 필요` 표시를 해결하거나 지운 뒤 `status: reviewed`로 바꿉니다.
3. `python -m ai_server.rag.ingest --sources guides`를 실행하면 바뀐 문서만 다시 적재되고, 지운 문서는 벡터 DB에서도 삭제됩니다.

현재 문서는 모두 Claude가 작성한 **초안(draft)** 입니다. 게임 시스템의 개념 위주로 썼고, 패치로 자주 바뀌는 수치는 비워 두었습니다.
