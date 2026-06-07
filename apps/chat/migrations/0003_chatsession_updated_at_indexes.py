# Generated migration for ChatSession updates

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0002_enable_pgvector'),
    ]

    operations = [
        migrations.AddField(
            model_name='chatsession',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, verbose_name='수정 일시'),
        ),
        migrations.AlterField(
            model_name='chatsession',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='생성 일시'),
        ),
        migrations.AlterField(
            model_name='chatsession',
            name='user',
            field=models.ForeignKey(blank=True, db_index=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='chat_sessions', to='auth.user', verbose_name='사용자'),
        ),
        migrations.AddIndex(
            model_name='chatsession',
            index=models.Index(fields=['user', '-created_at'], name='chat_chatsession_user_created_idx'),
        ),
    ]

