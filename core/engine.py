import asyncio
import datetime
import requests
import pandas as pd

from core.config import BASE_URL, APP_KEY, APP_SECRET, HTS_USER_ID
from core.auth import KISTokenManager
from core.order import execute_order
from utils.my_logger import logger
from utils.discord import send_discord_message

async def fetch_condition_stocks(access_token, seq_number, name):
    """실제 KIS HTS 조건검색식 결과 조회 API"""
    import os, requests
    url = "https://openapi.koreainvestment.com:9443/uapi/domestic-stock/v1/quotations/psearch-result"
    app_key = (os.getenv("KIS_APP_KEY") or "").strip()
    app_secret = (os.getenv("KIS_APP_SECRET") or "").strip()
    user_id = (os.getenv("HTS_USER_ID") or "@3084126").strip()
    headers = {
        "content-type": "application/json; charset=utf-8",
        "authorization": f"Bearer {str(access_token).strip()}",
        "appkey": app_key,
        "appsecret": app_secret,
        "tr_id": "HHKST03900400",
        "custtype": "P"
    }
    params = {
        "user_id": user_id,
        "seq": str(seq_number).strip()
    }
    try:
        res = await asyncio.to_thread(requests.get, url, headers=headers, params=params, timeout=5)
        if res.status_code == 200:
            data = res.json()
            return [item['code'] for item in data.get('output2', [])]
        else:
            logger.error(f"[{name}] 조건검색 호출 실패 ({res.status_code}): {res.text}")
            return []
    except Exception as e:
        logger.error(f"[{name}] 조건검색 통신 오류: {e}")
        return []

def get_3min_trend_data(stock_code, access_token):
    """KIS API로 3분봉 데이터를 가져와 MA5, MA15, VWAP를 계산합니다."""
    url = f"{BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-time-itemchartprice"
    headers = {
        "content-type": "application/json; charset=utf-8",
        "authorization": f"Bearer {str(access_token).strip()}",
        "appkey": str(APP_KEY).strip(),
        "appsecret": str(APP_SECRET).strip(),
        "tr_id": "FHKST03010200", 
        "custtype": "P"
    }
    params = {
        "FID_ETC_CLS_CODE": "",
        "FID_COND_MRKT_DIV_CODE": "J",
        "FID_INPUT_ISCD": str(stock_code).strip(),
        "FID_INPUT_HOUR_1": "153000",
        "FID_PW_DATA_INCU_YN": "N"
    }
    
    try:
        res = requests.get(url, headers=headers, params=params, timeout=7)
        if res.status_code != 200:
            return None
        data = res.json().get('output2', [])
        if not data:
            return None

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
        logger.error(f"분봉 데이터 분석 오류 ({stock_code}): {e}")
        return None

async def monitor_strategy_and_trade(strategy, access_token, dry_run=True):
    """YAML 전략 조건식 조회 및 데이트레이딩 루프 통합 관리 (Dry-Run 지원)"""
    name = strategy.get('name', '전략')
    cond_id = strategy.get('condition_id', '1')
    interval = strategy.get('poll_interval_sec', 10)
    
    mode_text = "[🧪 Dry-Run 가상매매]" if dry_run else "[⚡ 실전 주문]"
    logger.info(f"▶ {mode_text} [{name}] 감시 시작 (조건식 번호: {cond_id} / 갱신주기: {interval}초)")
    holding_stocks = []
    
    while True:
        target_stocks = await fetch_condition_stocks(access_token, cond_id, name)
        now = datetime.datetime.now().strftime("%H:%M:%S")
        logger.info(f"[{now}] [{name}] 포착 종목: {target_stocks}")
        
        # 보유 종목 매도 감시
        for stock_code in holding_stocks[:]:
            df = await asyncio.to_thread(get_3min_trend_data, stock_code, access_token)
            if df is None or len(df) < 15:
                continue
                
            current = df.iloc[-1]
            if current['MA5'] < current['MA15']:
                msg = f"📉 [매도 신호] {stock_code} | 현재가: {current['close']} (데드크로스)"
                logger.info(msg)
                await asyncio.to_thread(send_discord_message, msg)
                
                # 주문 분기: Dry-Run이면 가상 체결 로그만, False면 실제 증권사 주문
                if dry_run:
                    logger.info(f"🧪 [가상 매도 완료] {stock_code} 1주 가상 청산 처리")
                else:
                    await asyncio.to_thread(execute_order, stock_code, access_token, "sell", "1")
                    
                holding_stocks.remove(stock_code)

        # 신규 종목 매수 감시
        for stock_code in target_stocks[:]: 
            if stock_code in holding_stocks:
                continue
                
            df = await asyncio.to_thread(get_3min_trend_data, stock_code, access_token)
            if df is None or len(df) < 15:
                continue
                
            current = df.iloc[-1]
            close_price, vwap = current['close'], current['VWAP']
            ma5, ma15 = current['MA5'], current['MA15']
            
            if ma5 > ma15 and close_price > vwap and current['vol_surge']:
                msg = f"🚀 [매수 조건 포착] {stock_code} | 현재가: {close_price} | VWAP: {vwap:.2f}"
                logger.info(msg)
                await asyncio.to_thread(send_discord_message, msg)
                
                # 주문 분기: Dry-Run이면 가상 체결 로그만, False면 실제 증권사 주문
                if dry_run:
                    logger.info(f"🧪 [가상 매수 완료] {stock_code} 1주 가상 진입 처리 (실제 자금 사용 안 함)")
                else:
                    await asyncio.to_thread(execute_order, stock_code, access_token, "buy", "1")
                    
                holding_stocks.append(stock_code)
                
        await asyncio.sleep(interval)

async def run_trading_system(bot_config):
    access_token = KISTokenManager().get_access_token()
    if not access_token:
        logger.error("❌ 토큰 발급 실패로 종료합니다.")
        return

    strategies = bot_config.get('strategies', [])
    if not strategies:
        logger.error("❌ config.yaml에 'strategies' 설정이 없거나 비어 있습니다.")
        return

    # config.yaml의 DRY_RUN 설정값 읽기 (기본값: True로 안전 설정)
    dry_run = bot_config.get('DRY_RUN', True)
    mode_text = "🧪 [가상 매매(Dry-Run) 모드]" if dry_run else "⚡ [실전 매매 모드]"

    logger.info(f"총 {len(strategies)}개의 전략 엔진을 가동합니다. {mode_text}")
    await asyncio.to_thread(send_discord_message, f"🟢 KIS 자동 매매 시스템 가동 시작 {mode_text}")
    
    # 전략 엔진 실행 시 dry_run 플래그 전달
    tasks = [monitor_strategy_and_trade(strat, access_token, dry_run=dry_run) for strat in strategies]
    await asyncio.gather(*tasks)