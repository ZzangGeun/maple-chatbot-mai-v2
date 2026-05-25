# accounts/models.py
from django.db import models
from django.contrib.auth.models import User


# UserProfile 모델: Django의 기본 User 모델을 확장하여 추가 정보 저장
class UserProfile(models.Model):
    # 1:1 관계 설정: Django 기본 User와 연결
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    # [1] 메이플 닉네임 (대표 캐릭터명)
    maple_nickname = models.CharField(
        max_length=50, 
        blank=True, 
        null=True,
        verbose_name="메이플 캐릭터 닉네임"
    )
    
    # [2] 넥슨 API 키
    # 이 필드는 민감 정보이므로, 암호화 처리 후 저장하는 것이 좋습니다.
    # CharField를 사용하더라도, Django가 아닌 별도의 암호화 로직이 필요합니다.
    nexon_api_key = models.CharField(
        max_length=200, 
        blank=True, 
        null=True
    )
    