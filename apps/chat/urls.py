# chat/urls.py
"""
챗봇 API URL 설정

중앙 urls.py에서 /api/v1/chat/ prefix로 include됩니다.

    GET    /api/v1/chat/rooms/                        — 대화방 목록 조회
    POST   /api/v1/chat/rooms/                        — 새 대화방 생성
    DELETE /api/v1/chat/rooms/<session_id>/           — 대화방 삭제
    GET    /api/v1/chat/rooms/<session_id>/messages/  — 메시지 목록 조회
    POST   /api/v1/chat/rooms/<session_id>/messages/  — 메시지 전송 (동기)
    POST   /api/v1/chat/rooms/<session_id>/stream/    — 메시지 전송 (SSE 스트리밍)
"""

from django.urls import path
from . import views

app_name = "chat"

urlpatterns = [
    # 설계서 chat-api.md 규격에 맞춘 rooms 매핑 (GET: 목록 조회, POST: 생성)
    path("rooms", views.rooms_dispatch, name="rooms_dispatch"),
    path("rooms/", views.rooms_dispatch, name="rooms_dispatch_slash"),
    
    # 특정 대화방 상세 (DELETE: 삭제)
    path("rooms/<str:session_id>", views.room_detail_dispatch, name="room_detail_dispatch"),
    path("rooms/<str:session_id>/", views.room_detail_dispatch, name="room_detail_dispatch_slash"),
    
    # 특정 대화방 메시지 (GET: 조회, POST: 전송)
    path("rooms/<str:session_id>/messages", views.messages_dispatch, name="messages_dispatch"),
    path("rooms/<str:session_id>/messages/", views.messages_dispatch, name="messages_dispatch_slash"),
    
    # 스트리밍 SSE 엔드포인트 유지
    path("rooms/<str:session_id>/stream", views.stream_message, name="stream_message"),
    path("rooms/<str:session_id>/stream/", views.stream_message, name="stream_message_slash"),
]

