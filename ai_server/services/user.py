import logging
from ai_server.config import settings

logger = logging.getLogger(__name__)

def get_recommended_questions(authorization: str | None) -> tuple[str, list[dict]]:
    """JWT 토큰에서 캐릭터명을 추출하여 맞춤형 질문 리스트를 반환합니다."""
    character_name = "아델은최강"  # 기본 캐릭터명 Fallback

    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        try:
            import jwt

            # Django와 공유하는 secret_key를 통해 JWT 복호화 시도
            payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
            # 캐릭터명 추출
            character_name = payload.get("main_character_name", character_name)
        except ImportError:
            logger.warning("jwt 패키지가 존재하지 않아 토큰 복호화를 건너뜁니다.")
        except Exception as e:
            logger.warning(f"토큰 복호화 실패 (기본값 사용): {e}")

    # 캐릭터명 스펙 기반 맞춤 질문 데이터 (Mocking & Template)
    recommended = [
        {
            "id": "rec_01",
            "question": f"현재 [{character_name}] 캐릭터의 무기가 앱솔랩스 12성인데, 아케인셰이드 17성으로 넘어가는 비용과 스탯 상승 폭 비교해줘",
            "category": "item_upgrade",
        },
        {
            "id": "rec_02",
            "question": f"현재 [{character_name}] 캐릭터 스펙(주스탯 2.5만 전사) 기준 노말 스우 솔플 최소 컷과 도핑 팁이 어떻게 돼?",
            "category": "boss_guide",
        },
    ]

    return character_name, recommended
