<<<<<<< HEAD
import yaml
import asyncio
import datetime
import requests
import api_client

# 본인의 한투 HTS 접속 아이디 입력
HTS_USER_ID = "본인HTS아이디" 

def load_config(filepath="config.yaml"):
    """YAML 전략 설정 파일 로드"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"오류: {filepath} 파일을 찾을 수 없습니다.")
        return None

async def fetch_condition_stocks(access_token, seq_number, name):
    """실제 KIS HTS 조건검색식 결과 조회 API (t8427 역할)"""
    url = f"{api_client.URL_BASE}/uapi/domestic-stock/v1/quotations/psearch-result"
    headers = {
        "content-type": "application/json; charset=utf-8",
        "authorization": f"Bearer {access_token}",
        "appkey": api_client.APP_KEY,
        "appsecret": api_client.APP_SECRET,
        "tr_id": "HHKST03900400",
        "custtype": "P"
    }
    params = {
        "user_id": HTS_USER_ID,
        "seq": seq_number
    }

    # requests의 동기적 딜레이로 인한 병목을 막기 위해 비동기 백그라운드 실행
    loop = asyncio.get_event_loop()
    res = await loop.run_in_executor(None, lambda: requests.get(url, headers=headers, params=params))

    if res.status_code == 200:
        data = res.json()
        # 검색된 종목코드(code)만 추출
        return [item['code'] for item in data.get('output2', [])]
    else:
        print(f"[{name}] 조건검색 호출 실패: {res.text}")
        return []

async def monitor_strategy(strategy, access_token):
    """개별 전략의 종목 감시 루프"""
    name = strategy['name']
    cond_id = strategy['condition_id']
    interval = strategy['poll_interval_sec']
    
    print(f"▶ [{name}] 감시 시작 (조건식 번호: {cond_id} / 갱신주기: {interval}초)")
    
    while True:
        now = datetime.datetime.now().strftime("%H:%M:%S")
        
        # 1. KIS API로 실시간 조건검색 종목 리스트 확보
        target_stocks = await fetch_condition_stocks(access_token, cond_id, name)
        print(f"[{now}] [{name}] 포착 종목: {target_stocks}")
        
        # 2. 향후 여기에 웹소켓 실시간 현재가와 target_stocks를 비교하는 로직 추가
        
        # 3. KIS API 호출 제한(Rate Limit) 방지를 위한 대기
        await asyncio.sleep(interval)

async def main():
    print("=== KIS_AUTO_TRADER_PRO 통합 시스템 시작 ===")
    
    # 1. 환경 설정 로드
    bot_config = load_config("config.yaml")
    if not bot_config: return
    
    # 2. 한투 API 통신용 토큰 및 키 발급
    print("API 인증 토큰을 발급받습니다...")
    rest_token = api_client.get_access_token()
    ws_key = api_client.get_ws_approval_key()
    
    print(f"총 {len(bot_config['strategies'])}개의 전략 엔진을 가동합니다.\n" + "="*50)
    
    # 3. YAML에 등록된 개수만큼 비동기 감시 태스크 생성
    tasks = []
    for strat in bot_config['strategies']:
        tasks.append(monitor_strategy(strat, rest_token))
        
    # 4. 모든 전략 동시 실행 (병렬 처리)
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n시스템을 안전하게 종료합니다.")
=======
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
>>>>>>> b1b9734e225f6eb66fcecf0559fb07d6405e7acd
