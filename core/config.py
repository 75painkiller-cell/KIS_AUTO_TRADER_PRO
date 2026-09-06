import os
import yaml
from dotenv import load_dotenv
from utils.my_logger import logger

# .env 파일 강제 리로드
load_dotenv(override=True)

def _clean_env(key: str, default: str = "") -> str:
    """환경변수 앞뒤 공백 및 따옴표 제거"""
    val = os.getenv(key, default)
    if val is None:
        return default
    return str(val).strip().strip("'\"")

APP_KEY = _clean_env("KIS_APP_KEY")
APP_SECRET = _clean_env("KIS_APP_SECRET")
DISCORD_WEBHOOK_URL = _clean_env("DISCORD_WEBHOOK_URL")
BASE_URL = _clean_env("KIS_BASE_URL", "https://openapivts.koreainvestment.com:29443")
HTS_USER_ID = _clean_env("HTS_USER_ID").lstrip("@")

def load_config(filepath="config.yaml"):
    """YAML 전략 설정 파일 로드"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logger.error(f"오류: {filepath} 파일을 찾을 수 없습니다.")
        return None
    except Exception as e:
        logger.error(f"YAML 설정 파일 읽기 오류: {e}")
        return None