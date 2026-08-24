import datetime
import time
import api_kis
from risk import check_blackout_time
import telegram
import yfinance as yf

TARGET_SYMBOLS = {
    "069500": "KODEX 200             ",
    "114800": "KODEX 인버스         ",
    "229200": "KODEX 코스닥150      ",
    "251340": "KODEX 코스닥150선물인버스",
}
TARGET_BUY_AMOUNT = 1000000

# ==========================================
# 🧪 [마스터키] 테스트 모드 스위치
# - True  : 주말/야간 무시하고 강제 테스트 진행
# - False : 실전 모드 (시간 엄수 철통 방어)
IS_TEST_MODE = False  # 🚨 모의투자 테스트 구동 중
# ==========================================

# 중복 알림 방지용 변수
_last_nasdaq_notify_day = None
_last_hourly_briefing = None

# 📈 종목별 최고가를 기억하는 딕셔너리 (트레일링 스탑용)
_highest_prices = {}

# ⚙️ 트레일링 스탑 설정값
TRAIL_ACTIVATION_RATE = 3.0  # +3.0% 이상 수익부터 감시 시작
TRAIL_DROP_RATE = 1.5        # 최고점 대비 -1.5% 하락 시 익절
STOP_LOSS_RATE = -3.0        # 기본 손절 라인 (-3.0%)


def get_nasdaq_trend():
  try:
    nasdaq = yf.Ticker("NQ=F")
    hist = nasdaq.history(period="2d")
    if len(hist) >= 2:
      prev_close = hist["Close"].iloc[0]
      current_price = hist["Close"].iloc[1]
      return current_price > prev_close
  except Exception as e:
    api_kis.log(f"⚠️ 야후파이낸스 조회 오류: {e}")
  return False


def is_market_open():
  now = datetime.datetime.now()
  if now.weekday() >= 5:
    return False
  market_open = now.replace(hour=9, minute=0, second=0, microsecond=0)
  market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
  return market_open <= now <= market_close


