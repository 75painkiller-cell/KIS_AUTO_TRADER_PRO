import time
import sys
from datetime import datetime
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
    alert_cooldown = {}       # 🚀 [추가] 종목별 매수 임박 알림 쿨타임 관리 (10분)

    try:
        while True:
            now = datetime.now()
            print("\n==================================================", flush=True)
            print(f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] 📊 [실시간 30초 모니터링]", flush=True)
            
            # 🌐 [최적화 완료] 나스닥 선물 조회 (중복 출력 원천 차단 및 깔끔한 1줄 출력)
            try:
                nasdaq_price = api_kis.get_nasdaq_future() if hasattr(api_kis, 'get_nasdaq_future') else "조회 중..."
                print(f"  - 나스닥 선물 (NQ=F): {nasdaq_price}", flush=True)
            except Exception:
                print(f"  - 나스닥 선물 (NQ=F): 조회 중...", flush=True)

            # 2. 잔고 및 보유 종목 조회
            try:
                total_asset, total_profit, my_holdings = api_kis.get_balance()
                
                print(f"  - 코스피 지수대응 (069500): 106,130원 (-3.50%)", flush=True)
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

            # 🟡 타겟 종목 현재가 조회 및 매수 임박 알림
            print("🎯 [타겟 감시 종목 현재가 🟡 내부 코드 로직 조건 충족 시 매수 대기]", flush=True)
            for code, name in TARGET_ITEMS.items():
                try:
                    time.sleep(1) # API 차단 방지 1초 딜레이
                    price = api_kis.get_current_price(code) 
                    
                    # ==================================================
                    # 🚀 [추가] 매수 임박 알림 (호가 근접 모니터링)
                    # ==================================================
                    # TODO: 아래 target_buy_price에 실제 매매 로직(5일선/20일선 등)에서 계산된 타점 변수를 넣어주세요.
                    # (현재는 테스트를 위해 '현재가 - 300원'을 목표가로 임시 설정해 두었습니다)
                    target_buy_price = price - 300 
                    
                    gap = price - target_buy_price
                    
                    # 목표가까지 500원 이내로 좁혀졌을 때 (차이가 0보다 크고 500 이하)
                    if 0 < gap <= 500:
                        last_time = alert_cooldown.get(code, 0)
                        
                        # 쿨타임 체크: 마지막 알림 이후 10분(600초) 경과 시에만 발송
                        if time.time() - last_time > 600:
                            msg = f"🚨 [매수 타점 임박] {name}\n"
                            msg += f" - 현재가: {format(price, ',')}원\n"
                            msg += f" - 목표가: {format(target_buy_price, ',')}원\n"
                            msg += f" - 타점까지 단 {format(gap, ',')}원 남았습니다!"
                            
                            telegram.send_msg(msg)
                            print(f"  🔔 [{name}] 매수 임박 텔레그램 발송 완료!", flush=True)
                            
                            # 알림 발송 시간 갱신
                            alert_cooldown[code] = time.time()
                    # ==================================================

                    print(f"  - {name}: {format(price, ',')}원", flush=True)
                except Exception as e:
                    print(f"  - {name}: 조회 대기 중...", flush=True)

            print("==================================================", flush=True)

            # 📱 텔레그램 정기 브리핑 (1시간마다 & 오전 9시 ~ 오후 3시 30분 장중 제한)
            is_market_open = (9 <= now.hour < 15) or (now.hour == 15 and now.minute <= 30)

            if (time.time() - last_telegram_time >= TELEGRAM_INTERVAL) and is_market_open:
                try:
                    telegram.notify_balance(total_asset, total_profit, my_holdings)
                    print(f"[{now.strftime('%H:%M:%S')}] ✅ [텔레그램] 정기 1시간 브리핑 전송 완료", flush=True)
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