"""
工具函数模块
"""
from datetime import datetime, timedelta
from typing import List, Dict
import hashlib
import time

from ..config.settings import settings


def get_target_date() -> str:
    """获取目标日期"""
    target_date = datetime.now() + timedelta(days=settings.DAYS_AHEAD)
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


def update_request_headers(headers: Dict[str, str], force_update: bool = False) -> Dict[str, str]:
    """
    更新请求头信息，包括时间戳和签名
    
    Args:
        headers: 原始请求头
        force_update: 是否强制更新时间戳和签名，默认为False
        
    Returns:
        更新后的请求头
    """
    new_headers = headers.copy()
    
    # 仅在force_update为True或原headers中没有timestamp和sign时更新
    if force_update or "timestamp" not in headers or "sign" not in headers:
        # 更新时间戳
        timestamp = str(int(time.time() * 1000))
        new_headers["timestamp"] = timestamp
        
        # 更新签名
        if "clientId" in new_headers and "accessToken" in new_headers:
            new_headers["sign"] = generate_sign(
                new_headers["clientId"],
                new_headers["accessToken"],
                timestamp
            )
    
    # 添加标准HTTP请求头
    new_headers.update({
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Content-Type": "application/json",
        "Origin": settings.API_BASE_URL,
        "Referer": f"{settings.API_BASE_URL}/",
        "Host": settings.API_BASE_URL.replace("https://", ""),
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Connection": "keep-alive",
        "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin"
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