def execute_trading_logic():
  global _last_nasdaq_notify_day
  global _last_hourly_briefing
  global _highest_prices
  
  global _last_ready_day
  global _last_open_day
  global _last_close_day

  now = datetime.datetime.now()
  today_str = now.strftime("%Y-%m-%d")

  if '_last_ready_day' not in globals(): _last_ready_day = None
  if '_last_open_day' not in globals(): _last_open_day = None
  if '_last_close_day' not in globals(): _last_close_day = None

  # 🔔 [이벤트 1] 평일 장 시작 30분 전 준비 보고 (08:30)
  if now.weekday() < 5 and now.hour == 8 and now.minute >= 30 and now.minute < 50 and _last_ready_day != today_str:
    cash, holdings = api_kis.get_account_status()
    msg = f"🌅 <b>[장 시작 30분 전 준비 보고]</b>\n"
    msg += f"• 예수금: {cash:,}원\n"
    msg += f"• 상태: 09:00 정규장 개장 준비 중 (봇 정상 가동 🟢)"
    telegram.send_message(msg)
    _last_ready_day = today_str

  # 🔔 [이벤트 2] 평일 장 시작 10분 전 / 동시호가 진입 알림 (08:50)
  if now.weekday() < 5 and now.hour == 8 and now.minute >= 50 and _last_open_day != today_str:
    cash, holdings = api_kis.get_account_status()
    msg = f"🔔 <b>[08:50 동시호가 시작 / 장 개장 10분 전]</b>\n"
    msg += f"• 예수금: {cash:,}원\n"
    msg += f"• 상태: 09:00 정규장 오픈 대기 중 (09:15까지 변동성 관망)"
    telegram.send_message(msg)
    _last_open_day = today_str

  # 🔔 [이벤트 3] 평일 장 마감 및 종료 보고 (15:30)
  if now.weekday() < 5 and now.hour == 15 and now.minute >= 30 and _last_close_day != today_str:
    cash, holdings = api_kis.get_account_status()
    msg = f"🏁 <b>[15:30 정규장 마감 종료 보고]</b>\n"
    msg += f"• 예수금: {cash:,}원\n"
    if holdings:
      msg += "• 최종 보유 종목:\n"
      for code, info in holdings.items():
        msg += f"  - {info['name'].strip()}: {info['net_pl']:+.2f}%\n"
    else:
      msg += "• 보유 종목 없음 (현금 보유 중)\n"
    msg += f"• 상태: 오늘 매매 일정을 모두 마쳤습니다. 수고하셨습니다! ☕"
    telegram.send_message(msg)
    _last_close_day = today_str

  # ⏱️ [이벤트 4] 장중 1시간 간격 정기 브리핑
  current_hour_str = now.strftime("%Y-%m-%d %H")
  if is_market_open() and _last_hourly_briefing != current_hour_str:
    cash, holdings = api_kis.get_account_status()
    msg = f"⏱️ <b>[장중 {now.hour}시 정기 브리핑]</b>\n"
    msg += f"• 예수금: {cash:,}원\n"

    if holdings:
      msg += "• 보유 종목 (세후 수익률):\n"
      for code, info in holdings.items():
        msg += f"  - {info['name'].strip()}: {info['net_pl']:+.2f}%\n"
      msg += "\n💡 상태: 조건 도달 시 익절/손절 대기 중"
    else:
      msg += "• 보유 종목 없음\n"
      msg += "\n🧐 상태: 골든크로스 매수 기회 탐색 중"

    telegram.send_message(msg)
    _last_hourly_briefing = current_hour_str

  # ==============================================================

  # 🛡️ 1. 방어막 체크
  if not IS_TEST_MODE:
    is_blocked, reason = check_blackout_time()
    if is_blocked:
      return

    if not is_market_open():
      return
  else:
    api_kis.log("🧪 [테스트 모드 가동 중] 주말/야간 방어막을 강제로 무시하고 진행합니다.")

  # 🕒 2. 장 초반 관망 (09:15 이전)
  if now.hour == 9 and now.minute < 15 and not IS_TEST_MODE:
    api_kis.log("🕒 [장 초반 관망] 변동성 회피를 위해 09:15까지 매매를 보류합니다.")
    return

  print("\n" + "=" * 65)
  cash, holdings = api_kis.get_account_status()

  if cash == 0 and not holdings:
    api_kis.log("⚠️ [안전 모드] 잔고 데이터 수신 대기 중...")
    return

  api_kis.log(f"📊 [계좌 잔고 확인] 예수금: {cash:,}원")
  print("-" * 65)

  # ⏰ 5. 오후 3시 오버나이트 리스크 관리
  if now.hour == 15 and now.minute >= 0 and not IS_TEST_MODE:
    api_kis.log("⏰ [오버나이트 관리] 장 마감 임박. 나스닥 선물 추세 기반 포지션 조절 시작.")
    nasdaq_is_good = get_nasdaq_trend()
    trend_status = "상승(유지)" if nasdaq_is_good else "하락(회피)"
    api_kis.log(f"🔍 [나스닥 추세 확인] 현재 나스닥 선물 추세: {trend_status}")

    today_str = now.strftime("%Y-%m-%d")
    if _last_nasdaq_notify_day != today_str:
      trend_text = "상승 🟢 (오버나이트 유지)" if nasdaq_is_good else "하락 🔴 (리스크 회피 모드)"
      telegram.send_message(f"🔍 <b>[나스닥 선물 추세 브리핑]</b>\n• 현재 방향성: {trend_text}")
      _last_nasdaq_notify_day = today_str

    for symbol, my in list(holdings.items()):
      if not nasdaq_is_good and my["net_pl"] > 0:
        api_kis.log(f"  🚨 [{my['name'].strip()}] 나스닥 하락 우려, 오버나이트 회피 매도")
        is_success = api_kis.send_order(symbol, False, my["qty"], price=0, name=my["name"].strip())

        if is_success:
          if symbol in _highest_prices:
            del _highest_prices[symbol]
          cur_p = api_kis.get_current_price(symbol)
          if cur_p == 0: cur_p = my["avg"]
          inv_amt, ev_amt = my["qty"] * my["avg"], my["qty"] * cur_p
          raw_won, fee_won = ev_amt - inv_amt, ev_amt * (api_kis.ETF_FEE_RATE / 100)
          net_won = raw_won - fee_won
          telegram.send_sell_alert(my["name"].strip(), my["qty"], cur_p, my["net_pl"], raw_won, fee_won, net_won, "오버나이트 회피 익절")
        time.sleep(1.0)

  # 🎯 6. 종목 모니터링 (트레일링 스탑 및 매수 로직)
  for symbol, name in TARGET_SYMBOLS.items():
    price = api_kis.get_current_price(symbol)
    time.sleep(1.0)  # 👈 현재가 조회 후 휴식
    
    ma5, ma20, rsi, vol, prev_close, bb_upper, bb_lower, macd = api_kis.calculate_indicators(symbol)
    time.sleep(1.5)  # 👈 지표 계산 후 서버 부하 방지용 추가 휴식

    if price == 0 or ma5 == 0:
      api_kis.log(f"⚠️ [{name.strip()}] 데이터 조회 대기 중...")
      time.sleep(0.5)
      continue

    my = holdings.get(symbol)

    if my:
      raw_rate = ((price - my["avg"]) / my["avg"]) * 100
      net_rate = raw_rate - api_kis.ETF_FEE_RATE
      investment_amount = my["qty"] * my["avg"]
      current_eval_amount = my["qty"] * price
      raw_profit_won = current_eval_amount - investment_amount
      estimated_fee = current_eval_amount * (api_kis.ETF_FEE_RATE / 100)
      net_profit_won = raw_profit_won - estimated_fee

      if symbol not in _highest_prices:
        _highest_prices[symbol] = price
      elif price > _highest_prices[symbol]:
        _highest_prices[symbol] = price
        if net_rate >= TRAIL_ACTIVATION_RATE:
            api_kis.log(f"  📈 [{name.strip()}] 트레일링 스탑 가동 중! 최고가 갱신: {price:,}원 (현재 수익 {net_rate:+.2f}%)")

      highest_price = _highest_prices[symbol]
      drop_rate_from_high = ((highest_price - price) / highest_price) * 100

      print(f"  🔹 {name.strip()} | 현재가: {price:,}원 (고점대비: -{drop_rate_from_high:.2f}%) | 보유: {my['qty']}주")
      print(f"    👉 단순: {raw_rate:+.2f}% | 세후: {net_rate:+.2f}% | 💰 순수익: {net_profit_won:+,.0f}원")

      sell_reason = ""
      if net_rate <= STOP_LOSS_RATE:
        sell_reason = "기본 손절 라인 도달"
      elif net_rate >= TRAIL_ACTIVATION_RATE and drop_rate_from_high >= TRAIL_DROP_RATE:
        sell_reason = f"트레일링 스탑 발동 (최고점 대비 -{drop_rate_from_high:.2f}% 하락)"

      if sell_reason:
        api_kis.log(f"  🚨 [{name.strip()}] {sell_reason}! 시장가 청산 실행")
        is_success = api_kis.send_order(symbol, False, my["qty"], price=0, name=name.strip())
        if is_success:
          if symbol in _highest_prices: del _highest_prices[symbol]
          telegram.send_sell_alert(name.strip(), my["qty"], price, net_rate, raw_profit_won, estimated_fee, net_profit_won, sell_reason)
    else:
      if symbol in _highest_prices: del _highest_prices[symbol]
      
      trend = "🟢 상승" if ma5 > ma20 else "🔴 하락"
      chg_rate = ((price - prev_close) / prev_close) * 100 if prev_close else 0.0
      
      # 💡 [추가] 매수 조건 충족 여부 및 미달 사유 실시간 판단
      is_ma_ok = ma5 > ma20
      is_rsi_ok = rsi < 70
      if is_ma_ok and is_rsi_ok:
          buy_status = f"🟢 [매수 조건 충족! 현재가 {price:,}원 즉시 진입 대기]"
      else:
          reasons = []
          if not is_ma_ok: reasons.append("5일<20일선")
          if not is_rsi_ok: reasons.append("RSI 70이상")
          buy_status = f"⏳ [매수 대기 중 (미달 사유: {', '.join(reasons)})]"

      print(f"  🔸 {name.strip()} | 현재가: {price:,}원 ({chg_rate:+.2f}%) | 당일 거래량: {vol:,}주")
      print(f"    📈 추세: {trend} (5일: {ma5:,.0f}원 / 20일: {ma20:,.0f}원)")
      print(f"    📊 지표: RSI: {rsi} | MACD: {macd} | BB상단: {bb_upper:,.0f}원 | BB하단: {bb_lower:,.0f}원")
      print(f"    🎯 매수 상태: {buy_status}")

      if now.hour == 15 and now.minute >= 10 and not IS_TEST_MODE: continue

      if is_ma_ok and is_rsi_ok and cash >= TARGET_BUY_AMOUNT:
        calc_qty = max(1, int(TARGET_BUY_AMOUNT / price))
        api_kis.log(f"  🚀 [{name.strip()}] 골든크로스 매수 포착! {calc_qty}주 매수 실행")
        is_success = api_kis.send_order(symbol, True, calc_qty, price=price, name=name.strip())
        
        if is_success: 
          telegram.send_buy_alert(name.strip(), calc_qty, price, f"골든크로스 진입 (RSI: {rsi}, MACD: {macd})")
          
        cash -= calc_qty * price

    time.sleep(1.0)