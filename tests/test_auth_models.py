# tests/test_auth_models.py
"""
auth 앱 모델 및 커스텀 QuerySet 테스트

UserProfile 모델과 UserProfileQuerySet의 커스텀 메서드를 테스트합니다.
"""

import pytest

from django.contrib.auth.models import User

from apps.auth.models import UserProfile


@pytest.mark.django_db(transaction=True)
class TestUserProfileModel:
    """UserProfile 모델 기본 동작 테스트."""

    @pytest.fixture(autouse=True)
    def _setup(self, db) -> None:
        """공통 테스트 데이터를 세팅합니다."""
        self.user = User.objects.create_user(
            username="model_test_user", password="password123"
        )
        self.profile = UserProfile.objects.create(
            user=self.user,
            maple_nickname="모델테스트",
            nexon_api_key="test_key_123",
        )

    def test_str_representation(self) -> None:
        """__str__이 '{username} - {nickname}' 형식을 반환해야 합니다."""
        expected = "model_test_user - 모델테스트"
        assert str(self.profile) == expected

    def test_one_to_one_relationship(self) -> None:
        """User와 UserProfile이 OneToOne 관계로 연결되어야 합니다."""
        assert self.user.profile == self.profile
        assert self.profile.user == self.user

    def test_maple_nickname_unique(self) -> None:
        """동일한 메이플 닉네임으로 프로필을 생성하면 예외가 발생해야 합니다."""
        another_user = User.objects.create_user(
            username="another_user", password="pass123"
        )
        with pytest.raises(Exception):
            UserProfile.objects.create(
                user=another_user,
                maple_nickname="모델테스트",  # 중복
                nexon_api_key="other_key",
            )

    def test_nexon_api_key_nullable(self) -> None:
        """nexon_api_key는 null을 허용해야 합니다."""
        user = User.objects.create_user(
            username="nullable_key_user", password="pass123"
        )
        profile = UserProfile.objects.create(
            user=user,
            maple_nickname="널키유저",
            nexon_api_key=None,
        )
        assert profile.nexon_api_key is None


@pytest.mark.django_db(transaction=True)
class TestUserProfileQuerySet:
    """UserProfileQuerySet 커스텀 메서드 테스트."""

    @pytest.fixture(autouse=True)
    def _setup(self, db) -> None:
        """공통 테스트 데이터를 세팅합니다."""
        self.user = User.objects.create_user(
            username="qs_test_user", password="password123"
        )
        self.profile = UserProfile.objects.create(
            user=self.user,
            maple_nickname="쿼리셋테스트",
            nexon_api_key="qs_key",
        )

    def test_exists_by_nickname_true(self) -> None:
        """존재하는 닉네임을 검사하면 True를 반환해야 합니다."""
        assert UserProfile.objects.exists_by_nickname("쿼리셋테스트") is True

    def test_exists_by_nickname_false(self) -> None:
        """존재하지 않는 닉네임을 검사하면 False를 반환해야 합니다."""
        assert UserProfile.objects.exists_by_nickname("없는닉네임") is False

    def test_get_by_user_or_none_found(self) -> None:
        """존재하는 사용자의 프로필을 정상 조회해야 합니다."""
        result = UserProfile.objects.get_by_user_or_none(self.user)
        assert result is not None
        assert result.maple_nickname == "쿼리셋테스트"

    def test_get_by_user_or_none_not_found(self) -> None:
        """프로필이 없는 사용자를 조회하면 None을 반환해야 합니다."""
        user_without_profile = User.objects.create_user(
            username="no_profile_user", password="pass123"
        )
        result = UserProfile.objects.get_by_user_or_none(user_without_profile)
        assert result is None
