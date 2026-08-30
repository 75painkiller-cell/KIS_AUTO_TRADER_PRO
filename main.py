import time
from datetime import datetime
import api_kis
import global_data  
from my_logger import logger  
import telegram_msg  

# 🔥 테스트 모드 (True: 주말/새벽 무시하고 무조건 24시간 가동, False: 평일 장 시간에만 가동)
TEST_MODE = True  

# 내가 사고팔 목표 종목들
TARGETS = {
    "069500": "KODEX 200",
    "114800": "KODEX 인버스",
    "229200": "KODEX 코스닥150",
    "251340": "KODEX 코스닥150선물인버스"
}

# 🌐 글로벌 지표 캐싱용 전역 변수 설정
last_global_check_time = 0
GLOBAL_UPDATE_INTERVAL = 600  # 600초 (10분) 주기
cached_vix_price = 0.0        # 매매 로직에 넘겨줄 VIX 임시 저장 공간

def is_market_open():
    """현재가 정규장 시간(평일 09:00 ~ 15:30)인지 확인"""
    now = datetime.now()
    if now.weekday() > 4: 
        return False
    market_start = now.replace(hour=9, minute=0, second=0, microsecond=0)
    market_end = now.replace(hour=15, minute=30, second=0, microsecond=0)
    return market_start <= now <= market_end

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
    return vix_price

def check_account_and_targets():
    """내 계좌 잔고 및 타겟 종목 현재가 조회"""
    logger.info("💰 [내 계좌 및 타겟 종목]")
    asset, profit, holdings = api_kis.get_balance()
    logger.info(f"  총 자산: {asset:,}원 | 손익: {profit:,}원")
    
    for code, name in TARGETS.items():
        price = api_kis.get_current_price(code)
        logger.info(f"  🎯 {name}: {price}원" if price else f"  ⚠️ {name} 조회 실패")
        time.sleep(0.2) # API 통신 제한(Rate Limit) 방어용 딜레이
    logger.info("-" * 50)
    return holdings

def evaluate_trading_signals(vix_price, holdings):
    """매매 판단 로직 실행"""
    logger.info("🧠 매매 조건 탐색 중...")
    if vix_price is not None and isinstance(vix_price, (int, float)) and vix_price >= 20.0:
        if "114800" not in holdings:
            logger.info("🚨 공포장(VIX 20↑) 감지! 인버스 매수 시그널 발생!")
            telegram_msg.send_message("🚨 시장 공포 감지: KODEX 인버스 매수 로직 진입")
            # api_kis.buy_market_order("114800", 10) 
        else:
            logger.info("  -> 이미 인버스를 보유 중입니다.")
    else:
        logger.info("  -> 뚜렷한 매매 시그널이 없어 관망합니다.")
    logger.info("=" * 50)

def main():
    global last_global_check_time, cached_vix_price
    
    start_msg = "🚀 KIS_AUTO_TRADER_PRO 가동 시작! (10분 주기 글로벌 지표 캐싱 적용)"
    logger.info(start_msg)
    telegram_msg.send_message(start_msg) 

    while True:
        try:
            # 1. 휴식 시간 체크
            if not TEST_MODE and not is_market_open():
                logger.info("💤 장 마감/휴장 시간입니다. 1분 후 다시 체크합니다.")
                time.sleep(60) 
                continue 

            logger.info("=" * 50)
            logger.info("📊 시스템 상태 점검")
            
            # 2. 글로벌 지표 확인 (10분에 1번만 실행)
            current_time = time.time()
            if current_time - last_global_check_time >= GLOBAL_UPDATE_INTERVAL:
                # 10분이 지났을 때만 API를 호출하여 갱신
                cached_vix_price = check_global_indicators()
                last_global_check_time = current_time
            else:
                # 10분이 안 지났으면 남은 시간 표시
                remain_time = int(GLOBAL_UPDATE_INTERVAL - (current_time - last_global_check_time))
                logger.info(f"🌍 [미국/글로벌 지표] (다음 갱신까지 {remain_time}초 남음)")
            
            time.sleep(0.5) 
            
            # 3. 계좌 및 타겟 종목 확인 (매 사이클마다 실행)
            holdings = check_account_and_targets()
            
            # 4. 매매 판단 로직 실행 (캐싱된 VIX 데이터 사용)
            evaluate_trading_signals(cached_vix_price, holdings)

        except Exception as e:
            logger.error(f"⚠️ 봇 에러 발생: {e}")
            telegram_msg.send_message(f"🚨 봇 에러 발생: {e}")

        logger.info("⏳ 30초 대기 중...\n")
        time.sleep(30)

if __name__ == "__main__":
    main()