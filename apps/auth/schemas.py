# auth/schemas.py
"""
계정 API 요청 스키마 (Pydantic v2 기반)

Django Ninja 의존성을 제거하고 순수 pydantic.BaseModel로 전환합니다.
입력값 유효성 검사(형식, 비밀번호 길이·일치)를 담당합니다.
"""

import re

from pydantic import BaseModel, field_validator, model_validator


# ---------------------------------------------------------------------------
# 요청(Request) 스키마
# ---------------------------------------------------------------------------


class SignupSchema(BaseModel):
    """회원가입 요청 스키마."""

    username: str
    password: str
    confirm_password: str
    maple_nickname: str
    nexon_api_key: str

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        """아이디 형식 검사: 6~20자, 영문/숫자/밑줄만 허용합니다."""
        if not re.match(r"^[a-zA-Z0-9_]{6,20}$", v):
            raise ValueError("아이디는 6~20자의 영문자, 숫자, 밑줄(_)만 사용할 수 있습니다.")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """비밀번호 최소 길이 검사."""
        if len(v) < 8:
            raise ValueError("비밀번호는 최소 8자 이상이어야 합니다.")
        return v

    @model_validator(mode="after")
    def validate_confirm_password(self) -> "SignupSchema":
        """비밀번호 일치 여부를 검사합니다."""
        if self.password != self.confirm_password:
            raise ValueError("비밀번호와 비밀번호 확인이 일치하지 않습니다.")
        return self


class LoginSchema(BaseModel):
    """로그인 요청 스키마."""

    username: str
    password: str
