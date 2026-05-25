from django.apps import AppConfig


class CharacterInfoConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.character"
    label = "character"  # DB 테이블명 유지를 위해 기존 label 명시
