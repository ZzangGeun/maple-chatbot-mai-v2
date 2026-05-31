# 벡터 스토어 설계서 (Vector Store)

본 문서는 메이플스토리 가이드 및 패치 정보를 저장하는 벡터 데이터베이스(Vector Database - ChromaDB / Pinecone)의 스키마와 인덱싱 구조를 정의합니다.

## 1. 컬렉션(Collection) 정의

* **컬렉션 이름 (기본):** `maplestory_knowledge_base`
* **임베딩 모델:** `text-embedding-3-small` (Dimension: 1536) 또는 한국어 전용 오픈소스 임베딩 모델 (Dimension: 768)
* **거리 측정 알고리즘:** Cosine Similarity (`cosine`)

---

## 2. 데이터 구조 (Document Schema)

벡터 스토어에 삽입되는 개별 데이터의 필드 구성은 다음과 같습니다.

### 1) Vector Document Fields

| 필드명 | 데이터 타입 | 설명 |
| :--- | :--- | :--- |
| `id` | String | 고유 해시 ID (예: `doc_patch_20260531_001`) |
| `document` | String | 실제 텍스트 내용 (Chunk 텍스트) |
| `embedding` | Float Array | 임베딩 벡터값 (1536차원 또는 768차원) |
| `metadata` | JSON Object | 필터링용 메타데이터 (아래 상세 스키마 참조) |

### 2) Metadata Schema (메타데이터 속성)

유사도 검색 시 효율적인 필터링(Filtering)을 위해 아래 메타데이터 스키마를 준수합니다.

```json
{
  "source": "official_website | patch_note | database | wiki",
  "category": "character | item | potential | starforce | boss | patch",
  "doc_type": "guide | faq | raw_data | tables",
  "patch_version": "1.2.392",
  "title": "[업데이트] 신규 지역 테네브리스 추가",
  "chunk_index": 4,
  "created_at": "2026-05-31T03:00:00Z"
}
```

* **메타데이터 활용 예시:**
  - 사용자가 "이번 패치에서 보스 리워드 어떻게 바뀌었어?" 라고 물었을 때, `patch_version` 혹은 `category="patch"` 필터를 걸어 최근 패치노트 벡터 데이터만 한정하여 검색(Filtering)함으로써 검색 품질을 높이고 할루시네이션(Hallucination)을 줄입니다.

---

## 3. 벡터 데이터 갱신 전략

1. **중복 삽입 방지 (Upsert 전략)**
   - 문서 원본의 고유 URL이나 파일 경로 + 청크 인덱스를 조합한 고유한 해시 스트링을 생성하여 `id`로 지정합니다.
   - 배치 임베딩 적재 시 데이터가 수정되었을 경우 자동으로 덮어쓰기(`Upsert`) 처리되어 동일 데이터가 중복 인덱싱되지 않게 합니다.

2. **인덱스 관리**
   - ChromaDB 사용 시 데이터 볼륨이 커질 경우 인덱스 로딩 속도가 느려질 수 있으므로 성능 최적화를 위한 인덱싱 설정(`HNSW`) 매개변수를 조정합니다.
     - `hnsw:space`: `cosine`
     - `hnsw:construction_ef`: 100
     - `hnsw:M`: 16
