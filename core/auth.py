import os
import requests
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
from utils.my_logger import logger

load_dotenv()
APP_KEY = os.getenv("KIS_APP_KEY")
APP_SECRET = os.getenv("KIS_APP_SECRET")
BASE_URL = "https://openapi.koreainvestment.com:9443"

class KISTokenManager:
    _instance = None
    access_token = None
    token_expired_at = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(KISTokenManager, cls).__new__(cls)
            cls._instance.access_token = None
            cls._instance.token_expired_at = None
        return cls._instance

    def get_access_token(self):
        """유효한 토큰이 있으면 재사용하여 403(EGW00133) 제한 에러를 방지합니다."""
        now = datetime.now()
        if self.access_token and self.token_expired_at and now < self.token_expired_at:
            return self.access_token

        url = f"{BASE_URL}/oauth2/tokenP"
        headers = {"content-type": "application/json"}
        body = {
            "grant_type": "client_credentials",
            "appkey": APP_KEY,
            "appsecret": APP_SECRET
        }

        try:
            res = requests.post(url, headers=headers, data=json.dumps(body))
            if res.status_code == 200:
                data = res.json()
                self.access_token = data.get("access_token")
                self.token_expired_at = now + timedelta(hours=23)
                logger.info("🔑 [토큰 발급 성공] 접근 토큰 캐싱 완료")
                return self.access_token
            else:
                logger.error(f"❌ [토큰 발급 실패] {res.text}")
                return None
        except Exception as e:
            logger.error(f"⚠️ [토큰 발급 예외] {e}")
            return None