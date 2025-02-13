"""
配置文件
"""
from typing import Dict, List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置"""
    API_BASE_URL: str = "https://yuyue.library.sh.cn"
    FLOOR_ID: str = "4"
    LIBRARY_ID: str = "1"
    SEAT_RESERVATION_TYPE: str = "2"
    PERIOD_RESERVATION_TYPE: str = "14"
    
    # 区域优先级配置
    AREA_PRIORITY: List[str] = ["西", "东", "北", "南"]
    
    # 共享座位记录
    # 格式: {日期: {时间段: {区域: {桌号: [座位号]}}}}
    SHARED_SEAT_RECORDS: Dict[str, Dict[str, Dict[str, Dict[str, List[str]]]]] = {}
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings() 