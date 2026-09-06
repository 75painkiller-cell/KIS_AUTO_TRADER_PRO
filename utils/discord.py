import requests
from core.config import DISCORD_WEBHOOK_URL
from utils.my_logger import logger

def send_discord_message(msg: str):
    """디스코드 웹훅 알림 안전 전송"""
    if not DISCORD_WEBHOOK_URL or not DISCORD_WEBHOOK_URL.startswith("http"):
        return
    
    try:
        payload = {"content": str(msg)}
        resp = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=3)
        if resp.status_code not in (200, 204):
            logger.warning(f"디스코드 전송 실패 ({resp.status_code}): {resp.text}")
    except Exception as e:
        logger.warning(f"디스코드 전송 예외 발생: {e}")