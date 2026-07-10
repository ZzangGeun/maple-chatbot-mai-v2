import json

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.auth.models import UserProfile
from apps.community.models import CommunityPost


class CommunityPostApiTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="community-user",
            password="testpassword123",
        )
        UserProfile.objects.create(
            user=self.user,
            maple_nickname="메이플유저",
        )
        self.url = reverse("community:post_list")

    def test_list_posts(self):
        CommunityPost.objects.create(
            author=self.user,
            category=CommunityPost.Category.GUIDE,
            title="공략 게시글",
            content="공략 내용",
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        post = response.json()["posts"][0]
        self.assertEqual(post["title"], "공략 게시글")
        self.assertEqual(post["author"], "메이플유저")
        self.assertEqual(post["category"], "guide")

    def test_authenticated_user_can_create_post(self):
        self.client.force_login(self.user)

        response = self.client.post(
            self.url,
            data=json.dumps({"title": "새 글", "content": "새 내용", "category": "free"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(CommunityPost.objects.get().author, self.user)

    def test_anonymous_user_cannot_create_post(self):
        response = self.client.post(
            self.url,
            data=json.dumps({"title": "새 글", "content": "새 내용", "category": "free"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 401)