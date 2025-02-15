"""
座位捡漏服务模块
"""
from datetime import datetime, date, timedelta
import time
import uuid
from typing import Dict, List, Optional
import asyncio
from loguru import logger

from ..schemas.snipe_models import SnipeTask, TaskStatus
from ..config.settings import settings
from .seat_reservation import SeatReservation


class SnipeService:
    """座位捡漏服务"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """初始化捡漏服务"""
        if not self._initialized:
            self._tasks: Dict[str, SnipeTask] = {}
            self._running = False
            self._lock = asyncio.Lock()
            self._initialized = True
            logger.info("捡漏服务初始化完成")
    
    async def create_task(self, user_token: str, user_name: str, target_date: date) -> SnipeTask:
        """
        创建捡漏任务
        
        Args:
            user_token: 用户token
            user_name: 用户姓名
            target_date: 目标日期
            
        Returns:
            创建的任务实例
        """
        today = date.today()
        yesterday = today - timedelta(days=1)
        
        # 计算目标日期与今天的相对天数
        days_diff = (target_date - today).days
        
        logger.debug(
            f"日期调试信息: "
            f"目标日期={target_date} ({type(target_date)}), "
            f"今天={today} ({type(today)}), "
            f"昨天={yesterday} ({type(yesterday)}), "
            f"相对天数={days_diff}"
        )
        
        # 验证目标日期 - 只有相对天数小于0的才算过期
        if days_diff < 0:
            logger.warning(
                f"无法创建过期任务: "
                f"用户={user_name}, "
                f"目标日期={target_date}, "
                f"今天={today}, "
                f"昨天={yesterday}, "
                f"相对天数={days_diff}"
            )
            raise ValueError("无法创建过期的任务")
        
        logger.info(
            f"日期验证通过: "
            f"用户={user_name}, "
            f"目标日期={target_date}, "
            f"今天={today}, "
            f"相对天数={days_diff}"
        )
        
        # 检查是否已存在相同的任务
        for task in self._tasks.values():
            if (task.user_token == user_token and 
                task.target_date == target_date and 
                task.status == TaskStatus.ACTIVE):
                logger.info(f"任务已存在: 用户={user_name}, 日期={target_date}")
                return task
        
        task = SnipeTask(
            id=str(uuid.uuid4()),
            user_token=user_token,
            user_name=user_name,
            target_date=target_date,
            created_at=today
        )
        
        async with self._lock:
            self._tasks[task.id] = task
            if not self._running:
                self._running = True
                asyncio.create_task(self._snipe_loop())
                logger.info("启动捡漏循环")
        
        logger.info(
            f"创建捡漏任务: ID={task.id}, "
            f"用户={user_name}, "
            f"日期={target_date}, "
            f"当前任务总数={len(self._tasks)}"
        )
        return task
    
    def get_active_tasks(self) -> List[SnipeTask]:
        """获取所有活动中的任务"""
        active_tasks = [task for task in self._tasks.values() 
                       if task.status == TaskStatus.ACTIVE]
        logger.info(f"当前活动任务数: {len(active_tasks)}")
        return active_tasks
    
    async def stop_tasks(self, task_ids: List[str]) -> List[SnipeTask]:
        """
        停止指定的任务
        
        Args:
            task_ids: 要停止的任务ID列表
            
        Returns:
            已停止的任务列表
        """
        stopped_tasks = []
        async with self._lock:
            for task_id in task_ids:
                if task := self._tasks.get(task_id):
                    task.status = TaskStatus.TERMINATED
                    stopped_tasks.append(task)
                    logger.info(f"停止任务: ID={task_id}, 用户={task.user_name}")
        return stopped_tasks
    
    async def _snipe_loop(self):
        """捡漏主循环"""
        logger.info("捡漏循环开始运行")
        while self._running:
            try:
                active_tasks = self.get_active_tasks()
                if not active_tasks:
                    logger.info("没有活动中的任务，停止捡漏循环")
                    self._running = False
                    break
                
                # 按日期分组任务
                tasks_by_date: Dict[date, List[SnipeTask]] = {}
                today = date.today()
                yesterday = today - timedelta(days=1)
                for task in active_tasks:
                    # 如果目标日期是昨天或更早，则终止任务
                    if task.target_date <= yesterday:
                        task.status = TaskStatus.COMPLETED
                        logger.info(f"任务过期自动终止: ID={task.id}, 用户={task.user_name}, 目标日期={task.target_date}, 当前日期={today}")
                        continue
                    tasks_by_date.setdefault(task.target_date, []).append(task)
                    logger.info(f"任务进入执行队列: ID={task.id}, 用户={task.user_name}, 目标日期={task.target_date}")
                
                # 为每个日期执行捡漏
                for target_date, tasks in tasks_by_date.items():
                    logger.info(f"开始执行日期 {target_date} 的捡漏任务，共 {len(tasks)} 个任务")
                    await self._snipe_for_date(target_date, tasks)
                
                # 等待下一次执行
                logger.debug(f"等待 {settings.snipe_interval} 秒后进行下一轮捡漏")
                await asyncio.sleep(settings.snipe_interval)
            
            except Exception as e:
                logger.error(f"捡漏任务执行出错: {str(e)}")
                await asyncio.sleep(settings.snipe_interval)
    
    async def _snipe_for_date(self, target_date: date, tasks: List[SnipeTask]):
        """
        为指定日期执行捡漏
        
        Args:
            target_date: 目标日期
            tasks: 该日期的任务列表
        """
        try:
            # 为每个任务创建预订实例
            reservations = []
            for task in tasks:
                config = {"headers": {"token": task.user_token}}
                reservation = SeatReservation(config)
                reservations.append(reservation)
            
            # 获取可用时间段
            date_str = target_date.strftime("%Y-%m-%d")
            periods = reservations[0].get_available_periods(date_str)
            
            if not periods:
                logger.debug(f"日期 {date_str} 没有可用时间段")
                return
            
            # 获取所有区域
            areas = reservations[0].get_areas()
            logger.debug(f"获取到 {len(areas)} 个区域")
            
            # 尝试为每个区域预订座位
            for area in areas:
                area_id = str(area["areaId"])
                area_name = area["areaName"]
                
                # 获取区域座位
                seats = reservations[0].get_area_seats(
                    area_id=area_id,
                    start_time=periods[0]["startTime"],
                    end_time=periods[0]["endTime"]
                )
                
                if not seats:
                    logger.debug(f"区域 {area_name} 没有座位信息")
                    continue
                
                # 尝试为每个用户预订座位
                available_seats = [s for s in seats if s["seatStatus"] == 3]  # 状态3表示空座位
                logger.debug(f"区域 {area_name} 有 {len(available_seats)} 个空座位")
                
                for i, (task, reservation) in enumerate(zip(tasks, reservations)):
                    if i >= len(available_seats):
                        logger.debug(f"区域 {area_name} 座位不足，剩余 {len(tasks) - i} 个用户未分配座位")
                        break
                        
                    seat = available_seats[i]
                    try:
                        result = reservation.reserve_seat(
                            area_id=area_id,
                            seat_id=seat["seatId"],
                            seat_row_column=seat["seatRowColumn"],
                            start_time=periods[0]["startTime"],
                            end_time=periods[0]["endTime"],
                            date=date_str,
                            period=f"{periods[0]['startTime']}-{periods[0]['endTime']}",
                            area_name=area_name
                        )
                        
                        if result.get("status") == "success":
                            task.status = TaskStatus.COMPLETED
                            logger.info(
                                f"捡漏成功: "
                                f"用户={task.user_name}({task.user_token}), "
                                f"日期={date_str}, "
                                f"时间段={periods[0]['startTime']}-{periods[0]['endTime']}, "
                                f"座位={area_name} {seat['seatRow']}排 {seat['seatNo']}号"
                            )
                    
                    except Exception as e:
                        logger.error(f"预订座位失败: {str(e)}")
                        continue
        
        except Exception as e:
            logger.error(f"执行日期 {target_date} 的捡漏任务出错: {str(e)}") 