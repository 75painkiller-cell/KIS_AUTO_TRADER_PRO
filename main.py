import sys
import os
import time
from datetime import datetime
import threading
import asyncio

current_dir = os.path.dirname(os.path.abspath(__file__))
for folder in ['core', 'data', 'risk', 'utils']:
    folder_path = os.path.join(current_dir, folder)
    if folder_path not in sys.path:
        sys.path.append(folder_path)

from data import global_data
from utils.my_logger import logger
from utils import telegram_msg
from utils import discord
from utils.database import init_db
from core import strategy
from core import scheduler
from auth import KISTokenManager  
from core.ws_engine import KISWebsocketEngine  
from core import scanner  

last_global_check_time = 0
GLOBAL_UPDATE_INTERVAL = 600

def check_global_indicators():
    logger.info("🌍 [미국/글로벌 지표]")
    nq_price = global_data.get_nasdaq_futures()
    vix_price = global_data.get_vix()
    usdkrw = global_data.get_usdkrw()
    sox = global_data.get_sox()
    us10y = global_data.get_us_10y_yield()
    btc = global_data.get_bitcoin()

    logger.info(f" ▶ 나스닥: {nq_price} / VIX: {vix_price} / 환율: {usdkrw}")
    
    discord.send_embed_message(
        title="🌍 장전 글로벌 주요 지표",
        description="현재 해외 증시 및 경제 지표 현황입니다.",
        color=3066993,
        fields=[
            {"name": "나스닥 선물", "value": str(nq_price), "inline": True},
            {"name": "VIX 공포지수", "value": str(vix_price), "inline": True},
            {"name": "원달러 환율", "value": str(usdkrw), "inline": True},
            {"name": "반도체(SOX)", "value": str(sox), "inline": True},
            {"name": "국채금리(10Y)", "value": str(us10y), "inline": True},
            {"name": "비트코인", "value": str(btc), "inline": True}
        ]
    )
    logger.info("-" * 50)

def run_websocket_engine():
    engine = KISWebsocketEngine()
    target_symbols = []

    while not target_symbols:
        logger.info("🔍 실시간 감시할 거래량 상위 종목을 탐색합니다...")
        target_symbols = scanner.get_hot_symbols(15)
        
        if not target_symbols:
            logger.info("⏳ 아직 장 열리기 전이거나 탐색된 종목이 없습니다. 1분 후 다시 시도합니다.")
            time.sleep(60)

    logger.info(f"🕸️ [투트랙 가동] 핫한 급등주 {len(target_symbols)}개 실시간 감시(웹소켓) 시작!")
    asyncio.run(engine.connect_and_listen(target_symbols))

def main():
    global last_global_check_time
    
    init_db()

    start_msg = "🚀 KIS 자동 매매 봇이 투트랙 시스템으로 시작되었습니다."
    logger.info(start_msg)
    telegram_msg.send_message(start_msg)
    
    discord.send_embed_message(
        title="🚀 KIS 자동 매매 봇 가동",
        description="투트랙(스윙 + 고래 탐지) 시스템이 정상적으로 시작되었습니다.",
        color=3447003,
        fields=[
            {"name": "상태", "value": "장 개장 대기 중", "inline": True},
            {"name": "감시 방식", "value": "자동 스캐너 연동", "inline": True}
        ]
    )

    token_manager = KISTokenManager()
    initial_token = token_manager.get_access_token()
    if not initial_token:
        err_msg = "❌ 초기 KIS API 접근 토큰 발급 실패! 앱키와 시크릿 설정을 확인해주세요."
        logger.error(err_msg)
        telegram_msg.send_message(err_msg)
        return  

    logger.info("✅ KIS API 인증 토큰 정상 발급 완료. 20초 추세 메인 루프를 시작합니다.")

    while True:
        try:
            now = datetime.now()

            current_timestamp = time.time()
            if current_timestamp - last_global_check_time >= GLOBAL_UPDATE_INTERVAL:
                check_global_indicators()
                last_global_check_time = current_timestamp

            if not scheduler.is_market_open(now) and not getattr(strategy, 'IS_TEST_MODE', False):
                logger.info("⏳ 현재 장 외 시간 또는 공휴일입니다. 20초 후 다시 확인합니다.")
                time.sleep(20)
                continue

            if now.strftime("%H%M%S") >= "150000" and not getattr(strategy, 'IS_TEST_MODE', False):
                logger.info("🛑 15시 이후이므로 신규 매매를 진행하지 않습니다.")
                time.sleep(20)
                continue

            strategy.execute_trading_logic(now)

        except Exception as e:
            logger.error(f"⚠️ 봇 에러 발생: {e}")
            telegram_msg.send_message(f"⚠️ 봇 에러 발생: {e}")

        time.sleep(20) 

if __name__ == "__main__":
    ws_thread = threading.Thread(target=run_websocket_engine, daemon=True)
    ws_thread.start()
    main()