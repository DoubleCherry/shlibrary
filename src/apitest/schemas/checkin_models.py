"""
签到签退相关模型
"""
from typing import Optional
from pydantic import BaseModel, Field


class CheckinResult(BaseModel):
    """签到/签退结果模型"""
    user_name: str = Field(..., description="用户姓名")
    date: str = Field(..., description="预约日期")
    time_period: str = Field(..., description="时间段")
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="结果信息")
    error_reason: Optional[str] = Field(None, description="失败原因") 