"""
主入口模块
"""
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime

import click
import yaml
from loguru import logger

from .core.seat_reservation import SeatReservation, ReservationResult
from .config.settings import settings


def init_logger(log_level: Optional[str] = None) -> None:
    """初始化日志配置
    
    Args:
        log_level: 日志级别，如果为 None 则使用配置文件中的设置
    """
    logger.add(
        "logs/app.log",
        rotation=settings.LOG_ROTATION,
        retention=settings.LOG_RETENTION,
        level=log_level or settings.LOG_LEVEL,
        encoding=settings.LOG_ENCODING
    )


@click.group()
def cli() -> None:
    """座位预订系统命令行工具"""
    pass


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
        
        results: List[ReservationResult] = []
        # 为每个用户进行预订
        for user in config_data["users"]:
            user_config = {
                "name": user["name"],
                "headers": user["headers"],
                "date": formatted_date
            }
            
            # 创建预订实例并执行预订
            reservation = SeatReservation(user_config)
            user_results = reservation.make_reservation()
            results.extend(user_results)
        
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
        click.echo(f"API URL: {settings.API_BASE_URL}")
        click.echo(f"预订间隔: {settings.RESERVATION_INTERVAL}ms")
        click.echo(f"区域优先级: {settings.AREA_PRIORITY}")
        click.echo(f"日志级别: {settings.LOG_LEVEL}")
    except Exception as e:
        raise click.ClickException(f"配置文件格式错误: {str(e)}")


if __name__ == "__main__":
    cli() 