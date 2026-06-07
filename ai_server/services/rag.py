import logging
from ai_server.llm.factory import get_llm
from ai_server.rag.retriever import Retriever
from ai_server.services.chat import build_langchain_config

logger = logging.getLogger(__name__)

async def process_single_rag_query(query: str, top_k: int) -> dict:
    """단일 질의에 대한 RAG 처리 및 답변을 생성합니다."""
    retriever = Retriever(k=top_k)
    config = build_langchain_config()
        
    docs = retriever.retrieve(
        query, 
        config={"callbacks": config["callbacks"]} if "callbacks" in config else None
    )

    # 1. 검색 문서들로부터 컨텍스트 추출
    context = "\n\n".join([doc.page_content for doc in docs])

    # 2. 메이플스토리 전용 프롬프트 빌드 (나중에 prompts 파일로 분리 가능)
    prompt = (
        "당신은 메이플스토리 도메인 지식이 매우 풍부한 친절한 AI 비서 '메이(MAI)'입니다.\n"
        "아래 제공된 [가이드 컨텍스트]만을 바탕으로 질문에 정확하고 상세히 한국어로 답변해주세요.\n"
        "만약 정보가 부족하거나 답변이 불가능한 경우, '공식 홈페이지나 인게임 정보를 다시 확인해주세요'라고 답변하세요.\n\n"
        f"[가이드 컨텍스트]\n{context}\n\n"
        f"질문: {query}\n"
        "답변:"
    )

    # 3. LLM 비동기 추론 실행
    llm = get_llm()
    response = await llm.ainvoke(
        prompt, 
        config={"callbacks": config["callbacks"]} if "callbacks" in config else None
    )

    if hasattr(response, "content"):
        answer = response.content
    else:
        answer = str(response)

    # 4. 참조 문서 리스트 구성
    referenced_docs = []
    for doc in docs:
        referenced_docs.append(
            {
                "title": doc.metadata.get("title", "제목 없음"),
                "source": doc.metadata.get("source", "알 수 없음"),
                "score": doc.metadata.get("score", 1.0),
            }
        )

    return {
        "success": True,
        "answer": answer.strip(),
        "referenced_documents": referenced_docs,
    }
