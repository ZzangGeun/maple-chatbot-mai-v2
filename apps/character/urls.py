# character/urls.py
"""
캐릭터 앱 URL 설정

중앙 urls.py에서 /api/character/ prefix로 include됩니다.

    GET  /api/character/search/?name={캐릭터명}  — 캐릭터 정보 조회
"""

from django.urls import path
from . import views

app_name = "character"

urlpatterns = [
    path("search/", views.character_search, name="character_search"),
]
