from datetime import datetime
from utils.config import STOP_LOSS, TAKE_PROFIT
import pytz


def check_exit(buy_price, current_price):
  """매수 단가와 현재가를 비교하여 익절/손절 신호를 반환합니다."""
  if buy_price <= 0:
    return None

  # 수익률 계산 (예: 0.025 = 2.5%)
  profit_rate = (current_price - buy_price) / buy_price

  if profit_rate >= TAKE_PROFIT:
    return 'SELL_PROFIT'
  elif profit_rate <= STOP_LOSS:
    return 'SELL_LOSS'

  return None


def check_blackout_time():
  """나스닥 선물 거래 시 위험한 변동성 구간이나 세션 마감 시간대를 체크하여

  매매 차단 여부(True/False)와 사유를 반환합니다.
  """
  et_zone = pytz.timezone('US/Eastern')
  now_et = datetime.now(et_zone)

  # 주말(토, 일)은 거래소 휴장
  if now_et.weekday() >= 5:
    return True, '주말 휴장일'

  # 1. 미국장 정규 개장 직후 10분간 (09:30 ~ 09:40 ET) - 슬리피지 극심 구간 회피
  if now_et.hour == 9 and 30 <= now_et.minute < 40:
    return True, '미국장 개장 직후 변동성 집중 구간'

  # 2. CME 일일 정산 및 세션 전환 시간대 (예: 17:00 ~ 18:00 ET)
  if now_et.hour == 17:
    return True, 'CME 세션 전환 및 정산 시간대'

  return False, '정상 거래 구간'