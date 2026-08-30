import time
import global_data  
from my_logger import logger  
import telegram_msg  
import strategy  # 👈 디테일한 전략 모듈(strategy.py)을 가져옵니다.

# 🌐 글로벌 지표 캐싱용 전역 변수 설정
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

    logger.info(f"  ▶ 나스닥: {nq_price} / VIX: {vix_price} / 환율: {usdkrw}")
    logger.info(f"  ▶ 반도체: {sox} / 국채금리: {us10y} / 비트코인: {btc}")
    logger.info("-" * 50)

def main():
    global last_global_check_time
    
    start_msg = "🚀 KIS_AUTO_TRADER_PRO 가동 시작! (3중 모멘텀 전략 탑재 완료)"
    logger.info(start_msg)
    telegram_msg.send_message(start_msg) 

    while True:
        try:
            logger.info("=" * 50)
            logger.info("📊 시스템 상태 점검")
            
            # 1. 글로벌 지표 확인 (10분 주기 캐싱)
            current_time = time.time()
            if current_time - last_global_check_time >= GLOBAL_UPDATE_INTERVAL:
                check_global_indicators()
                last_global_check_time = current_time
            else:
                remain_time = int(GLOBAL_UPDATE_INTERVAL - (current_time - last_global_check_time))
                logger.info(f"🌍 [미국/글로벌 지표] (다음 갱신까지 {remain_time}초 남음)")
            
            time.sleep(0.5) 
            
            # 2. 🎯 전략 모듈 실행 (strategy.py의 디테일한 매수/매도 로직 작동)
            strategy.execute_trading_logic()

        except Exception as e:
            logger.error(f"⚠️ 봇 에러 발생: {e}")
            telegram_msg.send_message(f"🚨 봇 에러 발생: {e}")

        logger.info("⏳ 30초 대기 중...\n")
        time.sleep(30)

if __name__ == "__main__":
    main()