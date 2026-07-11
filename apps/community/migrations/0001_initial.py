import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="CommunityPost",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("category", models.CharField(choices=[("free", "자유"), ("question", "질문"), ("guide", "공략"), ("trade", "거래"), ("guild", "길드")], db_index=True, default="free", max_length=20, verbose_name="카테고리")),
                ("title", models.CharField(max_length=200, verbose_name="제목")),
                ("content", models.TextField(verbose_name="내용")),
                ("views", models.PositiveIntegerField(default=0, verbose_name="조회수")),
                ("likes", models.PositiveIntegerField(default=0, verbose_name="좋아요 수")),
                ("is_recommended", models.BooleanField(db_index=True, default=False, verbose_name="추천 여부")),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True, verbose_name="작성 일시")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="수정 일시")),
                ("author", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="community_posts", to=settings.AUTH_USER_MODEL, verbose_name="작성자")),
            ],
            options={
                "verbose_name": "커뮤니티 게시글",
                "verbose_name_plural": "커뮤니티 게시글 목록",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="communitypost",
            index=models.Index(fields=["category", "-created_at"], name="community_categor_eb9375_idx"),
        ),
    ]