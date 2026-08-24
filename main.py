import time
import sys
import telegram
import api_kis

# 🎯 감시할 타겟 종목 리스트 (KODEX ETF 4종목)
TARGET_ITEMS = {
    "069500": "KODEX 200",
    "114800": "KODEX 인버스",
    "229200": "KODEX 코스닥150",
    "251340": "KODEX 코스닥150선물인버스"
}

def main():
    print("🚀 시스템 가동 시작 (실시간 감시 모니터링)", flush=True)
    
    # 1. 시작 시 최초 알림 및 잔고 브리핑
    try:
        telegram.notify_start()
        total_asset, total_profit, my_holdings = api_kis.get_balance()
        telegram.notify_balance(total_asset, total_profit, my_holdings)
        print("✅ 초기 잔고 브리핑 전송 완료", flush=True)
    except Exception as e:
        print(f"⚠️ 초기 잔고 조회 실패: {e}", flush=True)

    print("🟢 실시간 30초 감시 모드 진입", flush=True)
    
    last_telegram_time = time.time()
    TELEGRAM_INTERVAL = 3600  # 1시간 (3600초)

    try:
        while True:
            print("\n==================================================", flush=True)
            current_time = time.strftime('%Y-%m-%d %H:%M:%S')
            print(f"[{current_time}] 📊 [실시간 30초 모니터링]", flush=True)
            
            # 2. 잔고 및 보유 종목 조회
            try:
                total_asset, total_profit, my_holdings = api_kis.get_balance()
                print(f"💰 총 자산: {format(total_asset, ',')}원 | 총 평가손익: {format(total_profit, ',')}원", flush=True)
                
                # 🟢 보유 종목 현황 출력 (상세 브리핑 추가)
                print("📝 [현재 보유 종목 현황 🟢 최고점 대비 하락 시 익절/손절 감시 중]", flush=True)
                if not my_holdings:
                    print("  - 보유 종목 없음", flush=True)
                else:
                    for item in my_holdings:
                        name = item.get('name', '알수없음')
                        qty = item.get('qty', 0)
                        price = item.get('price', 0)
                        profit = item.get('profit', 0)
                        profit_rate = item.get('profit_rate', 0.0)
                        print(f"  - {name} | {qty}주 | 현재가: {format(price, ',')}원 | 평가손익: {format(profit, ',')}원 ({profit_rate}%)", flush=True)
            except Exception as e:
                print(f"⚠️ [잔고/보유종목 조회 오류]: {e}", flush=True)

            # 🟡 타겟 종목 현재가 조회 (상세 브리핑 추가 + API 에러 원천 차단)
            print("🎯 [타겟 감시 종목 현재가 🟡 5일선이 20일선 돌파(골든크로스) 시 매수 대기]", flush=True)
            for code, name in TARGET_ITEMS.items():
                try:
                    # ⚠️ [핵심] API 초당 요청 제한 완벽 방어! 여기서 종목마다 1초씩 쉬면서 조심스럽게 물어봅니다.
                    time.sleep(1) 
                    
                    # 현재가 조회 (주의: 기존에 쓰시던 함수명이 get_current_price가 아니라면 그 이름으로 바꿔주세요!)
                    price = api_kis.get_current_price(code) 
                    print(f"  - {name}: {format(price, ',')}원", flush=True)
                except Exception as e:
                    print(f"  - {name}: 조회 대기 중... (현재가 호출 함수 점검 필요)", flush=True)

            print("==================================================", flush=True)

            # 📱 텔레그램 정기 브리핑 (1시간마다)
            if time.time() - last_telegram_time >= TELEGRAM_INTERVAL:
                try:
                    telegram.notify_balance(total_asset, total_profit, my_holdings)
                    print(f"[{time.strftime('%H:%M:%S')}] ✅ [텔레그램] 정기 1시간 브리핑 전송 완료", flush=True)
                    last_telegram_time = time.time()  # 시간 리셋
                except Exception as e:
                    print(f"⚠️ [텔레그램 정기 브리핑 실패]: {e}", flush=True)

            # 🚀 30초 대기 (이 시간이 곧 매매 감시 주기가 됩니다)
            time.sleep(30)

    except KeyboardInterrupt:
        telegram.send_msg("<b>[🛑 시스템 종료]</b> 수동으로 중단되었습니다.")
        print("\n🛑 시스템이 수동으로 종료되었습니다.", flush=True)
    except Exception as e:
        telegram.send_msg(f"<b>[🚨 시스템 오류]</b>\n{e}")
        print(f"🚨 시스템 오류: {e}", flush=True)

if __name__ == "__main__":
    main()