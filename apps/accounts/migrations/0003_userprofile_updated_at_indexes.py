# Generated migration for UserProfile indexes

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0002_remove_userprofile_character_ocid_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="userprofile",
            name="created_at",
            field=models.DateTimeField(
                auto_now_add=True, db_index=True, verbose_name="생성일"
            ),
        ),
        migrations.AlterField(
            model_name="userprofile",
            name="nexon_api_key",
            field=models.CharField(
                blank=True,
                db_index=True,
                help_text="넥슨 오픈 API 키 (선택사항)",
                max_length=255,
                null=True,
                verbose_name="넥슨 API 키",
            ),
        ),
        migrations.AlterField(
            model_name="userprofile",
            name="maple_nickname",
            field=models.CharField(
                db_index=True, max_length=12, unique=True, verbose_name="메이플 닉네임"
            ),
        ),
    ]
