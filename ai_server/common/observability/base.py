# -*- coding: utf-8 -*-
"""
옵저버빌리티 클라이언트 인터페이스 모듈

특정 모니터링 도구(Langfuse 등)에 강하게 결합하지 않도록
인증 및 수집 라이프사이클을 추상 인터페이스화합니다.
"""

from abc import ABC, abstractmethod

from langchain_core.callbacks import BaseCallbackHandler


class BaseObservabilityClient(ABC):
    """옵저버빌리티 도구 확장을 위한 최상위 추상 클래스."""

    @abstractmethod
    def startup(self) -> None:
        """모니터링 SDK를 초기화하고 리소스를 생성하는 비즈니스 진입점.
        앱 가동(lifespan) 시점에 최초 1회만 호출됩니다.
        """
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """SDK 큐에 쌓인 미전송 이벤트 데이터를 원격 서버로 플러시(flush)하고 리소스를 비웁니다.
        앱 중지(lifespan) 시점에 호출되어 데이터 누수를 방지합니다.
        """
        pass

    @abstractmethod
    def get_callback(self) -> BaseCallbackHandler | None:
        """LangChain 모니터링 수집을 위한 콜백 핸들러 인스턴스를 반환합니다.

        Returns:
            LangChain의 BaseCallbackHandler 상속 객체 또는 None (모니터링 비활성화 시).
        """
        pass
