from django.contrib import admin
from .models import ChatSession, ChatMessage

class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    readonly_fields = ('created_at',)

@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ('session_id', 'user', 'created_at')
    inlines = [ChatMessageInline] # 세션 상세 화면에서 메시지 내역을 같이 보여줌

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'session_id', 'user_message', 'created_at')
    list_filter = ('session_id', 'created_at')