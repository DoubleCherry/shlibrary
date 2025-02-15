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
        
        # 初始化日志
        logger.add(
            "logs/app.log",
            rotation=request.logging.rotation,
            retention=request.logging.retention,
            level=request.logging.level,
            encoding=request.logging.encoding
        )
        
        results: List[ReservationResult] = []
        formatted_date = request.date.strftime("%Y-%m-%d")
        
        # 为每个用户进行预订
        for user in request.users:
            user_config = {
                "name": user.name,
                "headers": user.headers,
                "date": formatted_date
            }
            
            # 创建预订实例并执行预订
            reservation = SeatReservation(user_config)
            user_results = reservation.make_reservation()
            results.extend(user_results)
            
            # 记录预订结果
            for result in user_results:
                logger.info(
                    f"用户: {user.name}, "
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