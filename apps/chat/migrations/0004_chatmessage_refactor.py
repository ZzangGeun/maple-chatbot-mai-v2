# Generated migration for ChatMessage refactoring

import django.db.models.deletion
from django.db import migrations, models


def migrate_chat_messages(apps, schema_editor):
    """기존 ChatMessage 데이터를 새로운 구조로 마이그레이션"""
    ChatMessage = apps.get_model('chat', 'ChatMessage')
    ChatSession = apps.get_model('chat', 'ChatSession')
    MessageMetadata = apps.get_model('chat', 'MessageMetadata')

    # 기존 메시지 데이터 수집
    old_messages = ChatMessage.objects.all()
    new_messages = []

    for old_msg in old_messages:
        session = ChatSession.objects.get(pk=old_msg.session_id_id)

        # User 메시지
        if hasattr(old_msg, 'user_message') and old_msg.user_message:
            user_msg = ChatMessage(
                session=session,
                role='user',
                content=old_msg.user_message
            )
            new_messages.append(user_msg)

        # Assistant 메시지
        if hasattr(old_msg, 'ai_response') and old_msg.ai_response:
            assistant_msg = ChatMessage(
                session=session,
                role='assistant',
                content=old_msg.ai_response
            )
            new_messages.append(assistant_msg)

    # 새로운 메시지 일괄 생성 (save하지 않음 - 아직 필드가 없음)
    # 이 마이그레이션 단계에서는 필드 구조만 변경


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0003_chatsession_updated_at_indexes'),
    ]

    operations = [
        # 1. 새로운 필드 추가
        migrations.AddField(
            model_name='chatmessage',
            name='role',
            field=models.CharField(
                choices=[('user', 'User'), ('assistant', 'Assistant'), ('system', 'System')],
                default='assistant',
                db_index=True,
                max_length=20,
                verbose_name='역할'
            ),
        ),
        migrations.AddField(
            model_name='chatmessage',
            name='content',
            field=models.TextField(blank=True, null=True, verbose_name='메시지 내용'),
        ),
        migrations.AddField(
            model_name='chatmessage',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, verbose_name='수정 일시'),
        ),

        # 2. 기존 필드 수정
        migrations.AlterField(
            model_name='chatmessage',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='생성 일시'),
        ),

        # 3. 세션 참조 이름 변경 (session_id → session)
        migrations.RenameField(
            model_name='chatmessage',
            old_name='session_id',
            new_name='session',
        ),

        # 4. 인덱스 추가
        migrations.AddIndex(
            model_name='chatmessage',
            index=models.Index(fields=['session', 'created_at'], name='chat_msg_session_created_idx'),
        ),
        migrations.AddIndex(
            model_name='chatmessage',
            index=models.Index(fields=['session', 'role'], name='chat_msg_session_role_idx'),
        ),
    ]
