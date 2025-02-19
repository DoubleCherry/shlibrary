"""
定时预订API端点
"""
from typing import List
from fastapi import APIRouter, HTTPException
from loguru import logger

from ..core.schedule_service import ScheduleService
from ..schemas.schedule_models import (
    ScheduleConfig,
    ScheduleStatus,
    ScheduleResponse,
    UserToken
)

router = APIRouter(
    prefix="/schedule",
    tags=["schedule"]
)

schedule_service = ScheduleService()

@router.get(
    "/status",
    response_model=ScheduleResponse,
    summary="获取定时任务状态",
    description="获取定时预订任务的当前状态，包括配置信息、运行状态和用户token列表"
)
async def get_schedule_status():
    """获取定时任务状态"""
    return ScheduleResponse(
        config=schedule_service.config,
        status=schedule_service.get_status(),
        user_tokens=schedule_service.get_user_tokens()
    )

@router.post(
    "/config",
    response_model=ScheduleResponse,
    summary="更新定时任务配置",
    description="更新定时预订任务的配置信息，包括cron表达式和是否启用"
)
async def update_schedule_config(config: ScheduleConfig):
    """更新定时任务配置"""
    try:
        schedule_service.config = config
        if config.enabled:
            await schedule_service.start()
        else:
            await schedule_service.stop()
        return await get_schedule_status()
    except Exception as e:
        logger.error(f"更新定时任务配置失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post(
    "/start",
    response_model=ScheduleResponse,
    summary="启动定时任务",
    description="启动定时预订任务"
)
async def start_schedule():
    """启动定时任务"""
    try:
        schedule_service.config.enabled = True
        await schedule_service.start()
        return await get_schedule_status()
    except Exception as e:
        logger.error(f"启动定时任务失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post(
    "/stop",
    response_model=ScheduleResponse,
    summary="停止定时任务",
    description="停止定时预订任务"
)
async def stop_schedule():
    """停止定时任务"""
    try:
        schedule_service.config.enabled = False
        await schedule_service.stop()
        return await get_schedule_status()
    except Exception as e:
        logger.error(f"停止定时任务失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get(
    "/tokens",
    response_model=List[UserToken],
    summary="获取用户token列表",
    description="获取所有已保存的用户token信息"
)
async def get_user_tokens():
    """获取用户token列表"""
    return schedule_service.get_user_tokens()

@router.post(
    "/tokens",
    response_model=List[UserToken],
    summary="更新用户token列表",
    description="更新整个用户token列表"
)
async def update_user_tokens(tokens: List[UserToken]):
    """更新用户token列表"""
    try:
        schedule_service.update_user_tokens(tokens)
        return schedule_service.get_user_tokens()
    except Exception as e:
        logger.error(f"更新用户token列表失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post(
    "/tokens/add",
    response_model=List[UserToken],
    summary="添加用户token",
    description="添加或更新单个用户的token信息"
)
async def add_user_token(token: UserToken):
    """添加用户token"""
    try:
        schedule_service.add_user_token(token)
        return schedule_service.get_user_tokens()
    except Exception as e:
        logger.error(f"添加用户token失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.delete(
    "/tokens/{name}",
    response_model=List[UserToken],
    summary="删除用户token",
    description="删除指定用户的token信息"
)
async def remove_user_token(name: str):
    """删除用户token"""
    try:
        schedule_service.remove_user_token(name)
        return schedule_service.get_user_tokens()
    except Exception as e:
        logger.error(f"删除用户token失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e)) 