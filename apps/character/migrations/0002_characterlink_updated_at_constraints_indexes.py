# Generated migration for CharacterLink updates

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('character', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='characterlink',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, verbose_name='수정 일시'),
        ),
        migrations.AlterField(
            model_name='characterlink',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='생성 일시'),
        ),
        migrations.AlterField(
            model_name='characterlink',
            name='is_main',
            field=models.BooleanField(db_index=True, default=False, verbose_name='대표 캐릭터 여부'),
        ),
        migrations.AlterField(
            model_name='characterlink',
            name='user',
            field=models.ForeignKey(db_index=True, on_delete=django.db.models.deletion.CASCADE, related_name='character_links', to='auth.user', verbose_name='사용자'),
        ),
        migrations.AddConstraint(
            model_name='characterlink',
            constraint=models.UniqueConstraint(fields=('user', 'character_name'), name='unique_user_character_name'),
        ),
        migrations.AddIndex(
            model_name='characterlink',
            index=models.Index(fields=['user', 'is_main'], name='character_c_user_id_a1b2c3_idx'),
        ),
        migrations.AddIndex(
            model_name='characterlink',
            index=models.Index(fields=['created_at'], name='character_c_created_d4e5f6_idx'),
        ),
    ]

