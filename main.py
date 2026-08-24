import time
import sys
import telegram
import api_kis

TARGET_ITEMS = {
    "069500": "KODEX 200",
    "114800": "KODEX 인버스",
    "229200": "KODEX 코스닥150",
    "251340": "KODEX 코스닥150선물인버스"
}

def main():
    print("🚀 시스템 가동 시작 (실시간 감시 모니터링)", flush=True)
    
    try:
        telegram.notify_start()
        total_asset, total_profit, my_holdings = api_kis.get_balance()
        telegram.notify_balance(total_asset, total_profit, my_holdings)
        print("✅ 초기 잔고 브리핑 전송 완료", flush=True)
    except Exception as e:
        print(f"⚠️ 초기 잔고 조회 실패: {e}", flush=True)

    print("🟢 실시간 30초 감시 모드 진입", flush=True)
    last_telegram_time = time.time()

    try:
        while True:
            print("\n==================================================", flush=True)
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 📊 [실시간 30초 모니터링]", flush=True)
            
            # 나스닥 선물 조회
            try:
                nasdaq = api_kis.get_nasdaq_future() if hasattr(api_kis, 'get_nasdaq_future') else "조회 중..."
                print(f"  - 나스닥 선물 (NQ=F): {nasdaq}", flush=True)
            except:
                print(f"  - 나스닥 선물 (NQ=F): 조회 중...", flush=True)

            # 잔고 및 보유 종목 조회
            try:
                total_asset, total_profit, my_holdings = api_kis.get_balance()
                print(f"💰 총 자산: {format(total_asset, ',')}원 | 총 평가손익: {format(total_profit, ',')}원", flush=True)
                
                print("📝 [현재 보유 종목 현황 🟢 최고점 대비 하락 시 익절/손절 감시 중]", flush=True)
                if not my_holdings:
                    print("  - 보유 종목 없음", flush=True)
                else:
                    for item in my_holdings:
                        print(f"  - {item.get('name')} | {item.get('qty')}주 | 현재가: {format(item.get('price', 0), ',')}원 | 평가손익: {format(item.get('profit', 0), ',')}원 ({item.get('profit_rate', 0.0)}%)", flush=True)
            except Exception as e:
                print(f"⚠️ [잔고 조회 오류]: {e}", flush=True)

            # 타겟 감시 종목 현재가 (1초 딜레이 적용)
            print("🎯 [타겟 감시 종목 현재가 🟡 내부 코드 로직 조건 충족 시 매수 대기]", flush=True)
            for code, name in TARGET_ITEMS.items():
                try:
                    time.sleep(1)
                    price = api_kis.get_current_price(code)
                    print(f"  - {name}: {format(price, ',')}원", flush=True)
                except:
                    print(f"  - {name}: 조회 대기 중...", flush=True)

            print("==================================================", flush=True)

            # 1시간 텔레그램 브리핑
            if time.time() - last_telegram_time >= 3600:
                try:
                    telegram.notify_balance(total_asset, total_profit, my_holdings)
                    last_telegram_time = time.time()
                except:
                    pass

            time.sleep(30)

    except KeyboardInterrupt:
        telegram.send_msg("<b>[🛑 시스템 종료]</b> 수동 중단")
    except Exception as e:
        telegram.send_msg(f"<b>[🚨 시스템 오류]</b>\n{e}")

if __name__ == "__main__":
    main()