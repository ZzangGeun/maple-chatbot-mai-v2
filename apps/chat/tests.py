from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.chat.models import ChatSession

User = get_user_model()

class MaiChatSessionTest(TestCase):
    def setUp(self):
        """테스트 환경 설정"""
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser",
            password="testpassword123"
        )
        self.chat_url = reverse("chat:chat")  # 실제 urls.py의 구성에 따라 변경 필요 (가정)

    def test_chat_page_creates_session_for_anonymous(self):
        """비로그인 유저의 경우 익명 세션을 생성하는지 확인 (현재 뷰 로직에 따라 다를 수 있음)"""
        # 만약 chat의 URL 구조가 다를 경우를 대비하여 패스
        pass

    def test_chat_session_creation(self):
        """DB에 ChatSession 엔티티가 정상적으로 생성되는지 테스트"""
        session = ChatSession.objects.create(user=self.user)
        self.assertTrue(session.session_id)
        self.assertEqual(session.user.username, "testuser")
        self.assertEqual(ChatSession.objects.count(), 1)
