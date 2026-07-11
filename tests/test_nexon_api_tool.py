from unittest.mock import AsyncMock

import pytest

from ai_server.graph.tools.nexon_api_tool import NexonAPIClient


@pytest.fixture
def client() -> NexonAPIClient:
    nexon_client = NexonAPIClient()
    nexon_client._api_key = "test-key"
    nexon_client._headers["x-nxopen-api-key"] = "test-key"
    return nexon_client


@pytest.mark.asyncio
async def test_get_ocid_uses_normalized_character_name(
    client: NexonAPIClient,
) -> None:
    client._get = AsyncMock(return_value={"ocid": "test-ocid"})

    result = await client.get_ocid("  테스트캐릭터  ")

    assert result == "test-ocid"
    client._get.assert_awaited_once_with(
        "/id",
        params={"character_name": "테스트캐릭터"},
    )


@pytest.mark.asyncio
async def test_get_character_summary_fetches_basic_and_stat(
    client: NexonAPIClient,
) -> None:
    client.get_ocid = AsyncMock(return_value="test-ocid")
    client.get_character_basic = AsyncMock(return_value={"character_level": 300})
    client.get_character_stat = AsyncMock(return_value={"final_stat": []})

    result = await client.get_character_summary("테스트캐릭터")

    assert result == {
        "basic": {"character_level": 300},
        "stat": {"final_stat": []},
    }
