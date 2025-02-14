"""
配置文件
"""
from typing import Dict, List, Any
from pathlib import Path
import yaml
from pydantic_settings import BaseSettings


def load_yaml_config() -> Dict[str, Any]:
    """加载 YAML 配置文件"""
    config_path = Path(__file__).parent / "config.yaml"
    if not config_path.exists():
        return {}
    
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


class Settings(BaseSettings):
    """应用配置"""
    # API 基础配置
    API_BASE_URL: str = "https://yuyue.library.sh.cn"
    FLOOR_ID: str = "4"
    LIBRARY_ID: str = "1"
    SEAT_RESERVATION_TYPE: str = "2"
    PERIOD_RESERVATION_TYPE: str = "14"
    
    # 预订请求之间的时间间隔（毫秒）
    RESERVATION_INTERVAL: int = 500
    
    # 区域优先级配置
    AREA_PRIORITY: List[str] = ["西", "东", "北", "南"]
    
    # 预订提前天数
    DAYS_AHEAD: int = 6
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_ROTATION: str = "1 day"
    LOG_RETENTION: str = "7 days"
    LOG_ENCODING: str = "utf-8"
    
    # 共享座位记录
    # 格式: {日期: {时间段: {区域: {桌号: [座位号]}}}}
    SHARED_SEAT_RECORDS: Dict[str, Dict[str, Dict[str, Dict[str, List[str]]]]] = {}
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        
        @classmethod
        def parse_env_var(cls, field_name: str, raw_val: str) -> Any:
            if field_name == "API_BASE_URL":
                return raw_val.rstrip("/")  # 移除末尾的斜杠
            return raw_val


# 加载 YAML 配置
yaml_config = load_yaml_config()

# 创建设置实例
settings = Settings()

# 从 YAML 配置更新设置
if yaml_config:
    if "api" in yaml_config:
        settings.API_BASE_URL = yaml_config["api"]["base_url"].rstrip("/")
        settings.FLOOR_ID = yaml_config["api"]["floor_id"]
        settings.LIBRARY_ID = yaml_config["api"]["library_id"]
        settings.SEAT_RESERVATION_TYPE = yaml_config["api"]["seat_reservation_type"]
        settings.PERIOD_RESERVATION_TYPE = yaml_config["api"]["period_reservation_type"]
        settings.RESERVATION_INTERVAL = yaml_config["api"]["reservation_interval"]
    
    if "area_priority" in yaml_config:
        settings.AREA_PRIORITY = yaml_config["area_priority"]
    
    if "logging" in yaml_config:
        settings.LOG_LEVEL = yaml_config["logging"]["level"]
        settings.LOG_ROTATION = yaml_config["logging"]["rotation"]
        settings.LOG_RETENTION = yaml_config["logging"]["retention"]
        settings.LOG_ENCODING = yaml_config["logging"]["encoding"]
    
    if "reservation" in yaml_config:
        settings.DAYS_AHEAD = yaml_config["reservation"]["days_ahead"] 