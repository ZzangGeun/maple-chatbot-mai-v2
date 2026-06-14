from django.db import models
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from typing import Optional


class UserProfileQuerySet(models.QuerySet):
    """사용자 프로필 데이터 조회/필터링을 담당하는 커스텀 QuerySet.

    비즈니스 서비스 및 뷰에서 DB 스키마 지식이 노출되지 않도록 DB 접근 로직을 캡슐화합니다.
    """

    def exists_by_nickname(self, nickname: str) -> bool:
        """주어진 메이플 닉네임이 사용 중인지 확인합니다.

        Args:
            nickname: 메이플스토리 캐릭터 닉네임.

        Returns:
            중복 시 True, 사용 가능 시 False.
        """
        return self.filter(maple_nickname=nickname).exists()

    def get_by_user_or_none(self, user) -> Optional["UserProfile"]:
        """특정 사용자의 프로필 객체를 안전하게 조회합니다.

        DoesNotExist 예외 처리를 내부에서 처리하여 뷰 및 서비스 코드를 단순하게 유지합니다.

        Args:
            user: Django User 객체.

        Returns:
            UserProfile 인스턴스 또는 None.
        """
        try:
            return self.get(user=user)
        except ObjectDoesNotExist:
            return None


class UserProfile(models.Model):
    """
    Django의 기본 User 모델을 확장하는 프로필 모델입니다.
    메이플스토리 관련 추가 정보를 저장합니다.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile'
    )

    nexon_api_key = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        db_index=True,
        verbose_name='넥슨 API 키',
        help_text='넥슨 오픈 API 키 (선택사항)'
    )

    maple_nickname = models.CharField(
        max_length=12,
        unique=True,
        db_index=True,
        null=True,
        blank=True,
        verbose_name='메이플 닉네임'
    )

    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='생성일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')

    objects = UserProfileQuerySet.as_manager()

    class Meta:
        verbose_name = '사용자 프로필'
        verbose_name_plural = '사용자 프로필들'

    def __str__(self):
        return f"{self.user.username} - {self.maple_nickname}"

