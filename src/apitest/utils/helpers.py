"""
工具函数模块
"""
from datetime import datetime, timedelta
from typing import List, Dict
import hashlib

from ..config.config import config


def get_target_date() -> str:
    """获取目标日期（T+6天）"""
    target_date = datetime.now() + timedelta(days=config.days_ahead)
    return target_date.strftime("%Y-%m-%d")


def generate_sign(client_id: str, access_token: str, timestamp: str) -> str:
    """
    生成签名
    
    Args:
        client_id: 客户端ID
        access_token: 访问令牌
        timestamp: 时间戳
        
    Returns:
        生成的签名
    """
    # 按照特定顺序拼接参数
    sign_str = f"{client_id}{access_token}{timestamp}"
    # 使用SHA256生成签名
    return hashlib.sha256(sign_str.encode()).hexdigest()


def update_request_headers(headers: Dict[str, str]) -> Dict[str, str]:
    """
    更新请求头信息
    
    Args:
        headers: 原始请求头
        
    Returns:
        更新后的请求头
    """
    new_headers = headers.copy()
    
    # 添加标准HTTP请求头
    new_headers.update({
        "User-Agent": "Apifox/1.0.0 (https://apifox.com)",
        "Accept": "*/*",
        "Host": "yuyue.library.sh.cn",
        "Connection": "keep-alive"
    })
    
    return new_headers


def parse_seat_row_number(seat_row: str) -> int:
    """解析座位排号"""
    try:
        return int(seat_row.split("排")[0])
    except (ValueError, IndexError):
        return 0


def get_preferred_seats(max_seat_no: int) -> List[int]:
    """获取优先座位顺序"""
    if max_seat_no == 4:
        return [4, 3, 2, 1]
    elif max_seat_no == 6:
        return [6, 5, 4, 3, 2, 1]
    return list(range(max_seat_no, 0, -1))


def is_odd_table(row: str) -> bool:
    """判断是否为奇数桌号"""
    table_number = parse_seat_row_number(row)
    return table_number % 2 == 1


def format_datetime(time_str: str) -> str:
    """格式化时间字符串"""
    return time_str 