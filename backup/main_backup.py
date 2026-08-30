import time
from datetime import datetime
import api_kis
import global_data  
from my_logger import logger  # 👈 로거 임포트

TARGETS = {
    "069500": "KODEX 200",
    "114800": "KODEX 인버스",
    "229200": "KODEX 코스닥150",
    "251340": "KODEX 코스닥150선물인버스"
}

def main():
    logger.info("🚀 메인 모니터링 시작 (국내/해외 모듈 분리형)")

    while True:
        try:
            logger.info("=" * 50)
            logger.info("📊 시스템 상태 점검")
            
            # 🌍 1. 글로벌 오버나이트 지표 (외국)
            logger.info("🌍 [글로벌 오버나이트 지표]")
            
            nq_price = global_data.get_nasdaq_futures()
            if nq_price is not None:
                logger.info(f"  ▶ 나스닥 선물 (NQ=F): {nq_price:,.2f}pt")
            else:
                logger.warning("  ⚠️ 나스닥 선물: 조회 실패")

            vix_price = global_data.get_vix()
            if vix_price is not None:
                logger.info(f"  ▶ VIX 공포지수 (^VIX): {vix_price:,.2f}")
            else:
                logger.warning("  ⚠️ VIX 지수: 조회 실패")
                
            usdkrw = global_data.get_usdkrw()
            if usdkrw is not None:
                logger.info(f"  ▶ 원/달러 환율 (KRW=X): {usdkrw:,.2f}원")
            else:
                logger.warning("  ⚠️ 환율: 조회 실패")

            logger.info("-" * 50)

            # 🇰🇷 2. 국내 타겟 종목 및 계좌 (국내)
            logger.info("🇰🇷 [국내 타겟 종목 및 계좌]")
            asset, profit, holdings = api_kis.get_balance()
            logger.info(f"  💰 총 자산: {asset:,}원 | 손익: {profit:,}원")

            for code, name in TARGETS.items():
                price = api_kis.get_current_price(code)
                if price is not None:
                    logger.info(f"  🎯 {name}: {price:,}원")
                else:
                    logger.warning(f"  ⚠️ {name}: 현재가 조회 실패")
                time.sleep(0.2) # API 과부하 방지
            
            logger.info("=" * 50)

        except Exception as e:
            # 에러가 나면 error()로 빨갛게 남김
            logger.error(f"⚠️ 메인 루프 에러 발생: {e}")

        # 3. 30초 대기
        logger.info("⏳ 30초 대기 중...\n")
        time.sleep(30)

if __name__ == "__main__":
    main()