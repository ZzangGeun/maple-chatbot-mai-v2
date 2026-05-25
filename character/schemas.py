# character/schemas.py
"""
캐릭터 API용 Pydantic 스키마 정의

Django Ninja 의존성을 제거하고 순수 pydantic.BaseModel로 전환합니다.
현재는 응답 직렬화에 직접 사용하지 않지만, 타입 힌트 및 문서화 목적으로 유지합니다.
"""

from typing import Any

from pydantic import BaseModel


class CharacterSearchOut(BaseModel):
    """캐릭터 정보 조회 성공 응답 스키마."""

    message: str
    status: str
    data: dict[str, Any]


class CharacterErrorOut(BaseModel):
    """캐릭터 정보 조회 실패 응답 스키마."""

    error: str
    status: str
