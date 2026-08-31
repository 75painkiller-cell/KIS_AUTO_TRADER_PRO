import time
import logging
from datetime import datetime, time as dtime

logger = logging.getLogger(__name__)

def is_weekend(now: datetime) -> bool:
    """주말(토, 일) 여부 확인"""
    return now.weekday() >= 5

def is_market_open(now: datetime = None) -> bool:
    """장 운영 시간 확인 (평일 09:00 ~ 15:30)"""
    now = now or datetime.now()
    if is_weekend(now):
        return False
    return dtime(9, 0) <= now.time() <= dtime(15, 30)

def can_buy(now: datetime = None) -> bool:
    """매수 가능 시간 확인 (평일 09:05 ~ 15:15)"""
    now = now or datetime.now()
    if is_weekend(now):
        return False
    return dtime(9, 5) <= now.time() <= dtime(15, 15)

def is_force_sell_time(now: datetime = None) -> bool:
    """강제 청산 시간 확인 (평일 15:20 ~ 15:30)"""
    now = now or datetime.now()
    if is_weekend(now):
        return False
    return dtime(15, 20) <= now.time() <= dtime(15, 30)


# ==========================================
# 🚀 실전 트레이딩 봇 적용 예시
# ==========================================
if __name__ == "__main__":
    # 메인 루프 (1초마다 반복한다고 가정)
    while True:
        # 1. 사이클이 시작될 때 시간을 한 번만 측정하여 고정합니다.
        current_time = datetime.now() 
        
        # 2. 고정된 시간을 각 함수에 전달하여 논리적 오차를 없앱니다.
        if not is_market_open(current_time):
            # logger.info("장이 열려있지 않습니다. 대기 중...")
            time.sleep(60)
            continue

        if is_force_sell_time(current_time):
            logger.warning("🕒 강제 청산 시간입니다! 모든 포지션을 종료합니다.")
            # liquidate_all_positions()
            time.sleep(60) # 청산 후 1분 대기
            continue

        if can_buy(current_time):
            # logger.info("📈 매수 로직 실행 중...")
            # execute_buy_strategy()
            pass
            
        time.sleep(1) # 1초 대기 후 다음 사이클 실행