from django.test import TestCase
from unittest.mock import patch

from apps.core.services import get_notice_list

class CoreServicesTest(TestCase):
    def setUp(self):
        """테스트 환경 설정"""
        self.mock_notice_data = {
            "notice_general": [{"title": "Test Notice 1", "notice_id": 1}],
            "notice_event": [],
            "notice_cashshop": [],
            "notice_update": []
        }

    @patch("apps.core.services.get_api_data")
    @patch("apps.core.services.load_notice_data_from_redis")
    def test_get_notice_list_calls_api_when_no_cache(self, mock_load_redis, mock_get_api_data):
        """캐시가 없을 때 API를 정상적으로 호출하는지 테스트"""
        mock_load_redis.return_value = {}  # 캐시 없음
        
        # get_api_data가 호출될 때 순서대로 반환할 값 설정
        mock_get_api_data.side_effect = [
            self.mock_notice_data["notice_general"],
            self.mock_notice_data["notice_event"],
            self.mock_notice_data["notice_cashshop"],
            self.mock_notice_data["notice_update"]
        ]
        
        # Redis 저장을 모킹
        with patch("apps.core.services.save_notice_data_to_redis") as mock_save_redis:
            result = get_notice_list()
            mock_save_redis.assert_called_once_with(self.mock_notice_data)

        self.assertEqual(mock_get_api_data.call_count, 4)
        self.assertEqual(result["notice_general"][0]["title"], "Test Notice 1")

    @patch("apps.core.services.load_notice_data_from_redis")
    def test_get_notice_list_uses_cache(self, mock_load_redis):
        """유효한 캐시가 있으면 API를 호출하지 않고 반환하는지 테스트"""
        mock_load_redis.return_value = self.mock_notice_data
        
        with patch("apps.core.services.get_api_data") as mock_get_api_data:
            result = get_notice_list()
            mock_get_api_data.assert_not_called()
            
        self.assertEqual(result, self.mock_notice_data)
