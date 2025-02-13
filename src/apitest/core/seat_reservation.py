"""
座位预订核心模块
"""
from typing import Dict, List, Optional, Any, TypedDict
import requests
from loguru import logger

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


class SeatReservation:
    """座位预订类"""
    
    def __init__(self, user_config: Dict[str, Any]):
        """
        初始化座位预订实例
        
        Args:
            user_config: 用户配置字典，包含 headers 和 name
        """
        self.headers: Dict[str, str] = user_config["headers"]
        self.user_name: str = user_config["name"]
        self.base_url: str = settings.API_BASE_URL
        
    def get_areas(self) -> List[Dict[str, Any]]:
        """获取所有区域信息"""
        url = f"{self.base_url}/eastLibReservation/area"
        params = {"floorId": settings.FLOOR_ID}
        headers = update_request_headers(self.headers)
        response = requests.get(url, headers=headers, params=params)
        logger.info(f"获取区域响应: {response.text}")
        data = response.json()
        areas = data.get("resultValue", [])
        
        # 按照优先级排序区域
        def get_area_priority(area: Dict[str, Any]) -> int:
            try:
                return settings.AREA_PRIORITY.index(area["areaName"])
            except ValueError:
                return len(settings.AREA_PRIORITY)
        
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
            "reservationType": settings.PERIOD_RESERVATION_TYPE,
            "libraryId": settings.LIBRARY_ID
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
        end_time: str
    ) -> List[SeatInfo]:
        """
        获取指定区域的座位信息
        
        Args:
            area_id: 区域ID
            start_time: 开始时间
            end_time: 结束时间
            
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
        
        logger.info(f"请求区域 {area_id} 的座位信息: URL={url}, Headers={headers}, Params={params}")
        
        try:
            response = requests.get(url, headers=headers, params=params)
            logger.info(f"状态码: {response.status_code}")
            logger.info(f"响应头: {response.headers}")
            logger.info(f"响应内容: {response.text}")
            
            if response.status_code != 200:
                logger.error(f"请求失败: {response.status_code} - {response.text}")
                return []
                
            data = response.json()
            seats = data.get("resultValue", [])
            if not seats:
                logger.warning(f"区域 {area_id} 没有找到任何座位")
                return []
                
            # 处理每个座位信息，添加 seatRowColumn 字段
            for seat in seats:
                seat["seatRowColumn"] = f"{seat['seatRow']} {seat['seatNo']}"
                
            available_seats = [s for s in seats if s.get("seatStatus") == 3]
            logger.info(f"区域 {area_id} 找到 {len(seats)} 个座位，其中可用的有 {len(available_seats)} 个")
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
        area_name: str
    ) -> Dict[str, Any]:
        """
        预订座位
        
        Args:
            area_id: 区域ID
            seat_id: 座位ID
            seat_row_column: 座位行列号
            start_time: 开始时间
            end_time: 结束时间
            date: 日期
            period: 时间段
            area_name: 区域名称
            
        Returns:
            预订结果字典
        """
        url = f"{self.base_url}/eastLibReservation/seatReservation/reservation"
        data = {
            "areaId": area_id,
            "floorId": settings.FLOOR_ID,
            "reservationStartDate": f"{date} {start_time}",
            "reservationEndDate": f"{date} {end_time}",
            "seatId": seat_id,
            "seatReservationType": settings.SEAT_RESERVATION_TYPE,
            "seatRowColumn": seat_row_column
        }
        
        # 更新请求头
        headers = update_request_headers(self.headers)
        
        logger.info(f"预订座位: URL={url}, Headers={headers}, Data={data}")
        
        try:
            response = requests.post(url, headers=headers, json=data)
            logger.info(f"状态码: {response.status_code}")
            logger.info(f"响应头: {response.headers}")
            logger.info(f"响应内容: {response.text}")
            
            if response.status_code != 200:
                logger.error(f"请求失败: {response.status_code} - {response.text}")
                return {"status": "error", "message": f"请求失败: {response.status_code}"}
                
            result = response.json()
            
            # 如果预订成功，更新共享座位记录
            if result.get("resultStatus", {}).get("code") == 0:
                seat_no = int(seat_row_column.split("号")[0].split()[-1])
                table_number = seat_row_column.split("排")[0]
                if table_number not in settings.SHARED_SEAT_RECORDS[date][period][area_name]:
                    settings.SHARED_SEAT_RECORDS[date][period][area_name][table_number] = []
                settings.SHARED_SEAT_RECORDS[date][period][area_name][table_number].append(str(seat_no))
                return {"status": "success", "message": "预订成功"}
            else:
                return {"status": "error", "message": result.get("resultStatus", {}).get("message", "未知错误")}
        except requests.exceptions.RequestException as e:
            logger.error(f"请求异常: {str(e)}")
            return {"status": "error", "message": f"请求异常: {str(e)}"}
        except Exception as e:
            logger.error(f"解析响应时出错: {str(e)}")
            return {"status": "error", "message": f"解析响应时出错: {str(e)}"}

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
        booked_tables = settings.SHARED_SEAT_RECORDS[date][period][area_name]
        
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

    def make_reservation(self) -> List[ReservationResult]:
        """
        执行座位预订流程
        
        Returns:
            预订结果列表，每个结果包含时间段、区域、座位和状态信息
        """
        results: List[ReservationResult] = []
        target_date = get_target_date()
        logger.info(f"目标日期: {target_date}")
        
        # 初始化共享座位记录
        if target_date not in settings.SHARED_SEAT_RECORDS:
            settings.SHARED_SEAT_RECORDS[target_date] = {}
            
        # 获取可用时间段
        periods = self.get_available_periods(target_date)
        if not periods:
            logger.warning("没有找到可用时间段")
            return results
            
        # 获取所有区域
        areas = self.get_areas()
        if not areas:
            logger.warning("没有找到可用区域")
            return results
            
        # 对每个时间段进行预订
        for period in periods:
            start_time = period["startTime"]
            end_time = period["endTime"]
            period_str = f"{start_time}-{end_time}"
            logger.info(f"处理时间段: {period_str}")
            
            # 初始化时间段的共享座位记录
            if period_str not in settings.SHARED_SEAT_RECORDS[target_date]:
                settings.SHARED_SEAT_RECORDS[target_date][period_str] = {}
                
            # 遍历每个区域尝试预订
            for area in areas:
                area_name = area["areaName"]
                area_id = str(area["id"])
                logger.info(f"处理区域: {area_name} (ID: {area_id})")
                
                # 初始化区域的共享座位记录
                if area_name not in settings.SHARED_SEAT_RECORDS[target_date][period_str]:
                    settings.SHARED_SEAT_RECORDS[target_date][period_str][area_name] = {}
                    
                # 获取区域座位信息
                seats = self.get_area_seats(area_id, start_time, end_time)
                if not seats:
                    logger.warning(f"区域 {area_name} 没有找到可用座位")
                    continue
                    
                # 找到最佳座位
                best_seat = self.find_best_seat(seats, area_name, target_date, period_str)
                if not best_seat:
                    logger.warning(f"区域 {area_name} 没有找到最佳座位")
                    continue
                    
                logger.info(f"找到最佳座位: {best_seat['seatRowColumn']}")
                
                # 尝试预订座位
                result = self.reserve_seat(
                    area_id=area_id,
                    seat_id=best_seat["seatId"],
                    seat_row_column=best_seat["seatRowColumn"],
                    start_time=start_time,
                    end_time=end_time,
                    date=target_date,
                    period=period_str,
                    area_name=area_name
                )
                
                # 记录预订结果
                status = "成功" if result.get("status") == "success" else "失败"
                logger.info(f"预订结果: {status}")
                results.append({
                    "time_period": period_str,
                    "area": area_name,
                    "seat": best_seat["seatRowColumn"],
                    "status": status
                })
                
                # 如果预订成功，继续下一个时间段
                if result.get("status") == "success":
                    break
                    
        return results 