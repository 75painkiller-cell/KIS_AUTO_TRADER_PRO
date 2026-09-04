import os
import json
import asyncio
import websockets
from dotenv import load_dotenv
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from auth import KISTokenManager
from utils.my_logger import logger
from utils import telegram_msg
from utils import discord
from utils.database import log_whale

load_dotenv()
APP_KEY = os.getenv("KIS_APP_KEY")
APP_SECRET = os.getenv("KIS_APP_SECRET")
WS_URL = "ops.koreainvestment.com:21000"

class KISWebsocketEngine:
    def __init__(self):
        self.token_manager = KISTokenManager()
        self.approval_key = None

    def get_approval_key(self):
        url = "https://openapi.koreainvestment.com:9443/oauth2/Approval"
        headers = {"content-type": "application/json; charset=utf-8"}
        body = {
            "grant_type": "client_credentials",
            "appkey": APP_KEY,
            "secretkey": APP_SECRET
        }
        try:
            import requests
            res = requests.post(url, headers=headers, data=json.dumps(body))
            if res.status_code == 200:
                data = res.json()
                self.approval_key = data.get("approval_key")
                logger.info("🔑 [웹소켓] 승인키 발급 성공")
                return self.approval_key
            else:
                logger.error(f"❌ [웹소켓] 승인키 발급 실패: {res.text}")
                return None
        except Exception as e:
            logger.error(f"⚠️ [웹소켓] 승인키 발급 중 예외 발생: {e}")
            return None

    # [수정 1] 동기화(Sync)로 인한 블로킹 방지를 위해 알림/DB 처리를 별도 비동기 함수로 분리
    async def process_whale_alert(self, symbol, price, volume):
        alert_msg = f"🚨 [고래 체결 포착!] 종목: {symbol} | 수량: {volume:,}주 | 가격: {price:,}원"
        logger.info(alert_msg)
        
        # asyncio.to_thread를 사용하여 I/O 병목을 유발하는 동기 함수들을 백그라운드 스레드로 넘김
        await asyncio.gather(
            asyncio.to_thread(log_whale, symbol, price, volume),
            asyncio.to_thread(telegram_msg.send_message, alert_msg),
            asyncio.to_thread(
                discord.send_embed_message,
                title="🚨 [고래 체결 포착!]",
                description="실시간 웹소켓 감시망에서 대량 거래량이 유입되었습니다.",
                color=15158332,
                fields=[
                    {"name": "종목 코드", "value": str(symbol), "inline": True},
                    {"name": "체결 수량", "value": f"{volume:,}주", "inline": True},
                    {"name": "체결 가격", "value": f"{price:,}원", "inline": True},
                    {"name": "대응 가이드", "value": "돌파 매수세 집중 모니터링", "inline": False}
                ]
            )
        )

    async def connect_and_listen(self, symbols):
        if not self.approval_key:
            self.get_approval_key()
            if not self.approval_key:
                return

        uri = f"ws://{WS_URL}/tryitout/H0STCNT0"
        
        async with websockets.connect(uri) as websocket:
            logger.info("🕸️ [웹소켓 서버 연결 완료] 실시간 고래 감시 모드 가동!")

            for symbol in symbols:
                request_data = {
                    "header": {
                        "approval_key": self.approval_key,
                        "custtype": "P",
                        "tr_type": "1",
                        "content-type": "utf-8"
                    },
                    "body": {
                        "input": {
                            "tr_id": "H0STCNT0",
                            "tr_key": symbol
                        }
                    }
                }
                await websocket.send(json.dumps(request_data))
                await asyncio.sleep(0.1) # 한국투자증권 구독 초당 요청 제한 방어용 유지

            while True:
                try:
                    data = await websocket.recv()
                    if data[0] in ['0', '1']: 
                        parsed_data = self.parse_packet(data)
                        if parsed_data:
                            symbol = parsed_data['symbol']
                            price = parsed_data['price']
                            volume = parsed_data['volume']
                            
                            if volume >= 2000:
                                # [수정 2] 웹소켓 수신 루프가 멈추지 않도록 백그라운드 Task로 분리 실행 (Fire and Forget)
                                asyncio.create_task(self.process_whale_alert(symbol, price, volume))

                except websockets.exceptions.ConnectionClosed:
                    logger.warning("⚠️ [웹소켓] 연결이 끊겼습니다. 재연결을 시도합니다...")
                    await asyncio.sleep(5)
                    break
                except Exception as e:
                    logger.error(f"⚠️ [웹소켓 수신 에러] {e}")
                    await asyncio.sleep(1)

    def parse_packet(self, data):
        try:
            if data.startswith("0") or data.startswith("1"):
                splits = data.split('|')
                if len(splits) >= 4:
                    body = splits[3]
                    values = body.split('^')
                    if len(values) >= 13:
                        symbol = values[0]
                        price = int(values[2])
                        volume = int(values[12])
                        return {"symbol": symbol, "price": price, "volume": volume}
        except Exception:
            pass
        return None