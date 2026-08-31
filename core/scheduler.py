import time
import logging
from datetime import datetime, time as dtime

logger = logging.getLogger(__name__)

def is_market_open() -> bool:
    """장 운영 시간 확인 (평일 09:00 ~ 15:30)"""
    now = datetime.now()
    if now.weekday() >= 5:
        return False
    return dtime(9, 0) <= now.time() <= dtime(15, 30)

def can_buy() -> bool:
    """매수 가능 시간 확인"""
    now = datetime.now()
    if now.weekday() >= 5:
        return False
    return dtime(9, 5) <= now.time() <= dtime(15, 15)

def is_force_sell_time() -> bool:
    """강제 청산 시간 확인"""
    now = datetime.now()
    if now.weekday() >= 5:
        return False
    return dtime(15, 20) <= now.time() <= dtime(15, 30)