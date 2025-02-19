"""
定时预订服务
"""
import json
import os
from datetime import datetime
from typing import List, Optional, Dict
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from loguru import logger

from ..schemas.schedule_models import (
    ScheduleConfig,
    ScheduleStatus,
    UserToken
)
from ..core.seat_reservation import SeatReservation
from ..utils.helpers import get_target_date

class ScheduleService:
    """定时预订服务"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.config = ScheduleConfig()
        self.user_tokens: List[UserToken] = []
        self.job = None
        self.last_run_time: Optional[datetime] = None
        self.last_run_result: Optional[str] = None
        self._load_user_tokens()
        logger.info("定时任务服务初始化完成")
        
    def _get_token_file_path(self) -> str:
        """获取token文件路径"""
        return os.path.join(os.path.dirname(__file__), "..", "data", "user_tokens.json")
        
    def _load_user_tokens(self) -> None:
        """从文件加载用户token信息"""
        try:
            file_path = self._get_token_file_path()
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.user_tokens = [UserToken(**token) for token in data]
                    logger.info(f"成功加载 {len(self.user_tokens)} 个用户token")
            else:
                logger.info("token文件不存在，将在首次保存时创建")
        except Exception as e:
            logger.error(f"加载token文件失败: {str(e)}")
            
    def _save_user_tokens(self) -> None:
        """保存用户token信息到文件"""
        try:
            file_path = self._get_token_file_path()
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(
                    [token.model_dump() for token in self.user_tokens],
                    f,
                    ensure_ascii=False,
                    indent=2
                )
            logger.info(f"成功保存 {len(self.user_tokens)} 个用户token")
        except Exception as e:
            logger.error(f"保存token文件失败: {str(e)}")
            
    async def _schedule_task(self) -> None:
        """定时任务执行函数"""
        try:
            self.last_run_time = datetime.now()
            if not self.user_tokens:
                logger.warning("没有维护任何用户token信息，跳过预订")
                self.last_run_result = "跳过执行：没有维护任何用户token信息"
                return
                
            target_date = get_target_date()
            logger.info(f"开始执行定时预订任务，目标日期: {target_date}")
            
            # 创建预订实例
            reservation = SeatReservation({"token": self.user_tokens[0].token})
            
            # 执行预订
            results = reservation.make_reservation(self.user_tokens)
            
            # 记录结果
            if results:
                logger.info(f"预订成功，共 {len(results)} 个结果")
                # 计算每个用户的结果数量
                periods_per_user = len(results) // len(self.user_tokens)
                success_count = 0
                result_messages = []
                for i, result in enumerate(results):
                    # 计算当前结果属于哪个用户
                    user_index = i // periods_per_user
                    user_name = self.user_tokens[user_index].name
                    status = result['status']
                    if status == 'success':
                        success_count += 1
                    result_messages.append(
                        f"{user_name}: {status} ({result['area']} {result['seat']} {result['time_period']})"
                    )
                    logger.info(
                        f"预订结果: "
                        f"用户={user_name}, "
                        f"状态={status}, "
                        f"区域={result['area']}, "
                        f"座位={result['seat']}, "
                        f"时间段={result['time_period']}"
                    )
                self.last_run_result = f"成功预订 {success_count}/{len(results)} 个座位。" + " ".join(result_messages)
            else:
                logger.warning("预订失败，没有找到可用座位")
                self.last_run_result = "预订失败：没有找到可用座位"
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"执行定时预订任务时出错: {error_msg}")
            self.last_run_result = f"执行出错：{error_msg}"
            
    async def initialize(self) -> None:
        """异步初始化"""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("调度器已启动")
            
        if self.config.enabled:
            await self.start()
            logger.info("定时任务已启动")

    async def start(self) -> None:
        """启动定时任务"""
        try:
            # 尝试移除已存在的任务
            try:
                if self.scheduler.get_job("seat_reservation"):
                    self.scheduler.remove_job("seat_reservation")
            except Exception:
                pass  # 如果任务不存在，忽略错误
        
            # 添加新任务
            self.job = self.scheduler.add_job(
                self._schedule_task,
                CronTrigger.from_crontab(self.config.cron),
                id="seat_reservation"
            )
            logger.info(f"定时任务已配置，cron表达式: {self.config.cron}")
        except Exception as e:
            logger.error(f"启动定时任务失败: {str(e)}")
            raise e

    async def stop(self) -> None:
        """停止定时任务"""
        if self.job:
            self.job.remove()
            self.job = None
            logger.info("定时任务已停止")
            
    def shutdown(self) -> None:
        """关闭调度器"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("调度器已关闭")

    def get_status(self) -> ScheduleStatus:
        """获取定时任务状态"""
        if not self.job:
            return ScheduleStatus(
                is_running=False,
                next_run_time=None,
                last_run_time=self.last_run_time,
                last_run_result=self.last_run_result
            )
            
        return ScheduleStatus(
            is_running=True,
            next_run_time=self.job.next_run_time,
            last_run_time=self.last_run_time,
            last_run_result=self.last_run_result
        )
        
    def update_config(self, config: ScheduleConfig) -> None:
        """更新定时任务配置"""
        self.config = config
        if config.enabled:
            self.start()
        else:
            self.stop()
            
    def get_user_tokens(self) -> List[UserToken]:
        """获取所有用户token"""
        return self.user_tokens
        
    def update_user_tokens(self, tokens: List[UserToken]) -> None:
        """更新用户token列表"""
        self.user_tokens = tokens
        self._save_user_tokens()
        
    def add_user_token(self, token: UserToken) -> None:
        """添加用户token"""
        # 检查是否已存在
        for existing in self.user_tokens:
            if existing.name == token.name:
                existing.token = token.token
                break
        else:
            self.user_tokens.append(token)
        self._save_user_tokens()
        
    def remove_user_token(self, name: str) -> None:
        """删除用户token"""
        self.user_tokens = [t for t in self.user_tokens if t.name != name]
        self._save_user_tokens() 