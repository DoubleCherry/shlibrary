"""
签到签退API端点
"""
from typing import Dict
from fastapi import APIRouter
from loguru import logger

from ..core.checkin_service import CheckinService
from ..schemas.checkin_models import CheckinResult

router = APIRouter(
    prefix="/checkin",
    tags=["checkin"]
)

checkin_service = CheckinService()

@router.post(
    "/in",
    response_model=Dict[str, CheckinResult],
    summary="执行签到",
    description="为所有已配置token的用户执行签到操作，返回每个用户的签到结果"
)
async def do_checkin():
    """执行签到"""
    try:
        return await checkin_service.checkin()
    except Exception as e:
        logger.error(f"执行签到失败: {str(e)}")
        raise

@router.post(
    "/out",
    response_model=Dict[str, CheckinResult],
    summary="执行签退",
    description="为所有已配置token的用户执行签退操作，返回每个用户的签退结果"
)
async def do_checkout():
    """执行签退"""
    try:
        return await checkin_service.checkout()
    except Exception as e:
        logger.error(f"执行签退失败: {str(e)}")
        raise 