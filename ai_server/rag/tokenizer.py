# ai_server/rag/tokenizer.py
"""
BM25 키워드 검색용 한국어 토크나이저 (kiwipiepy)

공백 기준으로 자르면 '스타포스는'과 '스타포스'가 다른 단어가 되므로 형태소 분석으로
조사·어미를 떼고 의미 있는 형태소만 남깁니다. 게임 용어는 사용자 사전에 등록해
'아케인심볼'이 '아/케이/ㄴ/심볼'처럼 잘못 나뉘지 않게 합니다.
"""

import threading
from typing import Any

# 형태소 분석기가 잘못 나누는 게임 용어
GAME_TERMS = (
    "스타포스", "스타캐치", "파괴방지", "샤이닝",
    "잠재능력", "에디셔널", "레전드리", "유니크", "에픽", "레어", "큐브", "등업",
    "추옵", "환불", "강환불", "영환불",
    "아케인심볼", "어센틱심볼", "아케인포스", "어센틱포스", "심볼",
    "헥사", "솔에르다", "솔 에르다", "오리진", "마스터리",
    "유니온", "아티팩트", "공격대원",
    "보공", "방무", "크뎀", "크확", "쿨감", "벞지", "공마", "주스탯", "부스탯", "올스탯",
    "레벨업", "스펙업", "템셋", "프리셋", "무릉", "무릉도장", "링크",
    "하스우", "하루시", "하윌", "진힐라", "검마", "세렌", "칼로스", "카벨", "카루타",
    "메소", "일퀘", "주퀘",
)

# 검색어로 쓸 품사: 일반·고유 명사, 의존 명사, 수사, 외국어, 숫자, 어근, 동사·형용사 어간
_KEEP_TAGS = {"NNG", "NNP", "NNB", "NR", "SL", "SN", "XR", "VV", "VA"}

_kiwi: Any = None
_lock = threading.Lock()


def _get_kiwi() -> Any:
    """형태소 분석기를 지연 생성합니다. (패키지가 없어도 서버 기동은 되도록 import도 이때 합니다)"""
    global _kiwi
    with _lock:
        if _kiwi is None:
            from kiwipiepy import Kiwi

            kiwi = Kiwi()
            for term in GAME_TERMS:
                kiwi.add_user_word(term.replace(" ", ""), "NNP", 0)
            _kiwi = kiwi
    return _kiwi


def tokenize(text: str) -> list[str]:
    """검색에 쓸 형태소 목록을 반환합니다. (영문은 소문자로 통일)"""
    return [
        token.form.lower()
        for token in _get_kiwi().tokenize(text)
        if token.tag in _KEEP_TAGS
    ]
