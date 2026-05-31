from django.apps import AppConfig


class SnsLoginConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.auth"
    label = "accounts"  # Django 내장 auth 앱과의 충돌 방지 및 기존 DB 테이블명 유지
