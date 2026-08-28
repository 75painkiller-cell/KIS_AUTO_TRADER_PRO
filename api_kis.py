import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()
APP_KEY = os.getenv("KIS_APP_KEY")
APP_SECRET = os.getenv("KIS_APP_SECRET")
ACCOUNT_NUM = os.getenv("KIS_ACCOUNT_NUM")

URL_BASE = "https://openapivts.koreainvestment.com:29443" 
ACCESS_TOKEN = ""

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
    
    holdings = []
    for item in data['output1']:
        if int(item['hldg_qty']) > 0:
            buy_price = float(item['pchs_avg_pric'])
            current_price = float(item['prpr'])
            qty = int(item['hldg_qty'])
            profit_amt = int(item['evlu_pfls_amt']) 
            tax = int(((current_price - buy_price) * qty) - profit_amt)
            
            holdings.append({
                "name": item['prdt_name'],
                "buy_price": buy_price,
                "price": current_price,
                "qty": qty,
                "rt": float(item['evlu_pfls_rt']), 
                "profit_amt": profit_amt,
                "tax": tax
            })
            
    return total_asset, total_profit, holdings

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
            print(f"⚠️ 현재가 조회 API 거부: {data.get('msg1', '알 수 없는 오류')}")
            return None
    except Exception as e:
        print(f"⚠️ 현재가 조회 통신 에러: {e}")
        return None
def order_cash(code, qty, is_buy=True):
    """
    국내 주식 시장가 매수/매도 주문 (모의투자 전용)
    - is_buy=True: 매수 / is_buy=False: 매도
    """
    if not ACCESS_TOKEN:
        get_token()

    url = f"{URL_BASE}/uapi/domestic-stock/v1/trading/order-cash"
    
    # 모의투자(VTS) 현금 주문 TR_ID (매수: VTTC0802U, 매도: VTTC0801U)
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
        "ORD_DVSN": "01", # 01: 시장가
        "ORD_QTY": str(qty),
        "ORD_UNPR": "0"   # 시장가 주문 시 단가는 0
    }
    
    try:
        res = requests.post(url, headers=headers, data=json.dumps(body), timeout=5)
        res.raise_for_status()
        data = res.json()
        
        order_side = "매수" if is_buy else "매도"
        
        if data.get('rt_cd') == '0':
            print(f"✅ [주문 성공] {code} {qty}주 시장가 {order_side} 접수 완료")
            return True
        else:
            print(f"❌ [주문 실패] {code} {order_side}: {data.get('msg1', '에러 사유 알 수 없음')}")
            return False
    except Exception as e:
        print(f"⚠️ 주문 API 통신 에러: {e}")
        return False

def buy_market_order(code, qty):
    """시장가 매수"""
    return order_cash(code, qty, is_buy=True)

def sell_market_order(code, qty):
    """시장가 매도"""
    return order_cash(code, qty, is_buy=False)