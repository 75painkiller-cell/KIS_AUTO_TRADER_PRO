from datetime import datetime, time
from typing import Tuple
import holidays

# 장 운영 및 매매 시간 설정 (시, 분)
MARKET_OPEN = (9, 0)
MARKET_CLOSE = (15, 30)
BUY_START = (9, 5)
BUY_END = (15, 15)
FORCE_SELL_TIME = (15, 20)

def _get_current_time_info() -> Tuple[int, time]:
    """현재 날짜의 요일 인덱스(월=0, ..., 일=6)와 시각 객체를 반환합니다."""
    now = datetime.now()
    return now.weekday(), now.time()

def _is_holiday() -> bool:
    """오늘이 대한민국 공휴일(대체공휴일 포함)인지 확인합니다."""
    kr_holidays = holidays.KR()
    return datetime.now().date() in kr_holidays

def is_market_open() -> bool:
    """현재 장 운영 시간 내에 있는지 확인합니다 (주말 및 공휴일 제외)."""
    weekday, current_time = _get_current_time_info()

    if weekday >= 5 or _is_holiday():
        return False

    open_time = time(MARKET_OPEN[0], MARKET_OPEN[1])
    close_time = time(MARKET_CLOSE[0], MARKET_CLOSE[1])

    return open_time <= current_time <= close_time

def can_buy() -> bool:
    """신규 매수 가능 시간 내에 있는지 확인합니다 (주말 및 공휴일 제외)."""
    weekday, current_time = _get_current_time_info()

    if weekday >= 5 or _is_holiday():
        return False

    buy_start_time = time(BUY_START[0], BUY_START[1])
    buy_end_time = time(BUY_END[0], BUY_END[1])

    return buy_start_time <= current_time <= buy_end_time

def is_force_sell_time() -> bool:
    """장 마감 전 강제 청산 시간인지 확인합니다 (주말 및 공휴일 제외)."""
    weekday, current_time = _get_current_time_info()

    if weekday >= 5 or _is_holiday():
        return False

    force_time = time(FORCE_SELL_TIME[0], FORCE_SELL_TIME[1])
    close_time = time(MARKET_CLOSE[0], MARKET_CLOSE[1])

    return force_time <= current_time <= close_time

def market_status() -> str:
    """현재 시장 상태 텍스트를 반환합니다."""
    if _is_holiday():
        return "HOLIDAY"
    if is_market_open():
        return "OPEN"
    return "CLOSED"

if __name__ == "__main__":
    print("현재 시각 :", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("시장 상태 :", market_status())
    print("공휴일 여부:", _is_holiday())
    print("매수 가능 :", can_buy())
    print("강제 청산 :", is_force_sell_time())