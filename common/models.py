from django.db import models


class TimestampedModel(models.Model):
    """모든 모델에 created_at, updated_at을 일관되게 제공하는 추상 베이스 모델"""
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='생성일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')

    class Meta:
        abstract = True
