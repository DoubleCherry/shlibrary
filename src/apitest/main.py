"""
主入口模块
"""
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime
from contextlib import asynccontextmanager

import click
import yaml
from loguru import logger
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.seat_reservation import SeatReservation, ReservationResult
from .config.settings import settings
from .api import endpoints
from .api import snipe_endpoints
from .api import schedule_endpoints
from .api import checkin_endpoints

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时的处理
    await schedule_endpoints.schedule_service.initialize()
    logger.info("应用启动：调度器初始化完成")
    
    yield
    
    # 关闭时的处理
    schedule_endpoints.schedule_service.shutdown()
    logger.info("应用关闭：调度器已停止")

# 创建FastAPI应用
app = FastAPI(
    title="图书馆座位预订系统",
    description="自动预订图书馆座位的API服务",
    version="1.0.0",
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(endpoints.router)
app.include_router(snipe_endpoints.router)
app.include_router(schedule_endpoints.router)
app.include_router(checkin_endpoints.router)

def init_logger(log_level: Optional[str] = None) -> None:
    """初始化日志配置
    
    Args:
        log_level: 日志级别，如果为 None 则使用配置文件中的设置
    """
    logger.add(
        "logs/app.log",
        rotation=settings.log_rotation,
        retention=settings.log_retention,
        level=log_level or settings.log_level,
        encoding=settings.log_encoding
    )


@click.group()
def cli() -> None:
    """座位预订系统命令行工具"""
    pass


@cli.command()
@click.option(
    "--host",
    default="0.0.0.0",
    help="服务器监听地址",
    show_default=True
)
@click.option(
    "--port",
    default=8000,
    help="服务器监听端口",
    show_default=True
)
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"], case_sensitive=False),
    default=None,
    help="日志级别（默认使用配置文件中的设置）",
    show_default=True
)
def serve(host: str, port: int, log_level: Optional[str]) -> None:
    """启动API服务器"""
    init_logger(log_level)
    uvicorn.run(app, host=host, port=port)


@cli.command()
@click.option(
    "--config",
    type=click.Path(exists=True, path_type=Path),
    help="用户配置文件路径",
    required=True
)
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"], case_sensitive=False),
    default=None,
    help="日志级别（默认使用配置文件中的设置）",
    show_default=True
)
@click.option(
    "--date",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    default=lambda: datetime.now().strftime("%Y-%m-%d"),
    help="预订日期，格式：YYYY-MM-DD",
    show_default=True
)
def reserve(config: Path, log_level: Optional[str], date: datetime) -> None:
    """
    执行座位预订
    
    Args:
        config: 用户配置文件路径
        log_level: 日志级别
        date: 预订日期
    """
    init_logger(log_level)
    
    try:
        # 读取用户配置
        with open(config, "r", encoding="utf-8") as f:
            config_data: Dict[str, Any] = yaml.safe_load(f)
            
        # 添加日期信息到配置中
        formatted_date = date.strftime("%Y-%m-%d")
        
        # 获取用户列表
        users_config = config_data.get("users", [])
        if not users_config:
            logger.error("配置文件中没有找到用户信息")
            raise click.ClickException("配置文件中没有找到用户信息")
            
        # 创建预订实例并执行预订
        reservation = SeatReservation({"headers": users_config[0]["headers"]})  # 使用第一个用户的 headers 初始化
        results = reservation.make_reservation(users_config)
        
        # 打印预订结果
        for result in results:
            logger.info(
                f"日期: {formatted_date}, "
                f"时间段: {result['time_period']}, "
                f"区域: {result['area']}, "
                f"座位: {result['seat']}, "
                f"状态: {result['status']}"
            )
            
    except Exception as e:
        logger.error(f"程序执行出错: {str(e)}")
        raise click.ClickException(str(e))


@cli.command()
@click.option(
    "--config",
    type=click.Path(exists=True, path_type=Path),
    help="用户配置文件路径",
    required=True
)
def validate(config: Path) -> None:
    """
    验证配置文件
    
    Args:
        config: 用户配置文件路径
    """
    try:
        with open(config, "r", encoding="utf-8") as f:
            yaml.safe_load(f)  # 只验证文件格式，不需要使用返回值
        click.echo(f"配置文件 {config} 格式正确")
        click.echo("当前配置:")
        click.echo(f"API URL: {settings.api_base_url}")
        click.echo(f"预订间隔: {settings.reservation_interval}ms")
        click.echo(f"区域优先级: {settings.area_priority}")
        click.echo(f"日志级别: {settings.log_level}")
    except Exception as e:
        raise click.ClickException(f"配置文件格式错误: {str(e)}")


@app.get("/")
async def root():
    """根路由"""
    return {"message": "座位预订API服务"}


if __name__ == "__main__":
    cli() 