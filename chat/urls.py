# chat/urls.py
"""
챗봇 API URL 설정

중앙 urls.py에서 /api/chat/ prefix로 include됩니다.

    GET    /api/chat/sessions/                        — 세션 목록 조회
    POST   /api/chat/sessions/create/                 — 새 세션 생성
    GET    /api/chat/sessions/<session_id>/messages/  — 메시지 목록 조회
    POST   /api/chat/sessions/<session_id>/send/      — 메시지 전송 (동기)
    POST   /api/chat/sessions/<session_id>/stream/    — 메시지 전송 (SSE 스트리밍)
    DELETE /api/chat/sessions/<session_id>/delete/    — 세션 삭제
"""

from django.urls import path
from . import views

app_name = "chat"

urlpatterns = [
    path("sessions/", views.get_sessions, name="get_sessions"),
    path("sessions/create/", views.create_session, name="create_session"),
    path("sessions/<str:session_id>/messages/", views.get_messages, name="get_messages"),
    path("sessions/<str:session_id>/send/", views.send_message, name="send_message"),
    path("sessions/<str:session_id>/stream/", views.stream_message, name="stream_message"),
    path("sessions/<str:session_id>/delete/", views.delete_session, name="delete_session"),
]
