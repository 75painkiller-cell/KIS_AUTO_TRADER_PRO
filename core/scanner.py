import os
import requests
import json
from dotenv import load_dotenv
import sys

# 경로 세팅
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from auth import KISTokenManager
from utils.my_logger import logger

load_dotenv()
APP_KEY = os.getenv("KIS_APP_KEY")
APP_SECRET = os.getenv("KIS_APP_SECRET")
URL_BASE = "https://openapi.koreainvestment.com:9443"

def get_hot_symbols(limit=15):
    """
    한투 API를 호출하여 당일 거래량 상위 종목 코드를 자동 추출합니다.
    (1,000원 이상 종목만 필터링하여 동전주 제외)
    """
    token_manager = KISTokenManager()
    token = token_manager.get_access_token()
    
    if not token:
        logger.error("❌ 토큰이 없어 급등주 탐색을 실패했습니다.")
        return []

    url = f"{URL_BASE}/uapi/domestic-stock/v1/quotations/volume-rank"
    
    headers = {
        "content-type": "application/json; charset=utf-8",
        "authorization": f"Bearer {token}",
        "appkey": APP_KEY,
        "appsecret": APP_SECRET,
        "tr_id": "FHPST01710000",  # 거래량 상위 조회 TR ID
        "custtype": "P"
    }
    
    params = {
        "FID_COND_MRKT_DIV_CODE": "0000",      # 0000: 전체 (코스피+코스닥)
        "FID_COND_SCR_DIV_CODE": "20171",      # 고정값
        "FID_INPUT_ISCD": "0000",              # 고정값
        "FID_DIV_CLS_CODE": "0",               # 0: 전체
        "FID_BLNG_CLS_CODE": "0",              # 0: 전체
        "FID_TRGT_CLS_CODE": "111111111",      # 1: 증거금 20~100% 전체 포함
        "FID_TRGT_EXLS_CLS_CODE": "0000000000",# 제외 조건 없음
        "FID_INPUT_PRICE_1": "1000",           # 최저가: 1,000원 (동전주 제외)
        "FID_INPUT_PRICE_2": "500000",         # 최고가: 500,000원 
        "FID_VOL_CNT": "0",                    # 거래량 제한 없음
        "FID_INPUT_DATE_1": ""
    }

    try:
        res = requests.get(url, headers=headers, params=params)
        if res.status_code == 200:
            data = res.json()
            items = data.get("output", [])
            
            hot_symbols = []
            for item in items:
                symbol = item.get("stck_shrn_iscd")  # 종목코드
                name = item.get("hts_kor_isnm")      # 종목명
                
                if symbol:
                    hot_symbols.append(symbol)
                    
                if len(hot_symbols) >= limit:
                    break
            
            logger.info(f"🔍 [자동 탐색 완료] 거래량 상위 {len(hot_symbols)}개 종목 장전 완료!")
            return hot_symbols
        else:
            logger.error(f"❌ 급등주 탐색 실패: {res.text}")
            return []
            
    except Exception as e:
        logger.error(f"⚠️ 급등주 탐색 중 에러 발생: {e}")
        return []

# 단독 테스트용
if __name__ == "__main__":
    symbols = get_hot_symbols(15)
    print(f"추출된 종목 코드: {symbols}")