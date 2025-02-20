"""
座位预订核心模块
"""
from typing import Dict, List, Optional, Any, TypedDict, Set
import requests
from loguru import logger
import time

from ..config.settings import settings
from ..utils.helpers import (
    get_target_date,
    is_odd_table,
    get_preferred_seats,
    update_request_headers
)


class SeatInfo(TypedDict):
    """座位信息类型"""
    seatId: int
    seatNo: str
    seat: str
    areaId: int
    areaName: str
    seatX: float
    seatY: float
    seatWidth: int
    seatHeight: int
    floorId: int
    floorName: str
    seatStatus: int
    seatStatusDesc: Optional[str]
    seatRow: str
    seatRowColumn: str


class PeriodInfo(TypedDict):
    """时间段信息类型"""
    startTime: str
    endTime: str
    remaining: int


class ReservationResult(TypedDict):
    """预订结果类型"""
    time_period: str
    area: str
    seat: str
    status: str
    user_name: str


class SeatReservation:
    """座位预订类"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化座位预订实例
        
        Args:
            config: 预订配置，包含 token
        """
        self.config = config
        self.base_url: str = settings.api_base_url
        self.headers = self._get_headers()
        
    def _get_headers(self):
        """获取请求头"""
        return {"token": self.config["token"]}

    def get_areas(self) -> List[Dict[str, Any]]:
        """获取所有区域信息"""
        url = f"{self.base_url}/eastLibReservation/area"
        params = {"floorId": settings.floor_id}
        headers = update_request_headers(self.headers)
        response = requests.get(url, headers=headers, params=params)
        logger.info(f"获取区域响应: {response.text}")
        data = response.json()
        areas = data.get("resultValue", [])
        
        # 按照优先级排序区域
        def get_area_priority(area: Dict[str, Any]) -> int:
            try:
                # 去掉区域名称中的"区"字后再匹配优先级
                area_name = area["areaName"].replace("区", "")
                return settings.area_priority.index(area_name)
            except ValueError:
                return len(settings.area_priority)
        
        return sorted(areas, key=get_area_priority)

    def get_available_periods(self, date: str) -> List[PeriodInfo]:
        """
        获取指定日期的可用时间段
        
        Args:
            date: 日期字符串，格式为 YYYY-MM-DD
            
        Returns:
            可用时间段列表，每个时间段包含开始时间、结束时间和剩余座位数
        """
        url = f"{self.base_url}/eastLibReservation/api/period"
        params = {
            "date": date,
            "reservationType": settings.period_reservation_type,
            "libraryId": settings.library_id
        }
        
        # 更新请求头
        headers = update_request_headers(self.headers)
        
        logger.info(f"请求时间段信息: URL={url}, Headers={headers}, Params={params}")
        
        try:
            response = requests.get(url, headers=headers, params=params)
            logger.info(f"状态码: {response.status_code}")
            logger.info(f"响应头: {response.headers}")
            logger.info(f"响应内容: {response.text}")
            
            if response.status_code != 200:
                logger.error(f"请求失败: {response.status_code} - {response.text}")
                return []
                
            data = response.json()
            periods = data.get("resultValue", [])
            if not periods:
                logger.warning(f"没有找到任何时间段")
                return []
                
            available_periods = [p for p in periods if p.get("quotaVo", {}).get("remaining", 0) > 0]
            logger.info(f"找到 {len(periods)} 个时间段，其中可用的有 {len(available_periods)} 个")
            
            return [{
                "startTime": p["beginTime"],
                "endTime": p["endTime"],
                "remaining": p["quotaVo"]["remaining"]
            } for p in available_periods]
        except requests.exceptions.RequestException as e:
            logger.error(f"请求异常: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"解析响应时出错: {str(e)}")
            return []

    def get_area_seats(
        self,
        area_id: str,
        start_time: str,
        end_time: str,
        area_name: str
    ) -> List[SeatInfo]:
        """
        获取指定区域的座位信息
        
        Args:
            area_id: 区域ID
            start_time: 开始时间
            end_time: 结束时间
            area_name: 区域名称
            
        Returns:
            座位信息列表，每个座位包含 ID、状态、行列号等信息
        """
        url = f"{self.base_url}/eastLibReservation/seat/getAreaSeats"
        target_date = get_target_date()
        params = {
            "areaId": area_id,
            "reservationStartDate": f"{target_date} {start_time}",
            "reservationEndDate": f"{target_date} {end_time}"
        }
        
        # 更新请求头
        headers = update_request_headers(self.headers)
        
        logger.info(f"请求区域 {area_name} 的座位信息: URL={url}, Headers={headers}, Params={params}")
        
        try:
            response = requests.get(url, headers=headers, params=params)
            logger.info(f"状态码: {response.status_code}")
            logger.info(f"响应头: {response.headers}")
            # logger.info(f"响应内容: {response.text}")
            
            if response.status_code != 200:
                logger.error(f"请求失败: {response.status_code} - {response.text}")
                return []
                
            data = response.json()
            seats = data.get("resultValue", [])
            if not seats:
                logger.warning(f"区域 {area_name} 没有找到任何座位")
                return []
                
            # 处理每个座位信息，添加 seatRowColumn 字段
            for seat in seats:
                seat["seatRowColumn"] = f"{seat['seatRow']} {seat['seatNo']}"
                
            available_seats = [s for s in seats if s.get("seatStatus") == 3]
            logger.info(f"区域 {area_name} 找到 {len(seats)} 个座位，其中可用的有 {len(available_seats)} 个")
            return seats
        except requests.exceptions.RequestException as e:
            logger.error(f"请求异常: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"解析响应时出错: {str(e)}")
            return []

    def reserve_seat(
        self,
        area_id: str,
        seat_id: int,
        seat_row_column: str,
        start_time: str,
        end_time: str,
        date: str,
        period: str,
        area_name: str,
        max_retries: int = 3,
        retry_interval: float = 1.0
    ) -> Dict[str, Any]:
        """
        预订座位，包含重试机制
        
        Args:
            area_id: 区域ID
            seat_id: 座位ID
            seat_row_column: 座位行列号
            start_time: 开始时间
            end_time: 结束时间
            date: 日期
            period: 时间段
            area_name: 区域名称
            max_retries: 最大重试次数
            retry_interval: 重试间隔（秒）
            
        Returns:
            预订结果字典
        """
        url = f"{self.base_url}/eastLibReservation/seatReservation/reservation"
        data = {
            "areaId": area_id,
            "floorId": settings.floor_id,
            "reservationStartDate": f"{date} {start_time}",
            "reservationEndDate": f"{date} {end_time}",
            "seatId": seat_id,
            "seatReservationType": settings.seat_reservation_type,
            "seatRowColumn": seat_row_column
        }
        
        for attempt in range(max_retries):
            try:
                # 更新请求头
                headers = update_request_headers(self.headers, force_update=False)
                
                logger.info(f"尝试第 {attempt + 1} 次预订: URL={url}, Headers={headers}, Data={data}")
                
                response = requests.post(url, headers=headers, json=data)
                logger.info(f"状态码: {response.status_code}")
                logger.info(f"响应头: {response.headers}")
                logger.info(f"响应内容: {response.text}")
                
                if response.status_code != 200:
                    logger.error(f"请求失败: {response.status_code} - {response.text}")
                    if attempt < max_retries - 1:
                        time.sleep(retry_interval)
                        continue
                    return {"status": "error", "message": f"请求失败: {response.status_code}"}
                    
                result = response.json()
                
                # 如果预订成功，更新共享座位记录
                if result.get("resultStatus", {}).get("code") == 0:
                    seat_no = int(seat_row_column.split("号")[0].split()[-1])
                    table_number = seat_row_column.split("排")[0]
                    if table_number not in settings.shared_seat_records[date][period][area_name]:
                        settings.shared_seat_records[date][period][area_name][table_number] = []
                    settings.shared_seat_records[date][period][area_name][table_number].append(str(seat_no))
                    return {"status": "success", "message": "预订成功"}
                else:
                    error_msg = result.get("resultStatus", {}).get("message", "未知错误")
                    if "已被预订" in error_msg and attempt < max_retries - 1:
                        logger.warning(f"座位已被预订，等待 {retry_interval} 秒后重试...")
                        time.sleep(retry_interval)
                        continue
                    return {"status": "error", "message": error_msg}
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"请求异常: {str(e)}")
                return {"status": "error", "message": f"请求异常: {str(e)}"}
            except Exception as e:
                logger.error(f"预订过程出错: {str(e)}")
                return {"status": "error", "message": f"预订过程出错: {str(e)}"}
        
        return {"status": "error", "message": "达到最大重试次数"}

    def find_best_seat(
        self,
        seats: List[SeatInfo],
        area_name: str,
        date: str,
        period: str
    ) -> Optional[SeatInfo]:
        """
        找到最佳座位
        
        规则：
        1. 优先选择已有其他用户预订的同桌座位
        2. 南区优先奇数桌号
        3. 优先选择靠右的座位
        
        Args:
            seats: 座位列表
            area_name: 区域名称
            date: 日期
            period: 时间段
            
        Returns:
            最佳座位信息字典，如果没有找到则返回 None
        """
        if not seats:
            return None

        # 按桌号分组座位
        tables: Dict[str, List[SeatInfo]] = {}
        for seat in seats:
            if seat["seatStatus"] != 3:  # 不是可用座位
                continue
            
            row = seat["seatRow"]
            if row not in tables:
                tables[row] = []
            tables[row].append(seat)

        # 如果是南区，只考虑奇数桌号
        if area_name == "南":
            tables = {row: seats for row, seats in tables.items() if is_odd_table(row)}

        if not tables:
            return None

        # 获取当前时间段已预订的桌子
        booked_tables = settings.shared_seat_records[date][period][area_name]
        
        # 对桌子进行排序，优先选择已有预订的桌子
        sorted_tables: List[tuple[int, str]] = []
        for row in tables.keys():
            table_number = row.split("排")[0]
            priority = 0 if table_number in booked_tables else 1
            sorted_tables.append((priority, row))
        
        sorted_tables.sort()

        # 对每个桌子的座位进行排序
        for _, row in sorted_tables:
            if not tables[row]:
                continue
                
            seats = tables[row]
            max_seat_no = max(int(seat["seatNo"].replace("号", "")) for seat in seats)
            preferred_order = get_preferred_seats(max_seat_no)
            
            # 按照优先级排序座位
            seats.sort(
                key=lambda x: preferred_order.index(int(x["seatNo"].replace("号", "")))
                if int(x["seatNo"].replace("号", "")) in preferred_order
                else len(preferred_order)
            )
            
            # 返回第一个可用座位
            return seats[0] if seats else None
            
        return None

    def find_common_best_seat(
        self,
        seats_per_period: List[List[SeatInfo]],
        area_name: str,
        date: str,
        periods: List[str],
        required_seats: int = 1
    ) -> List[Optional[SeatInfo]]:
        """
        找到所有给定时间段中共同存在的最佳座位组合。
        
        Args:
            seats_per_period: 每个时间段的可用座位列表（列表的列表）
            area_name: 区域名称
            date: 日期
            periods: 时间段字符串列表
            required_seats: 需要的座位数量
            
        Returns:
            最佳座位组合列表，如果没有找到则返回空列表
        """
        if not seats_per_period:
            return []
            
        # 找到在所有时间段都可用的座位
        seats_first: List[SeatInfo] = seats_per_period[0]
        common_seats: List[SeatInfo] = []
        
        for seat in seats_first:
            if seat["seatStatus"] != 3:
                continue
            is_available_all_periods = True
            for other_period_seats in seats_per_period[1:]:
                found_seat = next(
                    (s for s in other_period_seats if s["seatId"] == seat["seatId"]), 
                    None
                )
                if not found_seat or found_seat["seatStatus"] != 3:
                    is_available_all_periods = False
                    break
            if is_available_all_periods:
                common_seats.append(seat)
        
        if not common_seats:
            return []
            
        # 如果是南区，只保留奇数桌
        if area_name == "南":
            common_seats = [
                seat for seat in common_seats 
                if is_odd_table(str(seat["seatRow"]))
            ]
            
        if not common_seats:
            return []
            
        # 按桌号分组座位
        tables: Dict[str, List[SeatInfo]] = {}
        for seat in common_seats:
            table_number = seat["seatRowColumn"].split("排")[0]
            if table_number not in tables:
                tables[table_number] = []
            tables[table_number].append(seat)
        
        # 筛选出有足够座位的桌子
        valid_tables = {
            table: seats 
            for table, seats in tables.items() 
            if len(seats) >= required_seats
        }
        
        if not valid_tables:
            return []
            
        # 对每个桌子的座位按照右侧优先排序
        result_seats: List[Optional[SeatInfo]] = []
        for table_seats in valid_tables.values():
            if len(result_seats) == required_seats:
                break
                
            max_seat_no = max(
                int(seat["seatNo"].replace("号", "")) 
                for seat in table_seats
            )
            preferred_order = get_preferred_seats(max_seat_no)
            
            # 按照优先级排序座位
            table_seats.sort(
                key=lambda seat: preferred_order.index(
                    int(seat["seatNo"].replace("号", ""))
                ) if int(seat["seatNo"].replace("号", "")) in preferred_order 
                else len(preferred_order)
            )
            
            # 添加所需数量的座位
            seats_needed = required_seats - len(result_seats)
            result_seats.extend(table_seats[:seats_needed])
            
        return result_seats

    def make_reservation(self, users_config: List[Dict[str, Any]]) -> List[ReservationResult]:
        """
        为多个用户同时预订座位
        
        Args:
            users_config: 用户配置列表，每个用户包含 token 信息
            
        Returns:
            预订结果列表
        """
        results: List[ReservationResult] = []
        target_date = get_target_date()
        logger.info(f"目标日期: {target_date}")
        
        # 初始化共享座位记录
        if target_date not in settings.shared_seat_records:
            settings.shared_seat_records[target_date] = {}
            
        # 获取可用时间段
        periods_data = self.get_available_periods(target_date)
        if not periods_data:
            logger.warning("没有找到可用时间段")
            return results
            
        # 初始化时间段记录
        period_strs: List[str] = []
        for period in periods_data:
            p_str: str = f"{period['startTime']}-{period['endTime']}"
            period_strs.append(p_str)
            if p_str not in settings.shared_seat_records[target_date]:
                settings.shared_seat_records[target_date][p_str] = {}
                
        # 获取并按优先级排序区域
        areas = self.get_areas()
        if not areas:
            logger.warning("没有找到可用区域")
            return results
            
        # 遍历每个区域
        for area in areas:
            area_name = area["areaName"]
            area_id = str(area["id"])
            
            # 初始化区域记录
            for p_str in period_strs:
                if area_name not in settings.shared_seat_records[target_date][p_str]:
                    settings.shared_seat_records[target_date][p_str][area_name] = {}
                    
            # 获取每个时间段的座位信息
            seats_per_period: List[List[SeatInfo]] = []
            all_periods_available = True
            
            for period in periods_data:
                start_time = period["startTime"]
                end_time = period["endTime"]
                seats = self.get_area_seats(area_id, start_time, end_time, area_name)
                if not seats:
                    all_periods_available = False
                    break
                seats_per_period.append(seats)
                
            if not all_periods_available:
                continue
                
            # 查找满足所有用户的座位组合
            best_seats = self.find_common_best_seat(
                seats_per_period=seats_per_period,
                area_name=area_name,
                date=target_date,
                periods=period_strs,
                required_seats=len(users_config)
            )
            
            if not best_seats:
                logger.warning(f"区域 {area_name} 没有找到足够的共同座位")
                continue
                
            logger.info(f"区域 {area_name} 找到共同座位: {[seat['seatRowColumn'] for seat in best_seats]}")
            
            # 为每个用户预订座位
            reservation_failed = False  # 标记是否有预订失败（非已预约的情况）
            for user_idx, (user_config, seat) in enumerate(zip(users_config, best_seats)):
                # 更新当前实例的 headers
                self.headers = {"token": user_config.token}
                
                for i, period in enumerate(periods_data):
                    # 如果不是第一次预订，则等待指定的时间间隔
                    if i > 0 or user_idx > 0:
                        interval = settings.reservation_interval / 1000
                        logger.info(f"等待 {interval} 秒后进行下一次预订...")
                        time.sleep(interval)
                        
                    start_time = period["startTime"]
                    end_time = period["endTime"]
                    p_str = f"{start_time}-{end_time}"
                    
                    result = self.reserve_seat(
                        area_id=area_id,
                        seat_id=seat["seatId"],
                        seat_row_column=seat["seatRowColumn"],
                        start_time=start_time,
                        end_time=end_time,
                        date=target_date,
                        period=p_str,
                        area_name=area_name
                    )
                    
                    status = "成功" if result.get("status") == "success" else "失败"
                    message = result.get("message", "")
                    
                    # 使用接口传入的用户名记录日志
                    logger.info(
                        f"用户 {user_config.name} 在区域 {area_name} "
                        f"时间段 {p_str} 预订结果: {status} - {message}"
                    )
                    
                    results.append({
                        "user_name": user_config.name,
                        "time_period": p_str,
                        "area": area_name,
                        "seat": seat["seatRowColumn"],
                        "status": f"{status} - {message}"
                    })
                    
                    # 如果预订失败，且不是因为已有预约，则需要切换区域重试
                    if result.get("status") != "success" and "在该时间段有其他预约" not in message:
                        reservation_failed = True
                        break
                
                if reservation_failed:
                    break
                    
            # 只有在发生预订失败（非已预约）的情况下才切换区域
            if not reservation_failed:
                break
                
        return results 