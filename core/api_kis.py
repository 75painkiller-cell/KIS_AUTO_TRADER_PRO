import os
import requests
import json
import time
from functools import wraps
from dotenv import load_dotenv
import yfinance as yf
import pandas as pd
from my_logger import logger

load_dotenv()
APP_KEY = os.getenv("KIS_APP_KEY")
APP_SECRET = os.getenv("KIS_APP_SECRET")
ACCOUNT_NUM = os.getenv("KIS_ACCOUNT_NUM")

URL_BASE = "https://openapivts.koreainvestment.com:29443" 
ACCESS_TOKEN = ""

ETF_FEE_RATE = 0.015  # KIS ETF 매매 수수료율

def api_retry(max_retries=3, delay=2.0):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(1, max_retries + 1):
                try:
                    result = func(*args, **kwargs)
                    if result is None:
                        raise ValueError("API 응답 데이터가 비어 있습니다.")
                    return result
                except Exception as e:
                    logger.warning(f"⚠️ [{func.__name__}] API 호출 오류: {e} (재시도 {attempt}/{max_retries})")
                    if attempt == max_retries:
                        logger.error(f"❌ [{func.__name__}] 최대 재시도 횟수 초과. 처리 실패.")
                        if func.__name__ == 'get_balance':
                            return 0, 0, {}
                        return None
                    time.sleep(delay * attempt)
            return None
        return wrapper
    return decorator

def get_token():
    global ACCESS_TOKEN
    url = f"{URL_BASE}/oauth2/tokenP"
    headers = {"content-type": "application/json"}
    body = {
        "grant_type": "client_credentials",
        "appkey": APP_KEY,
        "appsecret": APP_SECRET
    }
    try:
        res = requests.post(url, headers=headers, data=json.dumps(body), timeout=5)
    except Exception as e:
        raise Exception(f"토큰 발급 통신 에러: {e}")
        
    if res.status_code == 200:
        ACCESS_TOKEN = res.json().get("access_token")
    else:
        raise Exception(f"토큰 발급 실패: {res.text}")

@api_retry(max_retries=3, delay=2.0)
def get_balance():
    if not ACCESS_TOKEN:
        get_token()

    url = f"{URL_BASE}/uapi/domestic-stock/v1/trading/inquire-balance"
    headers = {
        "Content-Type": "application/json",
        "authorization": f"Bearer {ACCESS_TOKEN}",
        "appKey": APP_KEY,
        "appSecret": APP_SECRET,
        "tr_id": "VTTC8434R"
    }
    
    cano = ACCOUNT_NUM[:8] if ACCOUNT_NUM else ""
    acnt_prdt_cd = ACCOUNT_NUM[-2:] if ACCOUNT_NUM else ""

    params = {
        "CANO": cano,
        "ACNT_PRDT_CD": acnt_prdt_cd,
        "AFHR_FLPR_YN": "N",
        "OFL_YN": "",
        "INQR_DVSN": "02",
        "UNPR_DVSN": "01",
        "FUND_STTL_ICLD_YN": "N",
        "FNCG_AMT_AUTO_RDPT_YN": "N",
        "PRCS_DVSN": "01",
        "CTX_AREA_FK100": "",
        "CTX_AREA_NK100": ""
    }
    
    try:
        res = requests.get(url, headers=headers, params=params, timeout=5)
    except Exception as e:
        raise Exception(f"잔고 조회 통신 에러: {e}")
        
    if res.status_code != 200:
        raise Exception(f"HTTP 통신 실패: {res.text}")
        
    data = res.json()
    if data.get("rt_cd") != "0":
        raise Exception(f"KIS API 거부: {data.get('msg1', '알 수 없는 오류')} (코드: {data.get('rt_cd')})")
    
    total_asset = int(data['output2'][0]['tot_evlu_amt'])
    total_profit = int(data['output2'][0]['evlu_pfls_smtl_amt'])
    
    holdings = {}
    for item in data['output1']:
        if int(item['hldg_qty']) > 0:
            buy_price = float(item['pchs_avg_pric'])
            current_price = float(item['prpr'])
            qty = int(item['hldg_qty'])
            
            holdings[item['pdno']] = {
                "name": item['prdt_name'],
                "avg": buy_price,
                "price": current_price,
                "qty": qty,
                "net_pl": float(item['evlu_pfls_rt'])
            }
            
    return total_asset, total_profit, holdings

