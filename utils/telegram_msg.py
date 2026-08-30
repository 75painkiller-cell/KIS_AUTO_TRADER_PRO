import requests
from utils.my_logger import logger

# 발급받은 봇 토큰과 본인의 챗 아이디를 넣어주세요.
TOKEN = "8847215327:AAGgWXRq4E--zwJBkvuh5fUSKbuRsh_dir0"
CHAT_ID = "8772867010"

def send_message(msg):
    """텔레그램으로 메시지를 전송하는 함수"""
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        # 🔥 timeout=5 : 텔레그램 서버가 아파도 5초 뒤엔 봇이 제 갈 길을 가게 만듭니다. (프리징 방지)
        response = requests.get(url, params={"chat_id": CHAT_ID, "text": msg}, timeout=5)
        
        if response.status_code == 200:
            logger.info("📩 텔레그램 알림 전송 완료")
        else:
            logger.error(f"⚠️ 텔레그램 전송 실패: {response.text}")
    except Exception as e:
        logger.error(f"⚠️ 텔레그램 통신 에러(타임아웃 등): {e}")