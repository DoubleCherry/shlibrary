"""
配置文件
"""
from typing import Dict, List, Any
from pathlib import Path
import yaml
from pydantic_settings import BaseSettings
from pydantic import BaseModel


def load_yaml_config() -> Dict[str, Any]:
    """加载 YAML 配置文件"""
    config_path = Path(__file__).parent / "config.yaml"
    if not config_path.exists():
        return {}
    
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


class Settings(BaseSettings):
    """应用程序设置"""
    api_base_url: str = ""
    floor_id: str = ""
    library_id: str = ""
    seat_reservation_type: str = ""
    period_reservation_type: str = ""
    reservation_interval: int = 500
    area_priority: List[str] = []
    log_level: str = "INFO"
    log_rotation: str = "1 day"
    log_retention: str = "7 days"
    log_encoding: str = "utf-8"
    days_ahead: int = 6
    shared_seat_records: Dict[str, Dict[str, Dict[str, Dict[str, List[str]]]]] = {}
    
    def update_from_request(self, request: "ReservationRequest") -> None:
        """从请求更新配置
        
        Args:
            request: API请求对象
        """
        self.api_base_url = request.api.base_url
        self.floor_id = request.api.floor_id
        self.library_id = request.api.library_id
        self.seat_reservation_type = request.api.seat_reservation_type
        self.period_reservation_type = request.api.period_reservation_type
        self.reservation_interval = request.api.reservation_interval
        self.area_priority = request.area_priority
        self.log_level = request.logging.level
        self.log_rotation = request.logging.rotation
        self.log_retention = request.logging.retention
        self.log_encoding = request.logging.encoding
        self.days_ahead = request.reservation.days_ahead


# 加载 YAML 配置
yaml_config = load_yaml_config()

# 创建设置实例
settings = Settings()

# 从 YAML 配置更新设置
if yaml_config:
    if "api" in yaml_config:
        settings.api_base_url = yaml_config["api"]["base_url"].rstrip("/")
        settings.floor_id = yaml_config["api"]["floor_id"]
        settings.library_id = yaml_config["api"]["library_id"]
        settings.seat_reservation_type = yaml_config["api"]["seat_reservation_type"]
        settings.period_reservation_type = yaml_config["api"]["period_reservation_type"]
        settings.reservation_interval = yaml_config["api"]["reservation_interval"]
    
    if "area_priority" in yaml_config:
        settings.area_priority = yaml_config["area_priority"]
    
    if "logging" in yaml_config:
        settings.log_level = yaml_config["logging"]["level"]
        settings.log_rotation = yaml_config["logging"]["rotation"]
        settings.log_retention = yaml_config["logging"]["retention"]
        settings.log_encoding = yaml_config["logging"]["encoding"]
    
    if "reservation" in yaml_config:
        settings.days_ahead = yaml_config["reservation"]["days_ahead"]

# 避免循环导入
from ..schemas.request_models import ReservationRequest

# 预订提前天数
DAYS_AHEAD: int = 6

# 共享座位记录
# 格式: {日期: {时间段: {区域: {桌号: [座位号]}}}}
SHARED_SEAT_RECORDS: Dict[str, Dict[str, Dict[str, Dict[str, List[str]]]]] = {} 