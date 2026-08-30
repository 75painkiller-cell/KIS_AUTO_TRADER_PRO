from datetime import datetime, time
from typing import Tuple
from config import (
    MARKET_OPEN,
    MARKET_CLOSE,
    BUY_START,
    BUY_END,
    FORCE_SELL_TIME,
)

def _get_current_time_info() -> Tuple[int, time]:
    """현재 날짜의 요일 인덱스(월=0, ..., 일=6)와 시각 객체를 반환합니다."""
    now = datetime.now()
    return now.weekday(), now.time()

def is_market_open() -> bool:
    """현재 장 운영 시간(09:00 ~ 15:30) 내에 있는지 확인합니다 (주말 제외)."""
    weekday, current_time = _get_current_time_info()

    # 주말(토=5, 일=6) 제외
    if weekday >= 5:
        return False

    open_time = time(MARKET_OPEN[0], MARKET_OPEN[1])
    close_time = time(MARKET_CLOSE[0], MARKET_CLOSE[1])

    return open_time <= current_time <= close_time

def can_buy() -> bool:
    """신규 매수 가능 시간(09:05 ~ 15:15) 내에 있는지 확인합니다."""
    weekday, current_time = _get_current_time_info()

    if weekday >= 5:
        return False

    buy_start_time = time(BUY_START[0], BUY_START[1])
    buy_end_time = time(BUY_END[0], BUY_END[1])

    return buy_start_time <= current_time <= buy_end_time

def is_force_sell_time() -> bool:
    """장 마감 전 강제 청산 시간(예: 15:20 이후)인지 확인합니다."""
    weekday, current_time = _get_current_time_info()

    if weekday >= 5:
        return False

    force_time = time(FORCE_SELL_TIME[0], FORCE_SELL_TIME[1])
    close_time = time(MARKET_CLOSE[0], MARKET_CLOSE[1])

    return force_time <= current_time <= close_time

def market_status() -> str:
    """현재 시장 상태 텍스트를 반환합니다."""
    if is_market_open():
        return "OPEN"
    return "CLOSED"


if __name__ == "__main__":
    # 단독으로 실행(테스트)할 때 출력되는 부분
    print("현재 시각 :", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("시장 상태 :", market_status())
    print("매수 가능 :", can_buy())
    print("강제 청산 :", is_force_sell_time())