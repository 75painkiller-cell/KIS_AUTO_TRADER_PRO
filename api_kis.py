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