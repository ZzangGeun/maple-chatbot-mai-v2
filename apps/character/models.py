from django.db import models
from django.conf import settings
from django.utils import timezone


class CharacterLinkQuerySet(models.QuerySet):
    """캐릭터 연동 데이터를 조회/가공하기 위한 커스텀 QuerySet.

    비즈니스 서비스(services.py)가 데이터베이스 기술에 의존적인 쿼리 로직을
    직접 다루지 않도록 캡슐화하고, 비비동기 처리를 안전하게 지원하기 위해 정의합니다.
    """

    async def is_first_link_async(self, user) -> bool:
        """사용자에게 연동된 캐릭터가 존재하지 않는지(첫 연동인지) 검사합니다.

        Args:
            user: 검사할 Django User 객체.

        Returns:
            첫 연동인 경우 True, 이미 연동된 캐릭터가 있다면 False.
        """
        return not await self.filter(user=user).aexists()

    async def update_or_create_link_async(
        self, user, character_name: str, ocid: str, world_name: str, is_main: bool
    ) -> tuple["CharacterLink", bool]:
        """캐릭터 연동 데이터를 데이터베이스에 비동기적으로 생성하거나 갱신합니다.

        본인 인증 완료 시점에 연동 내역을 갱신하기 위해 사용됩니다.

        Args:
            user: Django User 객체.
            character_name: 연동할 캐릭터 이름.
            ocid: 넥슨 Open API 식별자.
            world_name: 캐릭터가 속한 월드 이름.
            is_main: 대표 캐릭터 지정 여부.

        Returns:
            (CharacterLink 인스턴스, 생성 여부 bool) 튜플.
        """
        return await self.aupdate_or_create(
            user=user,
            character_name=character_name,
            defaults={
                "ocid": ocid,
                "world_name": world_name,
                "is_main": is_main,
                "verified_at": timezone.now(),
            },
        )


class CharacterLink(models.Model):
    """
    메이플스토리 캐릭터 연동 모델
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="character_links",
        db_index=True,
        verbose_name="사용자"
    )
    character_name = models.CharField(max_length=50, verbose_name="메이플스토리 캐릭터명")
    ocid = models.CharField(max_length=100, unique=True, verbose_name="넥슨 Open API 식별자(OCID)")
    world_name = models.CharField(max_length=30, verbose_name="월드 이름")
    is_main = models.BooleanField(default=False, db_index=True, verbose_name="대표 캐릭터 여부")
    verified_at = models.DateTimeField(null=True, blank=True, verbose_name="본인인증 완료 일시")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name="생성 일시")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정 일시")

    objects = CharacterLinkQuerySet.as_manager()

    class Meta:
        verbose_name = "캐릭터 연동"
        verbose_name_plural = "캐릭터 연동 목록"
        unique_together = ('user', 'character_name')
        indexes = [
            models.Index(fields=['user', 'is_main']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self) -> str:
        return f"{self.character_name} ({self.world_name}) - {self.user.username}"