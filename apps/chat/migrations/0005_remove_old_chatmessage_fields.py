# Generated migration to remove old ChatMessage fields

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0004_chatmessage_refactor'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='chatmessage',
            name='user_message',
        ),
        migrations.RemoveField(
            model_name='chatmessage',
            name='ai_response',
        ),
        migrations.RemoveField(
            model_name='chatmessage',
            name='thinking',
        ),
        migrations.RemoveField(
            model_name='chatmessage',
            name='response_time',
        ),
    ]
