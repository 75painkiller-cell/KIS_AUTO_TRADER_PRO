import os
import requests
from dotenv import load_dotenv

load_dotenv()

APP_KEY = os.getenv("KIS_APP_KEY")
APP_SECRET = os.getenv("KIS_APP_SECRET")
ACCOUNT_NUM = os.getenv("KIS_ACCOUNT_NUM", "").replace("-", "")

CANO = ACCOUNT_NUM[:8]
ACNT_PRDT_CD = ACCOUNT_NUM[8:10] if len(ACCOUNT_NUM) >= 10 else "01"
URL_BASE = "https://openapivts.koreainvestment.com:29443"

# 1. 토큰 발급
res_token = requests.post(
    f"{URL_BASE}/oauth2/tokenP",
    json={
        "grant_type": "client_credentials",
        "appkey": APP_KEY,
        "appsecret": APP_SECRET,
    },
)
token = res_token.json().get("access_token")

if not token:
  print(f"[토큰 발급 실패] {res_token.json()}")
else:
  print("[토큰 발급 성공]")
  # 2. 잔고 조회
  headers = {
      "Content-Type": "application/json; charset=utf-8",
      "authorization": f"Bearer {token}",
      "appKey": APP_KEY,
      "appSecret": APP_SECRET,
      "tr_id": "VTTC8434R",
  }
  params = {
      "CANO": CANO,
      "ACNT_PRDT_CD": ACNT_PRDT_CD,
      "AFHR_FLPR_YN": "N",
      "OFL_YN": "",
      "INQR_DVSN": "02",
      "UNPR_DVSN": "01",
      "FUND_STTL_ICLD_YN": "N",
      "FND_TP_CD": "0",
      "PRCS_DVSN": "00",
      "CTX_AREA_FK100": "",
      "CTX_AREA_NK100": "",
  }
  res_bal = requests.get(
      f"{URL_BASE}/uapi/domestic-stock/v1/trading/inquire-balance",
      headers=headers,
      params=params,
  )
  data = res_bal.json()

  if data.get("rt_cd") != "0":
    print(f"[조회 실패] {data.get('msg1')}")
  else:
    summary = data.get("output2", [{}])[0]
    deposit = int(summary.get("dnca_tot_amt", 0))
    print(f"=== 잔고 조회 성공! 예수금 총액: {deposit:,}원 ===")