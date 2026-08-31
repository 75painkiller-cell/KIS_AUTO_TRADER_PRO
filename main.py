import sys
import os
import time
from datetime import datetime

# 서브 폴더 경로 자동 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
for folder in ['core', 'data', 'risk', 'utils']:
    folder_path = os.path.join(current_dir, folder)
    if folder_path not in sys.path:
        sys.path.append(folder_path)

from data import global_data
from utils.my_logger import logger
from utils import telegram_msg
from core import strategy
from core import scheduler

last_global_check_time = 0
GLOBAL_UPDATE_INTERVAL = 600

def check_global_indicators():
    """미국/글로벌 지표 조회 및 출력"""
    logger.info("🌍 [미국/글로벌 지표]")
    nq_price = global_data.get_nasdaq_futures()
    vix_price = global_data.get_vix()
    usdkrw = global_data.get_usdkrw()
    sox = global_data.get_sox()
    us10y = global_data.get_us_10y_yield()
    btc = global_data.get_bitcoin()

    logger.info(f" ▶ 나스닥: {nq_price} / VIX: {vix_price} / 환율: {usdkrw}")
    logger.info(f" ▶ 반도체: {sox} / 국채금리: {us10y} / 비트코인: {btc}")
    logger.info("-" * 50)

def main():
    global last_global_check_time
    start_msg = "🚀 KIS 자동 매매 봇이 시작되었습니다."
    logger.info(start_msg)
    telegram_msg.send_message(start_msg)

    while True:
        try:
            now = datetime.now()

            # 💡 [위치 수정됨] 글로벌 지표 갱신을 먼저 실행
            current_timestamp = time.time()
            if current_timestamp - last_global_check_time >= GLOBAL_UPDATE_INTERVAL:
                check_global_indicators()
                last_global_check_time = current_timestamp

            # 장 운영 시간 체크
            if not scheduler.is_market_open(now) and not getattr(strategy, 'IS_TEST_MODE', False):
                logger.info("⏳ 현재 장 외 시간 또는 공휴일입니다. 30초 후 다시 확인합니다.")
                time.sleep(30)
                continue

            # 💡 [수정 위치 1: 장 마감 시간 체크] 
            # 오후 3시(15:00:00) 이후 신규 매매 진입 차단
            if now.strftime("%H%M%S") >= "150000" and not getattr(strategy, 'IS_TEST_MODE', False):
                logger.info("🛑 15시 이후이므로 신규 매매를 진행하지 않습니다.")
                time.sleep(30)
                continue

            # 전략 로직 호출
            strategy.execute_trading_logic(now)

        except Exception as e:
            logger.error(f"⚠️ 봇 에러 발생: {e}")
            telegram_msg.send_message(f"⚠️ 봇 에러 발생: {e}")

        # 💡 [수정 위치 2: 슬립 타임 30초 원복]
        # 1초 폭주를 막고 서버 및 API 안정화를 위해 30초 대기
        time.sleep(30) 

if __name__ == "__main__":
    main()