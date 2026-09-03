import os
import requests
import json
from dotenv import load_dotenv
from utils.my_logger import logger

load_dotenv()
APP_KEY = os.getenv("KIS_APP_KEY")
APP_SECRET = os.getenv("KIS_APP_SECRET")
CANO = os.getenv("KIS_CANO")
ACNT_PRDT_CD = os.getenv("KIS_ACNT_PRDT_CD", "01")
BASE_URL = "https://openapivts.koreainvestment.com:29443"

def execute_order(stock_code, access_token, order_type="buy", qty="1"):
    """모의투자 시장가 매수/매도 실행"""
    url = f"{BASE_URL}/uapi/domestic-stock/v1/trading/order-cash"
    tr_id = "VTTC0802U" if order_type == "buy" else "VTTC0801U"
        
    headers = {
        "Content-Type": "application/json",
        "authorization": f"Bearer {access_token}",
        "appKey": APP_KEY,
        "appSecret": APP_SECRET,
        "tr_id": tr_id,
        "custtype": "P"
    }
    body = {
        "CANO": CANO,
        "ACNT_PRDT_CD": ACNT_PRDT_CD,
        "PDNO": stock_code,
        "ORD_DVSN": "01",
        "ORD_QTY": str(qty),
        "ORD_UNPR": "0"   
    }
    
    try:
        res = requests.post(url, headers=headers, data=json.dumps(body))
        result = res.json()
        if result.get('rt_cd') == '0':
            logger.info(f"✅ [모의투자 {order_type.upper()}] 주문 성공! 종목: {stock_code}, 수량: {qty}")
        else:
            logger.error(f"❌ [모의투자 {order_type.upper()}] 주문 실패: {result.get('msg1')}")
    except Exception as e:
        logger.error(f"⚠️ 주문 API 호출 중 에러: {e}")