import os
import requests
import json
from dotenv import load_dotenv

# .env 파일에서 키값 불러오기
load_dotenv()
APP_KEY = os.getenv("KIS_APP_KEY")
APP_SECRET = os.getenv("KIS_APP_SECRET")

print("--- [한국투자증권 API 연결 테스트] ---")
if not APP_KEY or not APP_SECRET:
    print("❌ 오류: .env 파일에서 키값을 찾을 수 없습니다. 파일 내용과 이름을 확인해 주세요.")
    exit()

print(f"🔑 앱 키 로드 완료: {APP_KEY[:5]}... (보안을 위해 앞부분만 표시)")

# 접근 토큰(Access Token) 발급 요청
URL = "https://openapi.koreainvestment.com:9443/oauth2/tokenP"
headers = {"content-type": "application/json"}
body = {
    "grant_type": "client_credentials",
    "appkey": APP_KEY,
    "appsecret": APP_SECRET
}

try:
    print("⏳ 증권사 서버로 토큰 발급을 요청합니다...")
    res = requests.post(URL, headers=headers, data=json.dumps(body))
    
    if res.status_code == 200 and "access_token" in res.json():
        print("✅ 성공: 한국투자증권 서버와 완벽하게 연결되었습니다! (토큰 발급 완료)")
    else:
        print("❌ 실패: 키값이 잘못되었거나 권한이 없습니다.")
        print(f"상세 에러: {res.text}")
        
except Exception as e:
    print(f"❌ 실패: 통신 중 에러가 발생했습니다. ({e})")