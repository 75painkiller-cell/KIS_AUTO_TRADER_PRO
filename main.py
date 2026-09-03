import os
import asyncio
import requests
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

from core.auth import KISTokenManager
from core.order import execute_order  # ✅ 분리된 주문 함수 불러오기
from utils.my_logger import logger

load_dotenv()
APP_KEY = os.getenv("KIS_APP_KEY")
APP_SECRET = os.getenv("KIS_APP_SECRET")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
BASE_URL = "https://openapivts.koreainvestment.com:29443"

ACCESS_TOKEN = "" 

def send_discord_message(msg):
    if DISCORD_WEBHOOK_URL:
        try:
            requests.post(DISCORD_WEBHOOK_URL, json={"content": msg})
        except Exception as e:
            logger.error(f"디스코드 전송 실패: {e}")

def get_3min_trend_data(stock_code):
    """KIS API로 3분봉 데이터를 가져와 MA5, MA15, VWAP를 계산합니다."""
    url = f"{BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-time-itemchartprice"
    headers = {
        "Content-Type": "application/json",
        "authorization": f"Bearer {ACCESS_TOKEN}",
        "appKey": APP_KEY,
        "appSecret": APP_SECRET,
        "tr_id": "FHKST03010200", 
        "custtype": "P"
    }
    params = {
        "FID_ETC_CLS_CODE": "",
        "FID_COND_MRKT_DIV_CODE": "J",
        "FID_INPUT_ISCD": stock_code,
        "FID_INPUT_HOUR_1": "153000",
        "FID_PW_DATA_INCU_YN": "N"
    }
    
    try:
        res = requests.get(url, headers=headers, params=params, timeout=3)
        if res.status_code != 200: return None
        data = res.json().get('output2', [])
        if not data: return None

        df = pd.DataFrame(data)
        df = df[['stck_bsop_date', 'stck_cntg_hour', 'stck_prpr', 'stck_hgpr', 'stck_lwpr', 'cntg_vol']]
        df.columns = ['date', 'time', 'close', 'high', 'low', 'volume']
        df = df.astype({'close': 'float', 'high': 'float', 'low': 'float', 'volume': 'float'})
        
        df = df.sort_values(by=['date', 'time']).reset_index(drop=True)
        df['MA5'] = df['close'].rolling(window=5).mean()
        df['MA15'] = df['close'].rolling(window=15).mean()
        df['typical_price'] = (df['high'] + df['low'] + df['close']) / 3
        df['cum_vol_price'] = (df['typical_price'] * df['volume']).cumsum()
        df['cum_volume'] = df['volume'].cumsum()
        df['VWAP'] = df['cum_vol_price'] / df['cum_volume']
        df['vol_surge'] = df['volume'] > (df['volume'].shift(1) * 2)

        return df
    except Exception as e:
        return None

async def main_trading_loop(target_stocks):
    logger.info("🟩 3분봉 데이트레이딩 메인 루프를 시작합니다.")
    await asyncio.to_thread(send_discord_message, "🟢 KIS 모의투자: 3분봉 데이트레이딩 루프 시작")
    
    holding_stocks = []
    
    while True:
        # 1. 보유 종목 매도(데드크로스) 감시
        for stock_code in holding_stocks[:]:
            df = await asyncio.to_thread(get_3min_trend_data, stock_code)
            if df is None or len(df) < 15: continue
                
            current = df.iloc[-1]
            if current['MA5'] < current['MA15']:
                msg = f"📉 [매도 신호] {stock_code} | 현재가: {current['close']} (데드크로스)"
                logger.info(msg)
                await asyncio.to_thread(send_discord_message, msg)
                await asyncio.to_thread(execute_order, stock_code, ACCESS_TOKEN, "sell", "1")
                holding_stocks.remove(stock_code)

        # 2. 신규 종목 매수(추세/VWAP/거래량) 감시
        for stock_code in target_stocks[:]: 
            if stock_code in holding_stocks: continue
                
            df = await asyncio.to_thread(get_3min_trend_data, stock_code)
            if df is None or len(df) < 15: continue
                
            current = df.iloc[-1]
            close_price, vwap = current['close'], current['VWAP']
            ma5, ma15 = current['MA5'], current['MA15']
            
            is_uptrend = ma5 > ma15
            is_above_vwap = close_price > vwap
            is_volume_surged = current['vol_surge']
            
            if is_uptrend and is_above_vwap and is_volume_surged:
                msg = f"🚀 [매수 조건 포착] {stock_code} | 현재가: {close_price} | VWAP: {vwap:.2f}"
                logger.info(msg)
                await asyncio.to_thread(send_discord_message, msg)
                
                await asyncio.to_thread(execute_order, stock_code, ACCESS_TOKEN, "buy", "1")
                
                holding_stocks.append(stock_code)
                target_stocks.remove(stock_code)
                
        await asyncio.sleep(1.5)

async def main():
    logger.info("🚀 KIS_AUTO_TRADER_PRO 모의투자 데이트레이딩 모드로 시작되었습니다.")
    
    global ACCESS_TOKEN
    token_manager = KISTokenManager()
    ACCESS_TOKEN = token_manager.get_access_token()
    
    if not ACCESS_TOKEN:
        logger.error("❌ 토큰 발급 실패로 종료합니다.")
        return

    logger.info("🔍 [자동 탐색 완료] 거래량 상위 종목 장전 완료!")
    target_stocks = ["005930", "000660"] 
    
    await main_trading_loop(target_stocks)

if __name__ == "__main__":
    asyncio.run(main())