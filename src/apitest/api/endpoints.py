from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException
from loguru import logger

from ..schemas.request_models import ReservationRequest
from ..core.seat_reservation import SeatReservation, ReservationResult
from ..config.settings import settings

router = APIRouter()


@router.post("/reserve", response_model=List[Dict[str, Any]])
async def reserve_seat(request: ReservationRequest) -> List[ReservationResult]:
    """
    座位预订接口
    
    Args:
        request: 预订请求参数
        
    Returns:
        List[ReservationResult]: 预订结果列表
        
    Raises:
        HTTPException: 当预订过程出现错误时抛出
    """
    try:
        # 更新全局设置
        settings.update_from_request(request)
        
        formatted_date = request.date.strftime("%Y-%m-%d")
        
        # 准备所有用户的配置
        users_config = [
            {
                "name": user.name,
                "headers": user.headers,
                "date": formatted_date
            }
            for user in request.users
        ]
        
        if not users_config:
            logger.error("请求中没有找到用户信息")
            raise HTTPException(status_code=400, detail="请求中没有找到用户信息")
            
        # 创建预订实例并执行多人预订
        reservation = SeatReservation({"headers": users_config[0]["headers"]})
        results = reservation.make_reservation(users_config)
        
        # 记录预订结果
        for i, result in enumerate(results):
            user_name = users_config[i % len(users_config)]["name"]
            logger.info(
                f"用户: {user_name}, "
                f"日期: {formatted_date}, "
                f"时间段: {result['time_period']}, "
                f"区域: {result['area']}, "
                f"座位: {result['seat']}, "
                f"状态: {result['status']}"
            )
        
        return results
    
    except Exception as e:
        logger.error(f"预订过程出错: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 