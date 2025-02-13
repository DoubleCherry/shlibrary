from typing import Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict
from collections import defaultdict
from enum import Enum
from datetime import datetime


class AreaPriority(str, Enum):
    """区域优先级枚举"""
    WEST = "西"
    EAST = "东"
    NORTH = "北"
    SOUTH = "南"


class UserHeaders(BaseModel):
    """用户请求头配置"""
    model_config = ConfigDict(populate_by_name=True)
    
    client_id: str = Field(alias="clientId")
    source: str
    access_token: str = Field(alias="accessToken")
    sign: str
    timestamp: str
    cookie: str = Field(alias="Cookie")


class UserConfig(BaseModel):
    """用户配置"""
    name: str
    headers: UserHeaders


class APIConfig(BaseModel):
    """API相关配置"""
    base_url: str = "https://yuyue.library.sh.cn"
    floor_id: str = "4"
    library_id: str = "1"
    seat_reservation_type: str = "2"  # 预订座位时使用
    period_reservation_type: str = "14"  # 获取时间段时使用


class Config(BaseModel):
    """全局配置"""
    model_config = ConfigDict(use_enum_values=True)
    
    users: List[UserConfig] = []
    api: APIConfig = APIConfig()
    area_priority: List[AreaPriority] = [
        AreaPriority.WEST,
        AreaPriority.EAST,
        AreaPriority.NORTH,
        AreaPriority.SOUTH
    ]
    days_ahead: int = 6  # T+6天预约


# 初始化默认配置
config = Config(
    users=[
        UserConfig(
            name="用户1",
            headers={
                "clientId": "1837178870",
                "source": "1",
                "accessToken": "7494e9151c19573946183eb1b0f73f03",
                "sign": "6b103ec61bf68c170c7df990a61c51f230f66eb42ae0b79be666ff086d1c2807",
                "timestamp": "1739425432890",
                "Cookie": "Hm_lpvt_5baf77ff3c256db2d753d59a23540a6b=1739352030; Hm_lvt_5baf77ff3c256db2d753d59a23540a6b=1739340195,1739352030"
            }
        )
    ]
)

# 共享的座位记录类型定义
SeatRecordType = Dict[str, Dict[str, Dict[str, Dict[str, List[str]]]]]

# 共享的座位记录
# 格式: {日期: {时间段: {区域: {桌号: [已预订的座位号]}}}}
SHARED_SEAT_RECORDS: SeatRecordType = defaultdict(
    lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
) 