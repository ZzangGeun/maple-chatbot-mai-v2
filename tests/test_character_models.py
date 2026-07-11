# tests/test_character_models.py
"""
character 앱 모델 및 커스텀 QuerySet 테스트

CharacterLink 모델과 CharacterLinkQuerySet의 비동기 메서드를 테스트합니다.
"""

import pytest

from django.contrib.auth.models import User
from django.utils import timezone

from apps.character.models import CharacterLink


@pytest.mark.django_db(transaction=True)
class TestCharacterLinkModel:
    """CharacterLink 모델 기본 동작 테스트."""

    @pytest.fixture(autouse=True)
    def _setup(self, db) -> None:
        self.user = User.objects.create_user(
            username="char_model_user", password="password123"
        )

    def test_create_character_link(self) -> None:
        """캐릭터 연동 레코드가 정상 생성되어야 합니다."""
        link = CharacterLink.objects.create(
            user=self.user,
            character_name="테스트캐릭터",
            ocid="test_ocid_123",
            world_name="스카니아",
            is_main=True,
            verified_at=timezone.now(),
        )
        assert link.character_name == "테스트캐릭터"
        assert link.world_name == "스카니아"
        assert link.is_main is True
        assert link.ocid == "test_ocid_123"

    def test_str_representation(self) -> None:
        """__str__이 '캐릭터명 (월드) - 유저명' 형식을 반환해야 합니다."""
        link = CharacterLink.objects.create(
            user=self.user,
            character_name="스트링테스트",
            ocid="ocid_str_test",
            world_name="루나",
        )
        expected = "스트링테스트 (루나) - char_model_user"
        assert str(link) == expected

    def test_unique_together_constraint(self) -> None:
        """동일 사용자-캐릭터명 조합은 중복 생성 불가해야 합니다."""
        CharacterLink.objects.create(
            user=self.user,
            character_name="유니크캐릭",
            ocid="ocid_unique_1",
            world_name="루나",
        )
        with pytest.raises(Exception):
            CharacterLink.objects.create(
                user=self.user,
                character_name="유니크캐릭",  # 중복
                ocid="ocid_unique_2",
                world_name="루나",
            )

    def test_ocid_unique_constraint(self) -> None:
        """OCID는 전역적으로 유니크해야 합니다."""
        CharacterLink.objects.create(
            user=self.user,
            character_name="캐릭A",
            ocid="same_ocid",
            world_name="루나",
        )
        another_user = User.objects.create_user(
            username="another_char_user", password="pass123"
        )
        with pytest.raises(Exception):
            CharacterLink.objects.create(
                user=another_user,
                character_name="캐릭B",
                ocid="same_ocid",  # 중복 OCID
                world_name="스카니아",
            )

    def test_cascade_delete_with_user(self) -> None:
        """사용자 삭제 시 연동된 캐릭터 링크도 삭제되어야 합니다."""
        CharacterLink.objects.create(
            user=self.user,
            character_name="삭제테스트",
            ocid="ocid_del",
            world_name="루나",
        )
        assert CharacterLink.objects.count() == 1
        self.user.delete()
        assert CharacterLink.objects.count() == 0

    def test_multiple_characters_per_user(self) -> None:
        """한 사용자가 여러 캐릭터를 연동할 수 있어야 합니다."""
        CharacterLink.objects.create(
            user=self.user,
            character_name="캐릭터1",
            ocid="ocid_multi_1",
            world_name="루나",
            is_main=True,
        )
        CharacterLink.objects.create(
            user=self.user,
            character_name="캐릭터2",
            ocid="ocid_multi_2",
            world_name="스카니아",
            is_main=False,
        )
        assert CharacterLink.objects.filter(user=self.user).count() == 2


@pytest.mark.django_db(transaction=True)
class TestCharacterLinkQuerySet:
    """CharacterLinkQuerySet 비동기 커스텀 메서드 테스트."""

    @pytest.fixture(autouse=True)
    def _setup(self, db) -> None:
        self.user = User.objects.create_user(
            username="qs_char_user", password="password123"
        )

    @pytest.mark.asyncio
    async def test_is_first_link_true(self) -> None:
        """연동된 캐릭터가 없는 사용자는 True를 반환해야 합니다."""
        result = await CharacterLink.objects.is_first_link_async(self.user)
        assert result is True

    @pytest.mark.asyncio
    async def test_is_first_link_false(self) -> None:
        """이미 연동된 캐릭터가 있으면 False를 반환해야 합니다."""
        await CharacterLink.objects.acreate(
            user=self.user,
            character_name="기존캐릭",
            ocid="existing_ocid",
            world_name="루나",
        )
        result = await CharacterLink.objects.is_first_link_async(self.user)
        assert result is False

    @pytest.mark.asyncio
    async def test_update_or_create_link_create(self) -> None:
        """새 캐릭터 연동 시 레코드가 생성되어야 합니다."""
        link, created = await CharacterLink.objects.update_or_create_link_async(
            user=self.user,
            character_name="신규연동",
            ocid="new_ocid",
            world_name="스카니아",
            is_main=True,
        )
        assert created is True
        assert link.character_name == "신규연동"
        assert link.is_main is True
        assert link.verified_at is not None

    @pytest.mark.asyncio
    async def test_update_or_create_link_update(self) -> None:
        """기존 캐릭터 연동을 갱신 시 created=False를 반환해야 합니다."""
        # 먼저 생성
        await CharacterLink.objects.acreate(
            user=self.user,
            character_name="갱신대상",
            ocid="old_ocid",
            world_name="루나",
        )
        # 갱신
        link, created = await CharacterLink.objects.update_or_create_link_async(
            user=self.user,
            character_name="갱신대상",
            ocid="updated_ocid",
            world_name="스카니아",
            is_main=False,
        )
        assert created is False
        assert link.ocid == "updated_ocid"
        assert link.world_name == "스카니아"
