import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()
APP_KEY = os.getenv("KIS_APP_KEY")
APP_SECRET = os.getenv("KIS_APP_SECRET")
ACCOUNT_NUM = os.getenv("KIS_ACCOUNT_NUM")

# 모의투자(VTS) URL입니다. 실전 시 https://openapi.koreainvestment.com:9443 로 변경
URL_BASE = "https://openapivts.koreainvestment.com:29443" 

ACCESS_TOKEN = ""

def get_token():
    """한국투자증권 API 접근 토큰 발급"""
    global ACCESS_TOKEN
    url = f"{URL_BASE}/oauth2/tokenP"
    headers = {"content-type": "application/json"}
    body = {
        "grant_type": "client_credentials",
        "appkey": APP_KEY,
        "appsecret": APP_SECRET
    }
    res = requests.post(url, headers=headers, data=json.dumps(body))
    
    if res.status_code == 200:
        ACCESS_TOKEN = res.json().get("access_token")
        print("✅ KIS API 토큰 발급 성공")
    else:
        raise Exception(f"토큰 발급 실패: {res.text}")

def get_balance():
    """실제 계좌 잔고 및 보유 종목 조회"""
    if not ACCESS_TOKEN:
        get_token()

    url = f"{URL_BASE}/uapi/domestic-stock/v1/trading/inquire-balance"
    headers = {
        "Content-Type": "application/json",
        "authorization": f"Bearer {ACCESS_TOKEN}",
        "appKey": APP_KEY,
        "appSecret": APP_SECRET,
        "tr_id": "VTTC8434R" # 실전투자 전환 시 'TTTC8434R'로 변경
    }
    
    # 계좌번호 포맷팅 (앞 8자리, 뒤 2자리 분리)
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
    
    res = requests.get(url, headers=headers, params=params)
    if res.status_code != 200:
        raise Exception(f"잔고 조회 실패: {res.text}")
        
    data = res.json()
    
    # 총 자산 및 평가 손익 (세후)
    total_asset = int(data['output2'][0]['tot_evlu_amt'])
    total_profit = int(data['output2'][0]['evlu_pfls_smtl_amt'])
    
    # 보유 종목 리스트 정리
    holdings = []
    for item in data['output1']:
        if int(item['hldg_qty']) > 0: # 1주라도 보유한 종목만
            buy_price = float(item['pchs_avg_pric'])
            current_price = float(item['prpr'])
            qty = int(item['hldg_qty'])
            
            # API에서 제공하는 찐 세후 손익
            profit_amt = int(item['evlu_pfls_amt']) 
            
            # 텔레그램 포맷을 맞추기 위한 매도 제세금 역산 = (단순차액) - (세후손익)
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