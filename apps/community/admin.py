from django.contrib import admin

from apps.community.models import CommunityPost


@admin.register(CommunityPost)
class CommunityPostAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "author", "views", "likes", "created_at")
    list_filter = ("category", "is_recommended")
    search_fields = ("title", "content", "author__username")
    readonly_fields = ("created_at", "updated_at")