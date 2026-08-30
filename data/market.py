from datetime import datetime, timedelta
import time
import requests
from core.auth import get_access_token
from utils.config import APP_KEY, APP_SECRET, FUTURES_CODE, URL_BASE
from utils.logger import error, warning

# 캐시 관련 설정 (필요시 시세 데이터 캐싱용)
_daily_cache = {}
_daily_cache_time = {}
CACHE_SECONDS = 60


def get_current_price(code: str) -> int:
    """
    국내 주식 현재가(체결가)를 조회합니다.
    """
    time.sleep(0.1)  # 초당 호출 제한(Rate Limit) 방지
    access_token = get_access_token()
    if not access_token:
        return 0

    url = f"{URL_BASE.rstrip('/')}/uapi/domestic-stock/v1/quotations/inquire-price"
    headers = {
        "Content-Type": "application/json",
        "authorization": f"Bearer {access_token}",
        "appkey": APP_KEY,
        "appsecret": APP_SECRET,
        "tr_id": "FHKST01010100",
        "custtype": "P",
    }
    params = {
        "FID_COND_MRKT_DIV_CODE": "J",
        "FID_INPUT_ISCD": code,
    }

    try:
        res = requests.get(url, headers=headers, params=params, timeout=10)
        
        if res.status_code == 200:
            data = res.json()
            if data.get("rt_cd") == "0":
                price_str = data.get("output", {}).get("stck_prpr", "0")
                return int(price_str) if price_str else 0
            else:
                warning(f"[현재가] 조회 실패 ({code}): {data.get('msg1', '응답 에러')}")
        else:
            error(f"[현재가] HTTP 통신 실패 ({code}) [코드: {res.status_code}] - {res.text}")

    except Exception as e:
        error(f"[현재가] 조회 예외 ({code}): {e}", exc_info=True)

    return 0


def get_futures_price_and_oi(futures_code: str = FUTURES_CODE):
    """
    지수선물 현재가, 미결제약정(OI), 베이시스를 조회합니다.
    """
    time.sleep(0.1)  # 초당 호출 제한(Rate Limit) 방지
    access_token = get_access_token()
    if not access_token:
        return None

    url = f"{URL_BASE.rstrip('/')}/uapi/domestic-futureoption/v1/quotations/inquire-price"
    headers = {
        "Content-Type": "application/json",
        "authorization": f"Bearer {access_token}",
        "appkey": APP_KEY,
        "appsecret": APP_SECRET,
        "tr_id": "FHMIF10000000",
        "custtype": "P",
    }
    params = {
        "FID_COND_MRKT_DIV_CODE": "F",
        "FID_INPUT_ISCD": futures_code,
    }

    try:
        res = requests.get(url, headers=headers, params=params, timeout=10)
        
        if res.status_code == 200:
            data = res.json()
            if data.get("rt_cd") == "0":
                out = data.get("output", {})
                
                # 안전한 형변환 처리
                price_val = float(out.get("futs_prpr", 0.0) or 0.0)
                oi_val = int(float(out.get("open_unpr", 0) or 0))
                basis_val = float(out.get("futs_diff_prpr", 0.0) or 0.0)

                return {
                    "price": price_val,
                    "open_interest": oi_val,
                    "basis": basis_val,
                }
            else:
                warning(f"[선물시세] 조회 실패 ({futures_code}): {data.get('msg1', '응답 에러')}")
        else:
            error(f"[선물시세] HTTP 통신 실패 ({futures_code}) [코드: {res.status_code}] - {res.text}")

    except Exception as e:
        error(f"[선물시세] 조회 예외 ({futures_code}): {e}", exc_info=True)

    return None