import requests
import json

APP_KEY = "본인의_앱키를_입력하세요"
APP_SECRET = "본인의_시크릿키를_입력하세요"
URL_BASE = "https://openapi.koreainvestment.com:9443" # 실전투자 URL

def get_access_token():
    """REST API용 24시간 접근 토큰 발급"""
    headers = {"content-type": "application/json"}
    body = {
        "grant_type": "client_credentials",
        "appkey": APP_KEY,
        "appsecret": APP_SECRET
    }
    url = f"{URL_BASE}/oauth2/tokenP"
    res = requests.post(url, headers=headers, data=json.dumps(body))
    return res.json().get("access_token")

def get_ws_approval_key():
    """실시간 웹소켓(시세) 접속키 발급"""
    headers = {"content-type": "application/json"}
    body = {
        "grant_type": "client_credentials",
        "appkey": APP_KEY,
        "secretkey": APP_SECRET
    }
    url = f"{URL_BASE}/oauth2/Approval"
    res = requests.post(url, headers=headers, data=json.dumps(body))
    return res.json().get("approval_key")