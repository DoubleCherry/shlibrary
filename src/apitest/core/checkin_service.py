"""
签到服务
"""
from datetime import datetime, date
from typing import Dict, List, Optional
import httpx
from loguru import logger

from ..schemas.schedule_models import UserToken
from ..schemas.checkin_models import CheckinResult
from ..core.schedule_service import ScheduleService
from ..config.settings import settings


class CheckinService:
    """签到服务"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.schedule_service = ScheduleService()  # 这里会获取到已存在的实例
            self.base_url = settings.api_base_url
            self._initialized = True
        
    async def _get_reservation_list(self, token: str) -> List[Dict]:
        """获取预约列表"""
        headers = {
            "source": "1",
            "clientId": "1837178870",
            "token": token,
            "timestamp": str(int(datetime.now().timestamp() * 1000)),
        }
        
        all_content = []
        page = 1
        page_size = 50  # 增加每页大小
        
        while True:
            data = {
                "status": 0,  # 0表示未完结的预约
                "size": page_size,
                "page": page,
                "libraryId": 1  # 图书馆ID
            }
            
            logger.debug(f"获取预约列表: 第{page}页, 每页{page_size}条")
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/eastLibReservation/reservation/myReservationList",
                    headers=headers,
                    json=data
                )
                # logger.debug(f"预约列表接口响应: {response.text}")
                result = response.json()
                if result["resultStatus"]["code"] != 0:
                    error_msg = result["resultStatus"]["message"]
                    logger.error(f"获取预约列表失败: {error_msg}")
                    raise Exception(f"获取预约列表失败: {error_msg}")
                
                content = result["resultValue"]["content"]
                total_pages = result["resultValue"]["totalPages"]
                
                logger.debug(f"获取到第{page}页数据: {len(content)}条记录")
                all_content.extend(content)
                
                if page >= total_pages:
                    break
                    
                page += 1
        
        logger.debug(f"总共获取到{len(all_content)}条预约记录")
        return all_content
            
    async def _do_checkin(self, token: str, reservation_id: str) -> bool:
        """执行签到"""
        headers = {
            "source": "1",
            "clientId": "1837178870",
            "token": token,
            "timestamp": str(int(datetime.now().timestamp() * 1000)),
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/eastLibReservation/seatReservation/commonSignIn",
                headers=headers,
                params={"reservationId": reservation_id}
            )
            logger.debug(f"签到接口响应: {response.text}")
            result = response.json()
            if result["resultStatus"]["code"] != 0:
                error_msg = result["resultStatus"]["message"]
                logger.error(f"签到失败: {error_msg}")
                raise Exception(f"签到失败: {error_msg}")
            return True
            
    async def _do_checkout(self, token: str, reservation_id: str) -> bool:
        """执行签退"""
        headers = {
            "source": "1",
            "clientId": "1837178870",
            "token": token,
            "timestamp": str(int(datetime.now().timestamp() * 1000)),
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/eastLibReservation/seatReservation/signOut",
                headers=headers,
                params={"reservationId": reservation_id}
            )
            logger.debug(f"签退接口响应: {response.text}")
            result = response.json()
            if result["resultStatus"]["code"] != 0:
                error_msg = result["resultStatus"]["message"]
                logger.error(f"签退失败: {error_msg}")
                raise Exception(f"签退失败: {error_msg}")
            return True
            
    def _get_closest_reservation(self, reservations: List[Dict], for_checkout: bool = False) -> Optional[Dict]:
        """获取最接近当前时间的预约信息"""
        now = datetime.now()
        today = date.today().strftime("%Y-%m-%d")
        closest_reservation = None
        min_time_diff = float('inf')
        
        # 基础需要过滤的状态
        filtered_status = {
            "已取消",  # reservation_status_cancel
            "已失效",  # reservation_status_break_promise
            "自动签退"  # reservation_status_system_close
        }
        
        # 如果是签退操作，额外过滤"已签退"状态
        if for_checkout:
            filtered_status.add("已签退")  # reservation_status_sign_out
            logger.debug("签退操作：额外过滤'已签退'状态")
        
        logger.debug(f"当前时间: {now}, 今天日期: {today}")
        logger.debug(f"查找{'签退' if for_checkout else '签到'}预约")
        logger.debug(f"需要过滤的状态: {filtered_status}")
        
        for date_group in reservations:
            logger.debug(f"检查日期组: {date_group['reservationDate']}")
            if date_group["reservationDate"] != today:
                logger.debug(f"跳过非今天的日期: {date_group['reservationDate']}")
                continue
                
            for reservation in date_group["reservationList"]:
                # 跳过不可用状态的预约
                status_name = reservation["reservationStatusName"]
                if status_name in filtered_status:
                    logger.debug(f"跳过{status_name}的预约: ID={reservation['reservationId']}, 座位={reservation['seatNo']}, 时间={reservation['startTime']}-{reservation['endTime']}")
                    continue
                    
                logger.debug(f"检查预约: ID={reservation['reservationId']}, 状态={status_name}, 座位={reservation['seatNo']}, 时间={reservation['startTime']}-{reservation['endTime']}")
                    
                reservation_time = datetime.strptime(
                    f"{reservation['reservationDate']} {reservation['startTime']}",
                    "%Y-%m-%d %H:%M"
                )
                end_time = datetime.strptime(
                    f"{reservation['reservationDate']} {reservation['endTime']}",
                    "%Y-%m-%d %H:%M"
                )
                
                if for_checkout:
                    # 对于签退，我们需要找到包含当前时间或最接近当前时间的预约
                    logger.debug(
                        f"检查预约时段: {reservation['startTime']}-{reservation['endTime']}, "
                        f"预约ID: {reservation['reservationId']}, "
                        f"开始时间: {reservation_time}, "
                        f"结束时间: {end_time}, "
                        f"当前时间: {now}, "
                        f"状态: {status_name}, "
                        f"是否在时间段内: {reservation_time <= now <= end_time}"
                    )
                    if reservation_time <= now <= end_time:
                        logger.debug(f"找到当前时间段内的预约: {reservation['reservationId']}")
                        return reservation
                else:
                    # 对于签到，只考虑结束时间还未到的预约
                    if end_time <= now:
                        logger.debug(f"跳过已过结束时间的预约: ID={reservation['reservationId']}, 结束时间={end_time}")
                        continue
                        
                    time_diff = abs((reservation_time - now).total_seconds())
                    if time_diff < min_time_diff:
                        min_time_diff = time_diff
                        closest_reservation = reservation
                        logger.debug(f"更新最接近的预约: {reservation['reservationId']}, 时间差: {time_diff}秒")
                    
        if closest_reservation:
            logger.debug(f"返回最接近的预约: {closest_reservation['reservationId']}")
        else:
            logger.debug("没有找到符合条件的预约")
            
        return closest_reservation
            
    async def checkin(self) -> Dict[str, CheckinResult]:
        """执行签到"""
        results = {}
        tokens = self.schedule_service.get_user_tokens()
        
        for token_info in tokens:
            try:
                # 获取预约列表
                reservations = await self._get_reservation_list(token_info.token)
                
                # 获取最近的预约
                reservation = self._get_closest_reservation(reservations)
                if not reservation:
                    results[token_info.name] = CheckinResult(
                        user_name=token_info.name,
                        date=date.today().strftime("%Y-%m-%d"),
                        time_period="未知",
                        success=False,
                        message="签到失败",
                        error_reason="没有找到今天的预约"
                    )
                    continue
                
                # 执行签到
                await self._do_checkin(token_info.token, str(reservation["reservationId"]))
                
                # 记录成功结果
                results[token_info.name] = CheckinResult(
                    user_name=token_info.name,
                    date=reservation["reservationDate"],
                    time_period=f"{reservation['startTime']}-{reservation['endTime']}",
                    success=True,
                    message="签到成功"
                )
                
            except Exception as e:
                error_msg = str(e)
                logger.error(f"用户 {token_info.name} 签到时出错: {error_msg}")
                
                # 记录失败结果
                results[token_info.name] = CheckinResult(
                    user_name=token_info.name,
                    date=date.today().strftime("%Y-%m-%d"),
                    time_period="未知",
                    success=False,
                    message="签到失败",
                    error_reason=error_msg
                )
                
        return results
        
    async def checkout(self) -> Dict[str, CheckinResult]:
        """执行签退"""
        results = {}
        tokens = self.schedule_service.get_user_tokens()
        
        for token_info in tokens:
            try:
                # 获取预约列表
                reservations = await self._get_reservation_list(token_info.token)
                
                # 获取当前时间段的预约
                reservation = self._get_closest_reservation(reservations, for_checkout=True)
                if not reservation:
                    results[token_info.name] = CheckinResult(
                        user_name=token_info.name,
                        date=date.today().strftime("%Y-%m-%d"),
                        time_period="未知",
                        success=False,
                        message="签退失败",
                        error_reason="没有找到当前可签退的预约"
                    )
                    continue
                
                # 执行签退
                await self._do_checkout(token_info.token, str(reservation["reservationId"]))
                
                # 记录成功结果
                results[token_info.name] = CheckinResult(
                    user_name=token_info.name,
                    date=reservation["reservationDate"],
                    time_period=f"{reservation['startTime']}-{reservation['endTime']}",
                    success=True,
                    message="签退成功"
                )
                
            except Exception as e:
                error_msg = str(e)
                logger.error(f"用户 {token_info.name} 签退时出错: {error_msg}")
                
                # 记录失败结果
                results[token_info.name] = CheckinResult(
                    user_name=token_info.name,
                    date=date.today().strftime("%Y-%m-%d"),
                    time_period="未知",
                    success=False,
                    message="签退失败",
                    error_reason=error_msg
                )
                
        return results 