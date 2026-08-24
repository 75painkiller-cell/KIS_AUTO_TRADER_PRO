import time
import sys
import telegram
import api_kis

def main():
    print("🚀 시스템 가동 시작", flush=True)
    
    # 1. 시작 시 최초 알림 및 잔고 브리핑
    try:
        telegram.notify_start()
        total_asset, total_profit, my_holdings = api_kis.get_balance()
        telegram.notify_balance(total_asset, total_profit, my_holdings)
        print("✅ 초기 잔고 브리핑 전송 완료", flush=True)
    except Exception as e:
        print(f"⚠️ 초기 잔고 조회 실패: {e}", flush=True)

    print("🟢 실시간 감시 모드 진입 (터미널 10초 주기 / 텔레그램 1시간 주기)", flush=True)
    
    last_telegram_time = time.time()
    TELEGRAM_INTERVAL = 3600  # 1시간 (3600초)

    try:
        while True:
            # 🚀 터미널 감시: 10초마다 잔고를 조회해서 터미널 창에만 출력
            try:
                total_asset, total_profit, my_holdings = api_kis.get_balance()
                current_time = time.strftime('%Y-%m-%d %H:%M:%S')
                print(f"[{current_time}] 📊 [터미널 10초 체크] 총 자산: {format(total_asset, ',')}원 | 손익: {format(total_profit, ',')}원", flush=True)
            except Exception as e:
                print(f"⚠️ [터미널 체크 오류]: {e}", flush=True)

            # 📱 텔레그램 브리핑: 마지막 전송 시간부터 정확히 1시간이 지났을 때만 전송
            if time.time() - last_telegram_time >= TELEGRAM_INTERVAL:
                try:
                    telegram.notify_balance(total_asset, total_profit, my_holdings)
                    print(f"[{time.strftime('%H:%M:%S')}] ✅ [텔레그램] 정기 1시간 브리핑 전송 완료", flush=True)
                    last_telegram_time = time.time()  # 시간 리셋
                except Exception as e:
                    print(f"⚠️ [텔레그램 정기 브리핑 실패]: {e}", flush=True)

            # 10초 대기
            time.sleep(20)

    except KeyboardInterrupt:
        telegram.send_msg("<b>[🛑 시스템 종료]</b> 수동으로 중단되었습니다.")
    except Exception as e:
        telegram.send_msg(f"<b>[🚨 시스템 오류]</b>\n{e}")

if __name__ == "__main__":
    main()