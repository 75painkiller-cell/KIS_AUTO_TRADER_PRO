import os
import requests
from dotenv import load_dotenv

load_dotenv() # .env 파일 로드
TOKEN = os.getenv("TELEGRAM_TOKEN") # 이 부분이 누락되었을 확률이 높습니다!
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# 함수 이름을 send_message로 통일
def send_message(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"⚠️ 텔레그램 전송 실패: {e}", flush=True)
def send_buy_alert(name, qty, price, reason):
    msg = f"🟢 <b>[매수 체결]</b>\n• 종목: {name}\n• 수량: {qty}주\n• 단가: {price:,}원\n• 사유: {reason}"
    send_message(msg)

def send_sell_alert(name, qty, price, net_rate, raw_profit, fee, net_profit, reason):
    emoji = "🔴" if net_profit >= 0 else "🔵"
    msg = f"{emoji} <b>[매도 체결]</b>\n• 종목: {name}\n• 수량: {qty}주\n• 체결가: {price:,}원\n• 수익률: {net_rate:+.2f}%\n• 순수익: {net_profit:+,.0f}원\n• 사유: {reason}"
    send_message(msg)        