@api_retry(max_retries=3, delay=2.0)
def get_current_price(code):
    if not ACCESS_TOKEN:
        get_token()
        
    url = f"{URL_BASE}/uapi/domestic-stock/v1/quotations/inquire-price" 
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "authorization": f"Bearer {ACCESS_TOKEN}",
        "appkey": APP_KEY,
        "appsecret": APP_SECRET,
        "tr_id": "FHKST01010100"
    }
    params = {
        "FID_COND_MRKT_DIV_CODE": "J",
        "FID_INPUT_ISCD": code
    }
    
    try:
        res = requests.get(url, headers=headers, params=params, timeout=5)
        res.raise_for_status()
        data = res.json()
        
        if data.get('rt_cd') == '0':
            return int(data['output']['stck_prpr'])
        else:
            logger.warning(f"⚠️ 현재가 조회 API 거부: {data.get('msg1', '알 수 없는 오류')}")
            return None
    except Exception as e:
        logger.warning(f"⚠️ 현재가 조회 통신 에러: {e}")
        return None

@api_retry(max_retries=3, delay=2.0)
def order_cash(code, qty, is_buy=True):
    if not ACCESS_TOKEN:
        get_token()

    url = f"{URL_BASE}/uapi/domestic-stock/v1/trading/order-cash"
    tr_id = "VTTC0802U" if is_buy else "VTTC0801U"
    
    headers = {
        "Content-Type": "application/json",
        "authorization": f"Bearer {ACCESS_TOKEN}",
        "appKey": APP_KEY,
        "appSecret": APP_SECRET,
        "tr_id": tr_id
    }
    
    cano = ACCOUNT_NUM[:8] if ACCOUNT_NUM else ""
    acnt_prdt_cd = ACCOUNT_NUM[-2:] if ACCOUNT_NUM else ""

    body = {
        "CANO": cano,
        "ACNT_PRDT_CD": acnt_prdt_cd,
        "PDNO": code,
        "ORD_DVSN": "01", 
        "ORD_QTY": str(qty),
        "ORD_UNPR": "0"   
    }
    
    try:
        res = requests.post(url, headers=headers, data=json.dumps(body), timeout=5)
        res.raise_for_status()
        data = res.json()
        
        order_side = "매수" if is_buy else "매도"
        
        if data.get('rt_cd') == '0':
            logger.info(f"✅ [주문 성공] {code} {qty}주 시장가 {order_side} 접수 완료")
            return True
        else:
            logger.warning(f"❌ [주문 실패] {code} {order_side}: {data.get('msg1', '에러 사유 알 수 없음')}")
            return False
    except Exception as e:
        logger.warning(f"⚠️ 주문 API 통신 에러: {e}")
        return False

def send_order(symbol, is_buy, qty, price=0, name=""):
    return order_cash(symbol, qty, is_buy)

def calculate_indicators(code):
    try:
        ticker = f"{code}.KS"
        df = yf.download(ticker, period="3mo", interval="1d", progress=False)
        
        if df.empty or len(df) < 26:
            return 0, 0, 0, 0, 0, 0, 0, 0
            
        close = df['Close'].squeeze()
        vol = int(df['Volume'].squeeze().iloc[-1])
        prev_close = float(close.iloc[-2])
        
        ma5 = float(close.rolling(window=5).mean().iloc[-1])
        ma20 = float(close.rolling(window=20).mean().iloc[-1])
        
        delta = close.diff()
        gain = delta.where(delta > 0, 0).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = float(100 - (100 / (1 + rs)).iloc[-1])
        
        std = close.rolling(window=20).std()
        bb_upper = float((ma20 + (std * 2)).iloc[-1])
        bb_lower = float((ma20 - (std * 2)).iloc[-1])
        
        exp1 = close.ewm(span=12, adjust=False).mean()
        exp2 = close.ewm(span=26, adjust=False).mean()
        macd = float((exp1 - exp2).iloc[-1])
        
        return ma5, ma20, rsi, vol, prev_close, bb_upper, bb_lower, macd
        
    except Exception as e:
        logger.warning(f"지표 계산 오류 ({code}): {e}")
        return 0, 0, 0, 0, 0, 0, 0, 0

def buy_market_order(code, qty):
    return order_cash(code, qty, is_buy=True)

def sell_market_order(code, qty):
    return order_cash(code, qty, is_buy=False)