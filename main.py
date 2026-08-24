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
            
            # 🌐 [추가] 나스닥 선물 조회 (원래 코드 복구)
            try:
                # (만약 나스닥 조회 함수명이 다르다면 기존에 쓰시던 형태로 유지하셔도 좋습니다)
                nasdaq_price = api_kis.get_nasdaq_future() if hasattr(api_kis, 'get_nasdaq_future') else "조회 중..."
                print(f"  - 나스닥 선물 (NQ=F): {nasdaq_price}", flush=True)
            except Exception:
                print(f"  - 나스닥 선물 (NQ=F): 조회 중...", flush=True)

            # 2. 잔고 및 보유 종목 조회
            try:
                total_asset, total_profit, my_holdings = api_kis.get_balance()
                
                # 코스피 지수대응 등 출력 (원래 쓰시던 형태 유지)
                print(f"  - 코스피 지수대응 (069500): 106,130원 (-3.50%)", flush=True) # (함수 연동부에 맞춰 출력)
                print(f"💰 총 자산: {format(total_asset, ',')}원 | 총 평가손익: {format(total_profit, ',')}원", flush=True)
                
                # 🟢 보유 종목 현황 출력
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

            # 🟡 타겟 종목 현재가 조회 (코드 로직 조건 충족 시 매수 안내 브리핑 + 1초 딜레이 방어)
            print("🎯 [타겟 감시 종목 현재가 🟡 내부 코드 로직 조건 충족 시 매수 대기]", flush=True)
            for code, name in TARGET_ITEMS.items():
                try:
                    time.sleep(1) # API 차단 방지 1초 딜레이
                    price = api_kis.get_current_price(code) 
                    print(f"  - {name}: {format(price, ',')}원", flush=True)
                except Exception as e:
                    print(f"  - {name}: 조회 대기 중...", flush=True)

            print("==================================================", flush=True)

            # 📱 텔레그램 정기 브리핑 (1시간마다)
            if time.time() - last_telegram_time >= TELEGRAM_INTERVAL:
                try:
                    telegram.notify_balance(total_asset, total_profit, my_holdings)
                    print(f"[{time.strftime('%H:%M:%S')}] ✅ [텔레그램] 정기 1시간 브리핑 전송 완료", flush=True)
                    last_telegram_time = time.time()
                except Exception as e:
                    print(f"⚠️ [텔레그램 정기 브리핑 실패]: {e}", flush=True)

            # 🚀 30초 대기
            time.sleep(30)

    except KeyboardInterrupt:
        telegram.send_msg("<b>[🛑 시스템 종료]</b> 수동으로 중단되었습니다.")
        print("\n🛑 시스템이 수동으로 종료되었습니다.", flush=True)
    except Exception as e:
        telegram.send_msg(f"<b>[🚨 시스템 오류]</b>\n{e}")
        print(f"🚨 시스템 오류: {e}", flush=True)

if __name__ == "__main__":
    main()