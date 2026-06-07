# -*- coding: utf-8 -*-
"""
MAI Chat Django Models

채팅 세션 및 메시지를 저장하는 Django 모델
"""

import uuid
from django.db import models
from django.conf import settings

from common.exceptions.chat import InvalidSessionId, SessionNotFound


class ChatSessionQuerySet(models.QuerySet):
    """채팅 세션에 특화된 커스텀 QuerySet.

    비즈니스 레이어 및 뷰에서 데이터 조회 및 예외 처리를 직접 반복하지 않도록
    캡슐화하여 장고스러운 방식으로 DB 접근 계층을 격리합니다.
    """

    def get_by_uuid_or_raise(self, session_id: str) -> "ChatSession":
        """문자열 세션 ID를 UUID로 파싱하고 해당하는 ChatSession 객체를 반환합니다.

        존재하지 않거나 형식이 어긋난 경우 알맞은 커스텀 예외를 유발합니다.

        Args:
            session_id: UUID 포맷 문자열 세션 ID.

        Returns:
            조회된 ChatSession 인스턴스.

        Raises:
            InvalidSessionId: session_id가 올바른 UUID 포맷이 아닐 때.
            SessionNotFound: 해당 UUID 세션이 DB에 존재하지 않을 때.
        """
        try:
            session_uuid = uuid.UUID(session_id)
        except ValueError:
            raise InvalidSessionId()

        session = self.filter(session_id=session_uuid).first()
        if not session:
            raise SessionNotFound(session_id)
        return session

    async def aget_by_uuid_or_raise(self, session_id: str) -> "ChatSession":
        """문자열 세션 ID를 비동기적으로 조회하여 반환합니다.

        동기 get_by_uuid_or_raise의 비동기(Async) 대응 버전입니다.

        Args:
            session_id: UUID 포맷 문자열 세션 ID.

        Returns:
            조회된 ChatSession 인스턴스.

        Raises:
            InvalidSessionId: session_id가 올바른 UUID 포맷이 아닐 때.
            SessionNotFound: 해당 UUID 세션이 DB에 존재하지 않을 때.
        """
        try:
            session_uuid = uuid.UUID(session_id)
        except ValueError:
            raise InvalidSessionId()

        session = await self.filter(session_id=session_uuid).afirst()
        if not session:
            raise SessionNotFound(session_id)
        return session


class ChatSession(models.Model):
    """하나의 대화방"""
    session_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="세션 ID"
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chat_sessions",
        null=True,
        blank=True,
        db_index=True,
        verbose_name="사용자"
    )

    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name="생성 일시")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정 일시")

    objects = ChatSessionQuerySet.as_manager()

    class Meta:
        verbose_name = "채팅 세션"
        verbose_name_plural = "채팅 세션 목록"
        indexes = [
            models.Index(fields=['user', '-created_at']),
        ]

    def __str__(self):
        return f"{str(self.session_id)[:8]}"


class ChatMessage(models.Model):
    """채팅 메시지 (정규화된 구조: 각 메시지는 role과 content를 가짐)"""
    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('system', 'System'),
    ]

    session = models.ForeignKey(
        ChatSession,
        on_delete=models.CASCADE,
        related_name="messages",
        verbose_name="세션"
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='assistant',
        db_index=True,
        verbose_name="역할"
    )

    content = models.TextField(verbose_name="메시지 내용", null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name="생성 일시")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정 일시")

    class Meta:
        verbose_name = "채팅 메시지"
        verbose_name_plural = "채팅 메시지 목록"
        indexes = [
            models.Index(fields=['session', 'created_at']),
            models.Index(fields=['session', 'role']),
        ]

    def __str__(self):
        return f"{self.role}: {self.content[:50]}"


class MessageMetadata(models.Model):
    """메시지 메타데이터 (성능, 사고 과정, 모델 정보 등)"""
    message = models.OneToOneField(
        ChatMessage,
        on_delete=models.CASCADE,
        related_name="metadata",
        verbose_name="메시지"
    )

    thinking = models.TextField(
        blank=True,
        null=True,
        verbose_name="LLM 사고 과정",
        help_text="Qwen Thinking 모델 사고 과정"
    )

    response_time_ms = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="응답 시간(ms)"
    )

    model_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="사용 모델명"
    )

    tokens_used = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="토큰 사용량"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name="생성 일시"
    )

    class Meta:
        verbose_name = "메시지 메타데이터"
        verbose_name_plural = "메시지 메타데이터 목록"
        indexes = [
            models.Index(fields=['message']),
        ]

    def __str__(self):
        return f"Metadata for {self.message}"

