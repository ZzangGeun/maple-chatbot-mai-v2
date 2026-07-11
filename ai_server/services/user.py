import logging

from ai_server.schemas.user import RecommendedQuestion

logger = logging.getLogger(__name__)


def build_recommended_questions(character_name: str) -> list[RecommendedQuestion]:
    """캐릭터명 기반 맞춤형 추천 질문 리스트를 생성합니다.

    현재는 템플릿 기반 Mocking 데이터이며, 추후 캐릭터 스펙 조회 연동 예정입니다.
    """
    return [
        RecommendedQuestion(
            id="rec_01",
            question=(
                f"현재 [{character_name}] 캐릭터의 무기가 앱솔랩스 12성인데, "
                "아케인셰이드 17성으로 넘어가는 비용과 스탯 상승 폭 비교해줘"
            ),
            category="item_upgrade",
        ),
        RecommendedQuestion(
            id="rec_02",
            question=(
                f"현재 [{character_name}] 캐릭터 스펙(주스탯 2.5만 전사) 기준 "
                "노말 스우 솔플 최소 컷과 도핑 팁이 어떻게 돼?"
            ),
            category="boss_guide",
        ),
    ]
