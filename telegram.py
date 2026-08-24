import os
import requests
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_msg(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    try:
        # 타임아웃 5초 설정으로 무한 멈춤 방지
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"⚠️ 텔레그램 전송 실패: {e}", flush=True)

def notify_start():
    send_msg("<b>[🟢 KIS_AUTO_TRADER_PRO 가동 시작]</b>\n시스템 모니터링을 시작합니다.")

def notify_balance(total_asset, total_profit, holdings):
    msg = f"<b>[📊 계좌 잔고 현황]</b>\n"
    msg += f"■ 총 자산: {format(total_asset, ',')}원\n"
    msg += f"■ 세후 총 손익: {'🔴' if total_profit >= 0 else '🔵'} {format(total_profit, ',')}원\n\n"
    msg += f"<b>[📦 보유 종목 현황] (세후 기준)</b>\n"
    for h in holdings:
        sign = '+' if h['profit_amt'] >= 0 else ''
        emoji = '🔴' if h['profit_amt'] >= 0 else '🔵'
        msg += f"{emoji} <b>{h['name']} ({h['qty']}주)</b>\n"
        msg += f"  └ 매입 {format(int(h['buy_price']), ',')}원 ➡️ 현재 {format(int(h['price']), ',')}원\n"
        msg += f"  └ 세후 손익 {sign}{format(h['profit_amt'], ',')}원 ({sign}{h['rt']}%)\n\n"
    send_msg(msg)