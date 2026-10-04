# ai_server/api/deps.py
"""
FastAPI 공통 의존성(Dependency) 모듈

라우트 핸들러에서 반복되는 관심사(그래프 접근, 인증, 토큰 파싱)를
FastAPI의 Depends 패턴으로 분리하여 재사용성과 테스트 용이성을 높입니다.
"""

import hmac
import logging

from fastapi import Header, HTTPException, Request

from ai_server.config import settings

logger = logging.getLogger("AI_Server.Deps")

# 인증 토큰이 없거나 파싱에 실패했을 때 사용하는 기본 캐릭터명
DEFAULT_CHARACTER_NAME = "아델은최강"


def get_graph(request: Request):
    """lifespan에서 app.state에 바인딩된 컴파일된 LangGraph를 반환합니다."""
    graph = getattr(request.app.state, "graph", None)
    if graph is None:
        raise HTTPException(
            status_code=503,
            detail="AI 그래프가 아직 초기화되지 않았습니다. 잠시 후 다시 시도해주세요.",
        )
    return graph


def verify_internal_token(x_internal_token: str | None = Header(default=None)) -> None:
    """Django가 보낸 내부 호출 토큰(X-Internal-Token)을 검증합니다.

    AI_SERVER_TOKEN을 설정하지 않은 로컬 개발 환경에서는 검사하지 않습니다.
    """
    expected = settings.ai_server_token
    if not expected:
        return
    if not x_internal_token or not hmac.compare_digest(x_internal_token, expected):
        logger.warning("내부 호출 토큰이 없거나 일치하지 않습니다.")
        raise HTTPException(status_code=401, detail="인증이 필요합니다.")


def require_admin_token(authorization: str | None = Header(default=None)) -> str:
    """관리자용 엔드포인트의 Bearer 토큰을 AI_ADMIN_TOKEN과 비교해 검증합니다.

    AI_ADMIN_TOKEN을 설정하지 않으면 관리자 API를 아무도 쓸 수 없습니다.
    """
    token = (authorization or "").removeprefix("Bearer ").strip() if (authorization or "").startswith("Bearer ") else ""
    expected = settings.admin_token
    if not expected or not token or not hmac.compare_digest(token, expected):
        logger.warning("관리자 인증 실패 (토큰 누락·불일치 또는 AI_ADMIN_TOKEN 미설정)")
        raise HTTPException(status_code=401, detail="인증이 필요합니다.")
    return token


def get_character_name(authorization: str | None = Header(default=None)) -> str:
    """
    Authorization 헤더의 JWT에서 대표 캐릭터명을 추출합니다.

    토큰이 없거나 복호화에 실패하면 기본 캐릭터명으로 폴백합니다.
    """
    if not authorization or not authorization.startswith("Bearer "):
        return DEFAULT_CHARACTER_NAME

    token = authorization.removeprefix("Bearer ").strip()
    try:
        import jwt

        # Django와 공유하는 secret_key를 통해 JWT 복호화 시도
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        return payload.get("main_character_name", DEFAULT_CHARACTER_NAME)
    except ImportError:
        logger.warning("jwt 패키지가 존재하지 않아 토큰 복호화를 건너뜁니다.")
    except Exception as e:
        logger.warning(f"토큰 복호화 실패 (기본값 사용): {e}")

    return DEFAULT_CHARACTER_NAME
