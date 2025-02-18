from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException
from loguru import logger
from datetime import datetime

from ..schemas.request_models import ReservationRequest
from ..core.seat_reservation import SeatReservation, ReservationResult
from ..config.settings import settings
from ..utils.helpers import get_target_date

router = APIRouter()


@router.post("/reserve", response_model=Dict[str, Any])
async def reserve_seat(request: ReservationRequest) -> Dict[str, Any]:
    """
    座位预订接口
    
    Args:
        request: 预订请求参数
        
    Returns:
        Dict[str, Any]: {
            "success": bool,  # 是否成功
            "message": str,   # 提示信息
            "results": List[ReservationResult]  # 预订结果列表
        }
        
    Raises:
        HTTPException: 当预订过程出现错误时抛出
    """
    try:
        # 更新全局设置
        settings.update_from_request(request)
        
        # 获取目标日期
        target_date = (
            request.target_date.strftime("%Y-%m-%d")
            if request.target_date
            else get_target_date()
        )
        
        # 准备所有用户的配置
        users_config = request.users
        
        if not users_config:
            logger.error("请求中没有找到用户信息")
            return {
                "success": False,
                "message": "请求中没有找到用户信息",
                "results": []
            }
            
        # 创建预订实例并执行多人预订
        reservation = SeatReservation({"token": users_config[0].token})
        results = reservation.make_reservation(users_config)
        
        # 如果结果为空，说明没有找到可用时间段或座位
        if not results:
            current_time = datetime.now().strftime("%H:%M:%S")
            return {
                "success": False,
                "message": f"无可用预订资源 - 目标日期: {target_date}, 当前时间: {current_time}",
                "results": []
            }
        
        # 记录预订结果
        periods_per_user = len(results) // len(users_config)
        for i, result in enumerate(results):
            user_index = i // periods_per_user
            user_name = users_config[user_index].name
            logger.info(
                f"用户: {user_name}, "
                f"日期: {target_date}, "
                f"时间段: {result['time_period']}, "
                f"区域: {result['area']}, "
                f"座位: {result['seat']}, "
                f"状态: {result['status']}"
            )
        
        return {
            "success": True,
            "message": "预订请求处理完成",
            "results": results
        }
    
    except Exception as e:
        error_msg = str(e)
        logger.error(f"预订过程出错: {error_msg}")
        return {
            "success": False,
            "message": f"预订过程出错: {error_msg}",
            "results": []
        } 