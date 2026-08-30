from datetime import datetime, timedelta
import requests
from utils.config import APP_KEY, APP_SECRET, URL_BASE
from utils.logger import error, info

_access_token = None
_token_expired = None

def get_access_token():
    global _access_token, _token_expired
    now = datetime.now()

    # 기존 토큰이 존재하고 만료 시간이 지나지 않았다면 재발급 없이 기존 토큰 반환 (캐싱)
    if _access_token and _token_expired and now < _token_expired:
        return _access_token

    url = f"{URL_BASE.rstrip('/')}/oauth2/tokenP"
    headers = {"content-type": "application/json"}
    body = {
        "grant_type": "client_credentials",
        "appkey": APP_KEY,
        "appsecret": APP_SECRET,
    }

    try:
        res = requests.post(url, headers=headers, json=body, timeout=10)
        
        # [수정된 부분] 상태 코드가 200일 때만 JSON으로 변환 (에러 페이지 파싱 방지)
        if res.status_code == 200:
            data = res.json()
            if "access_token" in data:
                _access_token = data["access_token"]
                # 한국투자증권 토큰은 보통 24시간 유효하나, 안전하게 6시간 주기로 갱신
                _token_expired = now + timedelta(hours=6)
                info("[인증] OAuth2 토큰 발급 성공")
                return _access_token
            else:
                error(f"[인증] 토큰 발급 응답에 access_token이 없습니다: {data}")
                return None
        else:
            # 200이 아닐 경우 상태 코드와 상세 메시지 로깅
            error(f"[인증] 토큰 발급 실패 (상태코드: {res.status_code}) - {res.text}")
            return None
            
    except Exception as e:
        error(f"[인증] 토큰 발급 예외 발생: {e}")
        return None