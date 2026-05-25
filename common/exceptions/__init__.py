# common/exceptions 패키지
# 프로젝트 전역에서 사용하는 커스텀 예외 클래스 모음

from common.exceptions.base import AppException
from common.exceptions.nexon import (
    CharacterNotFound,
    ApiRateLimitExceeded,
    NexonApiError,
)
from common.exceptions.chat import (
    SessionNotFound,
    AiServerUnavailable,
    InvalidSessionId,
)

__all__ = [
    "AppException",
    "CharacterNotFound",
    "ApiRateLimitExceeded",
    "NexonApiError",
    "SessionNotFound",
    "AiServerUnavailable",
    "InvalidSessionId",
]
