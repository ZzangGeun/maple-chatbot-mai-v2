# common/utils/text.py
"""
텍스트 처리 유틸리티

HTML 파싱, 텍스트 정규화 등 프로젝트 전역에서 사용하는
문자열 변환 함수를 모아둡니다.
"""

from bs4 import BeautifulSoup


def html_to_text(html_content: str, separator: str = "\n") -> str:
    """
    HTML 문자열에서 태그를 제거하고 순수 텍스트만 추출합니다.

    Nexon API의 공지사항 등은 HTML 형식으로 제공되므로,
    RAG 문서화 등에서 이 함수로 텍스트를 추출합니다.

    Args:
        html_content: 변환할 HTML 문자열.
        separator: 태그 사이에 삽입할 구분자. 기본 줄바꿈.

    Returns:
        태그가 제거된 순수 텍스트.
    """
    if not html_content:
        return ""
    soup = BeautifulSoup(html_content, "html.parser")
    return soup.get_text(separator=separator).strip()


def truncate(text: str, max_length: int = 20, suffix: str = "...") -> str:
    """
    텍스트를 지정된 길이로 자르고 접미사를 붙입니다.

    채팅 세션 제목 등 UI 표시용 텍스트를 생성할 때 사용합니다.

    Args:
        text: 원본 텍스트.
        max_length: 최대 길이 (접미사 포함 전).
        suffix: 잘린 텍스트 뒤에 붙일 접미사.

    Returns:
        잘린 텍스트. max_length 이하면 원본 반환.
    """
    if not text or len(text) <= max_length:
        return text or ""
    return text[:max_length] + suffix


def normalize_character_name(name: str) -> str:
    """
    캐릭터 이름을 정규화합니다.

    앞뒤 공백 제거, 연속 공백 단일화 등을 처리합니다.
    메이플스토리 캐릭터명 검색 시 일관된 입력을 보장합니다.

    Args:
        name: 원본 캐릭터 이름.

    Returns:
        정규화된 캐릭터 이름.
    """
    if not name:
        return ""
    # 앞뒤 공백 제거 후 연속 공백을 단일 공백으로 치환
    return " ".join(name.split())
