"""
座位预订单元测试
"""
import pytest
from unittest.mock import Mock, patch
from src.apitest.core.seat_reservation import SeatReservation


@pytest.fixture
def user_config():
    """用户配置fixture"""
    return {
        "headers": {"Authorization": "test_token"},
        "name": "test_user"
    }


@pytest.fixture
def seat_reservation(user_config):
    """座位预订实例fixture"""
    return SeatReservation(user_config)


def test_get_areas(seat_reservation):
    """测试获取区域信息"""
    with patch("requests.get") as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [
                {"id": "1", "areaName": "南"},
                {"id": "2", "areaName": "北"}
            ]
        }
        mock_get.return_value = mock_response
        
        areas = seat_reservation.get_areas()
        assert len(areas) == 2
        assert areas[0]["areaName"] == "南"
        assert areas[1]["areaName"] == "北"


def test_get_available_periods(seat_reservation):
    """测试获取可用时间段"""
    with patch("requests.get") as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = {
            "resultValue": [
                {
                    "beginTime": "08:00",
                    "endTime": "12:00",
                    "quotaVo": {"remaining": 10}
                }
            ]
        }
        mock_get.return_value = mock_response
        
        periods = seat_reservation.get_available_periods("2024-02-13")
        assert len(periods) == 1
        assert periods[0]["startTime"] == "08:00"
        assert periods[0]["endTime"] == "12:00"
        assert periods[0]["remaining"] == 10


def test_find_best_seat(seat_reservation):
    """测试找到最佳座位"""
    seats = [
        {
            "id": 1,
            "seatRow": "1排",
            "seatNo": "1",
            "seatStatus": 3
        },
        {
            "id": 2,
            "seatRow": "1排",
            "seatNo": "2",
            "seatStatus": 3
        }
    ]
    
    best_seat = seat_reservation.find_best_seat(
        seats,
        "南",
        "2024-02-13",
        "08:00-12:00"
    )
    assert best_seat is not None
    assert best_seat["id"] == 2  # 应该选择靠右的座位 