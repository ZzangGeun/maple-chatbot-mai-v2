# -*- coding: utf-8 -*-
"""
MAI Chat App Configuration

Django 앱 설정 및 초기화
"""

import logging
from django.apps import AppConfig

logger = logging.getLogger(__name__)



class MaiChatConfig(AppConfig):
    """
    MAI Chat 앱 설정 클래스
    
    비동기 FastAPI 서비스를 통해 AI 모델을 호출하므로,
    여기서 모델을 직접 로드하지 않습니다.
    """
    
    default_auto_field = "django.db.models.BigAutoField"
    name = "chat"
    verbose_name = "MAI 채팅"
    
    def ready(self) -> None:
        """
        Django 앱 초기화
        """
        pass
