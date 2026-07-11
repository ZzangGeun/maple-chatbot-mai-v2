from django.conf import settings
from django.db import models


class CommunityPost(models.Model):
    class Category(models.TextChoices):
        FREE = "free", "자유"
        QUESTION = "question", "질문"
        GUIDE = "guide", "공략"
        TRADE = "trade", "거래"
        GUILD = "guild", "길드"

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="community_posts",
        verbose_name="작성자",
    )
    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        default=Category.FREE,
        db_index=True,
        verbose_name="카테고리",
    )
    title = models.CharField(max_length=200, verbose_name="제목")
    content = models.TextField(verbose_name="내용")
    views = models.PositiveIntegerField(default=0, verbose_name="조회수")
    likes = models.PositiveIntegerField(default=0, verbose_name="좋아요 수")
    is_recommended = models.BooleanField(default=False, db_index=True, verbose_name="추천 여부")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name="작성 일시")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정 일시")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "커뮤니티 게시글"
        verbose_name_plural = "커뮤니티 게시글 목록"
        indexes = [
            models.Index(fields=["category", "-created_at"]),
        ]

    def __str__(self):
        return self.title