"""
座位捡漏API端点
"""
from datetime import date
from typing import List

from fastapi import APIRouter, HTTPException
from loguru import logger

from ..core.snipe_service import SnipeService
from ..schemas.snipe_models import (
    SnipeTask,
    CreateSnipeTaskRequest,
    StopSnipeTaskRequest,
    SnipeTaskResponse,
    TaskInfo
)


router = APIRouter(
    prefix="/snipe", 
    tags=["snipe"]
)
snipe_service = SnipeService()


@router.post(
    "/tasks", 
    response_model=SnipeTaskResponse,
    summary="创建捡漏任务",
    description="创建一个或多个捡漏任务，支持同一天为多个用户创建任务"
)
async def create_snipe_tasks(request: CreateSnipeTaskRequest):
    """
    创建捡漏任务
    
    - 支持同时创建多个任务
    - 如果任务已存在(相同用户+日期)，则返回已存在的任务
    - 任务创建后会立即开始执行捡漏
    """
    tasks = []
    for task_info in request.tasks:
        try:
            target_date = date.fromisoformat(task_info.target_date)
            logger.debug(
                f"日期转换: "
                f"输入字符串={task_info.target_date}, "
                f"转换结果={target_date} ({type(target_date)})"
            )
            
            task = await snipe_service.create_task(
                user_token=task_info.user_token,
                user_name=task_info.user_name,
                target_date=target_date
            )
            tasks.append(task)
        except ValueError as e:
            logger.error(f"日期转换或创建任务失败: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))
    return SnipeTaskResponse(tasks=tasks)


@router.get(
    "/tasks", 
    response_model=SnipeTaskResponse,
    summary="查询活动中的捡漏任务",
    description="获取所有正在进行中的捡漏任务列表"
)
async def get_active_tasks():
    """
    获取所有活动中的捡漏任务
    
    - 只返回状态为 active 的任务
    - 不包含已完成或已终止的任务
    """
    tasks = snipe_service.get_active_tasks()
    return SnipeTaskResponse(tasks=tasks)


@router.post(
    "/tasks/stop", 
    response_model=SnipeTaskResponse,
    summary="停止捡漏任务",
    description="停止一个或多个捡漏任务"
)
async def stop_snipe_tasks(request: StopSnipeTaskRequest):
    """
    停止指定的捡漏任务
    
    - 支持同时停止多个任务
    - 任务停止后状态变为 terminated
    - 已完成的任务不会被影响
    """
    tasks = await snipe_service.stop_tasks(request.task_ids)
    if not tasks:
        raise HTTPException(status_code=404, detail="未找到指定的任务")
    return SnipeTaskResponse(tasks=tasks)