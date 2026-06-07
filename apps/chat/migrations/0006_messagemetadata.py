# Generated migration to create MessageMetadata model

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0005_remove_old_chatmessage_fields'),
    ]

    operations = [
        migrations.CreateModel(
            name='MessageMetadata',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('thinking', models.TextField(blank=True, help_text='Qwen Thinking 모델 사고 과정', null=True, verbose_name='LLM 사고 과정')),
                ('response_time_ms', models.IntegerField(blank=True, null=True, verbose_name='응답 시간(ms)')),
                ('model_name', models.CharField(blank=True, max_length=100, verbose_name='사용 모델명')),
                ('tokens_used', models.IntegerField(blank=True, null=True, verbose_name='토큰 사용량')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='생성 일시')),
                ('message', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='metadata', to='chat.chatmessage', verbose_name='메시지')),
            ],
            options={
                'verbose_name': '메시지 메타데이터',
                'verbose_name_plural': '메시지 메타데이터 목록',
            },
        ),
        migrations.AddIndex(
            model_name='messagemetadata',
            index=models.Index(fields=['message'], name='chat_msgmeta_msg_idx'),
        ),
    ]
