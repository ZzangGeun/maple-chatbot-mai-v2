from django.contrib import admin
from .models import ChatSession, ChatMessage, MessageMetadata

class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    readonly_fields = ('created_at', 'updated_at')

class MessageMetadataInline(admin.StackedInline):
    model = MessageMetadata
    extra = 0
    readonly_fields = ('created_at',)

@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ('session_id', 'user', 'created_at', 'updated_at')
    list_filter = ('user', 'created_at')
    readonly_fields = ('session_id', 'created_at', 'updated_at')
    inlines = [ChatMessageInline]

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'session', 'role', 'content', 'created_at')
    list_filter = ('session', 'role', 'created_at')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [MessageMetadataInline]

@admin.register(MessageMetadata)
class MessageMetadataAdmin(admin.ModelAdmin):
    list_display = ('message', 'model_name', 'response_time_ms', 'tokens_used', 'created_at')
    list_filter = ('model_name', 'created_at')
    readonly_fields = ('created_at',)
