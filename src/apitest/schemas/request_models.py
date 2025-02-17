from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from pathlib import Path
import yaml


def get_config_value(key_path: str, default_value: Any = None) -> Any:
    """从config.yaml获取配置值
    
    Args:
        key_path: 配置键路径，例如 "api.base_url" 或 "logging.level"
        default_value: 如果配置不存在时的默认值
        
    Returns:
        配置值或默认值
    """
    config_path = Path(__file__).parent.parent / "config" / "config.yaml"
    if not config_path.exists():
        return default_value
        
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            
        # 处理嵌套键
        keys = key_path.split(".")
        value = config
        for key in keys:
            if not isinstance(value, dict) or key not in value:
                return default_value
            value = value[key]
        return value
    except Exception:
        return default_value


class UserConfig(BaseModel):
    """用户配置模型"""
    name: str = Field(..., description="用户名称")
    token: str = Field(..., description="用户token")

    def get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        return {"token": self.token}


class ApiConfig(BaseModel):
    """API配置模型"""
    base_url: str = Field(
        default_factory=lambda: get_config_value("api.base_url", "https://yuyue.library.sh.cn"),
        description="基础URL"
    )
    floor_id: str = Field(
        default_factory=lambda: get_config_value("api.floor_id", "4"),
        description="楼层ID"
    )
    library_id: str = Field(
        default_factory=lambda: get_config_value("api.library_id", "1"),
        description="图书馆ID"
    )
    seat_reservation_type: str = Field(
        default_factory=lambda: get_config_value("api.seat_reservation_type", "2"),
        description="座位预订类型"
    )
    period_reservation_type: str = Field(
        default_factory=lambda: get_config_value("api.period_reservation_type", "14"),
        description="时间段预订类型"
    )
    reservation_interval: int = Field(
        default_factory=lambda: get_config_value("api.reservation_interval", 500),
        description="预订请求间隔（毫秒）"
    )


class ReservationConfig(BaseModel):
    """预订配置模型"""
    days_ahead: int = Field(
        default_factory=lambda: get_config_value("reservation.days_ahead", 6),
        description="预订提前天数"
    )


class ReservationRequest(BaseModel):
    """预订请求模型"""
    users: List[UserConfig] = Field(..., description="用户配置列表")
    api: ApiConfig = Field(default_factory=ApiConfig, description="API配置")
    area_priority: List[str] = Field(
        default_factory=lambda: get_config_value("area_priority", ["西", "东", "北", "南"]),
        description="区域优先级"
    )
    reservation: ReservationConfig = Field(default_factory=ReservationConfig, description="预订配置")
    target_date: Optional[datetime] = Field(
        default=None,
        description="目标预订日期，格式：YYYY-MM-DD，如果不提供则根据days_ahead自动计算"
    )


class TokenUser(BaseModel):
    """Token用户模型"""
    token: str = Field(..., description="用户token")


class SimpleReservationRequest(BaseModel):
    """简化版预订请求模型"""
    users: List[TokenUser] = Field(..., description="用户token列表")
    date: datetime = Field(..., description="预订日期时间") 