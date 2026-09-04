import requests
import json

# ==========================================
# 1. API 키 및 기본 설정 (본인 정보로 수정)
# ==========================================
APP_KEY = "본인의_앱키를_입력하세요"
APP_SECRET = "본인의_시크릿키를_입력하세요"

# 실전투자(오전 9시~오후 3시 30분) 기준 URL
# 모의투자인 경우 https://openapivts.koreainvestment.com:29443 로 변경
URL_BASE = "https://openapi.koreainvestment.com:9443" 

# ==========================================
# 2. REST API 접근 토큰 발급 (매매, 조건검색용)
# ==========================================
def get_access_token():
    """조건검색, 매수/매도 등 REST API를 사용하기 위한 24시간용 토큰 발급"""
    headers = {"content-type": "application/json"}
    body = {
        "grant_type": "client_credentials",
        "appkey": APP_KEY,
        "appsecret": APP_SECRET
    }
    url = f"{URL_BASE}/oauth2/tokenP"
    
    res = requests.post(url, headers=headers, data=json.dumps(body))
    access_token = res.json().get("access_token")
    print("[API] REST 토큰 발급 완료")
    return access_token

# ==========================================
# 3. 실시간 웹소켓 접속키 발급 (시세 수신용)
# ==========================================
def get_ws_approval_key():
    """실시간 체결가를 0.1초 단위로 받기 위한 웹소켓 전용 접속키 발급"""
    headers = {"content-type": "application/json"}
    body = {
        "grant_type": "client_credentials",
        "appkey": APP_KEY,
        "secretkey": APP_SECRET
    }
    url = f"{URL_BASE}/oauth2/Approval"
    
    res = requests.post(url, headers=headers, data=json.dumps(body))
    approval_key = res.json().get("approval_key")
    print("[API] 웹소켓 접속키 발급 완료")
    return approval_key

# ==========================================
# 4. 조건검색 결과 조회 (t8427 연동)
# ==========================================
def fetch_real_condition_stocks(access_token, condition_id):
    """실제 HTS 조건검색식 결과를 조회하여 종목 코드 리스트 반환"""
    # 이 부분은 한투 API의 t8427 혹은 t8436 TR 호출 로직으로 채워집니다.
    # (한국투자증권 API 구조상 조건식 고유번호 입력 필요)
    pass