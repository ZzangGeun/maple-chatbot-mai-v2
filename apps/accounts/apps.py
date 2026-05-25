from django.apps import AppConfig


class SnsLoginConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.accounts"
    label = "accounts"  # DB 테이블명 유지를 위해 기존 label 명시
