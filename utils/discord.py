import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

def send_embed_message(title, description, color=3447003, fields=None):
    """
    디스코드로 알록달록한 임베드(카드형) 메시지를 전송합니다.
    - color: 좌측 컬러바 색상 코드 (기본 파란색, 빨간색=15158332, 초록색=3066993 등)
    - fields: [{"name": "항목", "value": "내용", "inline": True/False}, ...] 형태의 상세 정보 리스트
    """
    if not DISCORD_WEBHOOK_URL:
        return

    headers = {"Content-Type": "application/json"}
    
    embed = {
        "title": title,
        "description": description,
        "color": color,
        "footer": {"text": "KIS Auto Trader Pro • Two-Track System"}
    }

    if fields:
        embed["fields"] = fields

    payload = {
        "embeds": [embed]
    }

    try:
        response = requests.post(DISCORD_WEBHOOK_URL, data=json.dumps(payload), headers=headers)
        if response.status_code not in [200, 204]:
            print(f"디스코드 전송 실패: {response.text}")
    except Exception as e:
        print(f"디스코드 전송 에러: {e}")