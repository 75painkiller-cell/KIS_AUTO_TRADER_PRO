import pytz
from datetime import datetime

def check_blackout_time():
    """매매 차단 여부(True/False)와 사유를 반환합니다."""
    # 1. 한국 시간 기준 주말(토, 일) 체크
    kst_zone = pytz.timezone('Asia/Seoul')
    now_kst = datetime.now(kst_zone)
    if now_kst.weekday() >= 5:
        return True, '주말 휴장일'

    # 2. 미국장 관련 시간 체크
    et_zone = pytz.timezone('US/Eastern')
    now_et = datetime.now(et_zone)

    # 미국장 정규 개장 직후 10분간 (09:30 ~ 09:40 ET)
    if now_et.weekday() < 5 and now_et.hour == 9 and 30 <= now_et.minute < 40:
        return True, '미국장 개장 직후 변동성 집중 구간'

    # CME 일일 정산 및 세션 전환 시간대 (17:00 ~ 18:00 ET)
    if now_et.weekday() < 5 and now_et.hour == 17:
        return True, 'CME 세션 전환 및 정산 시간대'

    return False, '정상 거래 구간'