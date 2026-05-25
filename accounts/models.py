from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

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
    
    maple_nickname = models.CharField(
        max_length=12,  # 메이플스토리 닉네임 최대 길이
        unique=True,  # 중복 방지
        verbose_name='메이플 닉네임'
    )
    
    nexon_api_key = models.CharField(
        max_length=255,
        blank=True,  # 선택사항
        null=True,
        verbose_name='넥슨 API 키',
        help_text='넥슨 오픈 API 키 (선택사항)'
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')
    
    class Meta:
        verbose_name = '사용자 프로필'
        verbose_name_plural = '사용자 프로필들'
    
    def __str__(self):
        return f"{self.user.username} - {self.maple_nickname}"

