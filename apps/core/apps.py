from django.apps import AppConfig


class MainPageConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"
    label = "core"  # DB 테이블명 유지를 위해 기존 label 명시
