import sys
import os
import time

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

# 글로벌 지표 캐싱용 전역 변수 설정
last_global_check_time = 0
GLOBAL_UPDATE_INTERVAL = 600  # 600초 (10분) 주기

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
            current_time = time.time()
            if current_time - last_global_check_time >= GLOBAL_UPDATE_INTERVAL:
                check_global_indicators()
                last_global_check_time = current_time

            # 전략 실행 함수 호출
            strategy.execute_trading_logic()

        except Exception as e:
            logger.error(f"⚠️ 봇 에러 발생: {e}")
            telegram_msg.send_message(f"⚠️ 봇 에러 발생: {e}")

        logger.info("⏳ 30초 대기 중...\n")
        time.sleep(30)

if __name__ == "__main__":
    main()