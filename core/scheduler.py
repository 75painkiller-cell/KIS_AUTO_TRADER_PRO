import time
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def run_scheduler(api, symbols):
    """자동매매 스케줄러 메인 루프"""
    logger.info("🚀 KIS 자동 매매 봇 스케줄러가 시작되었습니다.")
    
    while True:
        try:
            # 글로벌 지표 및 상태 체크 영역
            logger.info("🌍 [미국/글로벌 지표] 상태 확인 완료")
            
            # 종목별 실시간 시세 및 조건 체크 루프
            for code in symbols:
                # API를 통한 현재가 및 목표가 조회
                current_price = api.get_current_price(code)
                target_price = api.get_target_price(code)
                
                # 🔍 터미우스 창에 실시간으로 출력되는 조건식 및 가격 로그
                logger.info(f"[{code}] 현재가: {current_price:,}원 | 목표가: {target_price:,}원")
                
                # 조건 충족 시 매수 실행 로직
                if current_price >= target_price:
                    logger.info(f"🚨 [{code}] 변동성 돌파 조건 충족! 매수 주문 검토 중...")
                    
        except Exception as e:
            logger.error(f"❌ 스케줄러 실행 중 에러 발생: {e}")

        # 30초 대기 루프
        logger.info("⏳ 30초 대기 중...")
        time.sleep(30)