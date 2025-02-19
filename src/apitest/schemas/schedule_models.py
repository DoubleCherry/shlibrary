from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

class UserToken(BaseModel):
    """用户Token信息"""
    name: str = Field(..., description="用户姓名", example="张三")
    token: str = Field(..., description="用户token", example="your_token_here")

class ScheduleConfig(BaseModel):
    """定时任务配置"""
    cron: str = Field(
        default="0-5 12 * * *",  # 每天12:00至12:05内每分钟执行一次
        description="Cron表达式，格式：分 时 日 月 星期",
        example="0 8 * * *"  # 每天早上8点
    )
    enabled: bool = Field(
        default=True,
        description="是否启用定时任务"
    )

class ScheduleStatus(BaseModel):
    """定时任务状态"""
    is_running: bool = Field(..., description="是否正在运行")
    next_run_time: Optional[datetime] = Field(None, description="下次运行时间")
    last_run_time: Optional[datetime] = Field(None, description="上次运行时间")
    last_run_result: Optional[str] = Field(None, description="上次运行结果")

class ScheduleResponse(BaseModel):
    """定时任务响应"""
    config: ScheduleConfig
    status: ScheduleStatus
    user_tokens: List[UserToken] 