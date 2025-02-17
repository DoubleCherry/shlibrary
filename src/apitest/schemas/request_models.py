from typing import Dict, List
from pydantic import BaseModel, Field
from datetime import datetime


class UserConfig(BaseModel):
    """用户配置模型"""
    name: str = Field(..., description="用户名称")
    token: str = Field(..., description="用户token")

    def get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        return {"token": self.token}


class ApiConfig(BaseModel):
    """API配置模型"""
    base_url: str = Field(..., description="基础URL")
    floor_id: str = Field(..., description="楼层ID")
    library_id: str = Field(..., description="图书馆ID")
    seat_reservation_type: str = Field(..., description="座位预订类型")
    period_reservation_type: str = Field(..., description="时间段预订类型")
    reservation_interval: int = Field(..., description="预订请求间隔（毫秒）")


class LoggingConfig(BaseModel):
    """日志配置模型"""
    level: str = Field("INFO", description="日志级别")
    rotation: str = Field("1 day", description="日志轮转周期")
    retention: str = Field("7 days", description="日志保留时间")
    encoding: str = Field("utf-8", description="日志编码")


class ReservationConfig(BaseModel):
    """预订配置模型"""
    days_ahead: int = Field(..., description="预订提前天数")


class ReservationRequest(BaseModel):
    """预订请求模型"""
    users: List[UserConfig] = Field(..., description="用户配置列表")
    api: ApiConfig = Field(..., description="API配置")
    area_priority: List[str] = Field(..., description="区域优先级")
    logging: LoggingConfig = Field(..., description="日志配置")
    reservation: ReservationConfig = Field(..., description="预订配置")
    date: datetime = Field(
        default_factory=lambda: datetime.now(),
        description="预订日期，格式：YYYY-MM-DD"
    )


class TokenUser(BaseModel):
    """Token用户模型"""
    token: str = Field(..., description="用户token")


class SimpleReservationRequest(BaseModel):
    """简化版预订请求模型"""
    users: List[TokenUser] = Field(..., description="用户token列表")
    date: datetime = Field(..., description="预订日期时间") 