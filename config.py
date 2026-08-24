import os
from dotenv import load_dotenv

load_dotenv() 

# -------------------------------
# 1. API 및 알림 보안 설정 (.env 연동)
# -------------------------------
APP_KEY = os.getenv("KIS_APP_KEY")
APP_SECRET = os.getenv("KIS_APP_SECRET")
ACCOUNT_NUMBER = os.getenv("KIS_ACCOUNT_NUMBER") # 예: "12345678-01"

# --- 추가된 부분: 계좌번호를 API가 요구하는 형식으로 자동 분리 ---
if ACCOUNT_NUMBER and "-" in str(ACCOUNT_NUMBER):
    CANO = ACCOUNT_NUMBER.split("-")[0]      # 앞 8자리
    ACNT_PRDT_CD = ACCOUNT_NUMBER.split("-")[1] # 뒤 2자리
else:
    CANO = str(ACCOUNT_NUMBER)[:8]
    ACNT_PRDT_CD = str(ACCOUNT_NUMBER)[8:]
# -------------------------------------------------------------

USE_TELEGRAM = True
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# -------------------------------
# 2. 계좌 및 환경 설정
# -------------------------------
# 모의투자 여부 (True: 모의투자 / False: 실전투자)
IS_PAPER = False
URL_BASE = "https://openapivts.koreainvestment.com:29443" if IS_PAPER else "https://openapi.koreainvestment.com:9443"

# -------------------------------
# 3. 3,000만 원 자금 운용 및 리스크 관리 설정
# -------------------------------
INVEST_RATIO = 0.5           # 현금 대비 투입 비율 (50%)
MAX_ORDER_AMOUNT = 5000000    # 1회 최대 진입 금액 (500만 원)
TAKE_PROFIT = 0.025          # 익절 기준 (+2.5%)
STOP_LOSS = -0.015           # 손절 기준 (-1.5%)
DAILY_MAX_LOSS = 600000      # 일일 최대 손실 한도 (-60만 원)

USE_TAKE_PROFIT = True       # 익절 사용 여부
USE_STOP_LOSS = True         # 손절 사용 여부

# -------------------------------
# 4. 선물 및 ETF 매매 종목 코드
# -------------------------------
TARGET_CODE = "069500"       # KODEX 200 (롱)
INVERSE_CODE = "252670"      # KODEX 200선물인버스2X (숏)
FUTURES_CODE = "101V3000"    # 지수선물 표준 코드 (또는 10100000)
ACCUMULATED_THRESHOLD = 400  # 3분 미결제약정 누적 변동량 임계치 (계약)