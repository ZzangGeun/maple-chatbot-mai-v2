# AI 특화 API 명세서 (AI & RAG APIs)

본 문서는 대화 기록(Session) 유지 없이 일회성 RAG 검색을 수행하거나, AI 기반 유저 맞춤형 추천 질문을 가져오는 API 스펙을 정의합니다.

* **Base URL:** `/api/v1/ai`

---

## 1. 일회성 RAG 검색 및 답변 (Single RAG Query)

세션 기록을 생성하지 않고 특정 메이플스토리 주제에 대해 즉시 문서를 찾아 답변만 반환하는 API입니다. (외부 서비스 연동이나 간단한 팝업창 검색용)

* **Endpoint:** `POST /query`
* **Content-Type:** `application/json`

### Request Body
```json
{
  "query": "익스트림 골드 물약 도핑 효과가 뭐야?",
  "top_k": 3
}
```

### Response Body (200 OK)
```json
{
  "success": true,
  "answer": "익스트림 골드 물약은 30분간 경험치 획득량 10% 증가 효과를 줍니다. 몬스터파크 주화를 통해 구매 가능합니다.",
  "referenced_documents": [
    {
      "title": "몬스터파크 상점 및 소비 아이템 리스트",
      "source": "official_website",
      "score": 0.892
    }
  ]
}
```

---

## 2. 맞춤형 추천 질문 생성 (Get Spec-Based Recommended Questions)

사용자의 현재 연동된 대표 캐릭터 스펙(Nexon API로 조회된 스탯, 템셋팅 정보 등)을 AI가 분석하여, 해당 유저가 다음 스펙업 단계로 나아가기 위해 할 만한 유용한 질문들을 추천합니다.

* **Endpoint:** `GET /recommend-questions`
* **Headers:** `Authorization: Bearer <access_token>`

### Response Body (200 OK)
```json
{
  "success": true,
  "character_name": "아델은최강",
  "recommended_questions": [
    {
      "id": "rec_01",
      "question": "현재 무기가 앱솔랩스 12성인데, 아케인셰이드 17성으로 넘어가는 비용과 스탯 상승 폭 비교해줘",
      "category": "item_upgrade"
    },
    {
      "id": "rec_02",
      "question": "현재 주스탯 2.5만 전사인데 노말 스우 솔플 최소 컷과 도핑 팁이 어떻게 돼?",
      "category": "boss_guide"
    }
  ]
}
```

* **설계 의도:** 사용자가 챗봇을 활용해 무엇을 물어봐야 할지 모르는 상황(Cold Start)을 해결하고, 실시간 게임 스펙에 기반한 유용한 AI 개인화 추천 가이드를 제안하여 서비스 리텐션을 증대시킵니다.

---

## 3. 임베딩 동기화 트리거 (Trigger Embedding Synchronization)

관리자 권한이 있는 경우, 최신 패치 내용이나 업데이트 문서를 크롤링한 뒤 강제로 벡터 DB에 임베딩 적재를 재시작하는 API입니다.

* **Endpoint:** `POST /embed/sync`
* **Headers:** `Authorization: Bearer <admin_token>`

### Response Body (202 Accepted)
```json
{
  "success": true,
  "task_id": "task_embed_sync_20260531_001",
  "message": "벡터 DB 임베딩 동기화 작업이 백그라운드에서 시작되었습니다."
}
```
