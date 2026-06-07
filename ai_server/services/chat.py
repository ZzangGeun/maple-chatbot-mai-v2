import re
from ai_server.common.observability import get_langfuse_callback

def build_langchain_config(session_id: str | None = None) -> dict:
    """Langchain 호출 시 공통 설정을 생성합니다."""
    config = {}
    if session_id:
        config["configurable"] = {"thread_id": session_id}
        config["metadata"] = {"langfuse_session_id": session_id}
    
    callbacks = []
    langfuse_handler = get_langfuse_callback()
    if langfuse_handler:
        callbacks.append(langfuse_handler)
        
    if callbacks:
        config["callbacks"] = callbacks
        
    return config

def parse_thinking_response(text: str) -> tuple[str, str]:
    """
    Qwen Thinking 모델의 출력에서 <think>...</think> 부분을 분리합니다.

    Args:
        text: LLM 원본 응답 텍스트.

    Returns:
        (thinking_process, final_answer) 튜플.
    """
    if "<think>" in text and "</think>" in text:
        think_match = re.search(r"<think>(.*?)</think>", text, re.DOTALL)
        thinking_process = think_match.group(1).strip() if think_match else ""
        final_answer = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
        return thinking_process, final_answer

    if "<think>" in text:
        # 닫는 태그 없이 <think>가 있는 비정상 케이스
        return "태그 파싱 에러", text.replace("<think>", "").strip()

    return "", text.strip()
