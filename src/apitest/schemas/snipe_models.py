from datetime import date
from enum import Enum
from typing import List
from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    """捡漏任务状态"""
    ACTIVE = "active"  # 进行中
    TERMINATED = "terminated"  # 已终止
    COMPLETED = "completed"  # 已完成


class TaskInfo(BaseModel):
    """任务信息"""
    user_token: str = Field(
        ..., 
        description="用户token",
        example="c531acb567c7daa10a4c8cfec83b72da"
    )
    user_name: str = Field(
        ..., 
        description="用户姓名",
        example="张三"
    )
    target_date: str = Field(
        ..., 
        description="目标日期，格式：YYYY-MM-DD",
        example="2024-02-15"
    )


class SnipeTask(BaseModel):
    """捡漏任务模型"""
    id: str = Field(
        ..., 
        description="任务ID",
        example="550e8400-e29b-41d4-a716-446655440000"
    )
    user_token: str = Field(
        ..., 
        description="用户token",
        example="c531acb567c7daa10a4c8cfec83b72da"
    )
    user_name: str = Field(
        ..., 
        description="用户姓名",
        example="张三"
    )
    target_date: date = Field(
        ..., 
        description="目标日期"
    )
    status: TaskStatus = Field(
        default=TaskStatus.ACTIVE, 
        description="任务状态：active(进行中)、terminated(已终止)、completed(已完成)"
    )
    created_at: date = Field(
        ..., 
        description="创建时间"
    )


class CreateSnipeTaskRequest(BaseModel):
    """创建捡漏任务请求"""
    tasks: List[TaskInfo] = Field(
        ..., 
        description="任务列表",
        example=[
            {
                "user_token": "c531acb567c7daa10a4c8cfec83b72da",
                "user_name": "张三",
                "target_date": "2024-02-15"
            },
            {
                "user_token": "another_token",
                "user_name": "李四",
                "target_date": "2024-02-15"
            }
        ]
    )


class StopSnipeTaskRequest(BaseModel):
    """停止捡漏任务请求"""
    task_ids: List[str] = Field(
        ..., 
        description="要停止的任务ID列表",
        example=[
            "550e8400-e29b-41d4-a716-446655440000",
            "550e8400-e29b-41d4-a716-446655440001"
        ]
    )


class SnipeTaskResponse(BaseModel):
    """捡漏任务响应"""
    tasks: List[SnipeTask] = Field(..., description="任务列表")