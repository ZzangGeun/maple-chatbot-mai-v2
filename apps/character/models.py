from django.db import models
from django.conf import settings

class CharacterLink(models.Model):
    """
    메이플스토리 캐릭터 연동 모델
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="character_links",
        verbose_name="사용자"
    )
    character_name = models.CharField(max_length=50, verbose_name="메이플스토리 캐릭터명")
    ocid = models.CharField(max_length=100, unique=True, verbose_name="넥슨 Open API 식별자(OCID)")
    world_name = models.CharField(max_length=30, verbose_name="월드 이름")
    is_main = models.BooleanField(default=False, verbose_name="대표 캐릭터 여부")
    verified_at = models.DateTimeField(null=True, blank=True, verbose_name="본인인증 완료 일시")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성 일시")

    class Meta:
        verbose_name = "캐릭터 연동"
        verbose_name_plural = "캐릭터 연동 목록"

    def __str__(self) -> str:
        return f"{self.character_name} ({self.world_name}) - {self.user.username}"

