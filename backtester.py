import pandas as pd
import FinanceDataReader as fdr

# config.py와 동일한 자금 관리 세팅
INITIAL_CAPITAL = 30000000  # 초기 자본금 3,000만 원
INVEST_RATIO = 0.5          # 현금 대비 투입 비율 50%
TAKE_PROFIT = 0.025         # 익절 기준 (+2.5%)
STOP_LOSS = -0.015          # 손절 기준 (-1.5%)

def run_backtest(target_code="069500", start_date="2023-01-01", end_date="2023-12-31"):
    print(f"📊 [{target_code}] 과거 데이터 불러오는 중... ({start_date} ~ {end_date})")
    
    # 1. KODEX 200 과거 일봉 데이터 불러오기
    df = fdr.DataReader(target_code, start_date, end_date)
    if df.empty:
        print("데이터를 불러오지 못했습니다. 종목 코드와 날짜를 확인하세요.")
        return

    # 가상의 매수 진입 시그널 (이동평균선 골든크로스 예시)
    df['MA_5'] = df['Close'].rolling(window=5).mean()
    df['MA_20'] = df['Close'].rolling(window=20).mean()

    cash = INITIAL_CAPITAL
    holdings = 0
    buy_price = 0
    
    # 통계용 변수
    trade_count = 0
    win_count = 0

    print("=== 🚀 백테스트 시뮬레이션 시작 ===")

    for i in range(20, len(df)):
        current_price = df['Close'].iloc[i]
        date = df.index[i].strftime('%Y-%m-%d')
        
        # [청산 로직] 보유 중일 때 익절/손절 체크 (risk.py 로직과 동일)
        if holdings > 0:
            profit_rate = (current_price - buy_price) / buy_price
            
            # 익절 조건 달성
            if profit_rate >= TAKE_PROFIT:
                cash += holdings * current_price
                holdings = 0
                trade_count += 1
                win_count += 1
                print(f"[{date}] 🟢 익절 완료! 수익률: +{profit_rate*100:.2f}% (매도가: {current_price:,.0f}원)")
            
            # 손절 조건 달성
            elif profit_rate <= STOP_LOSS:
                cash += holdings * current_price
                holdings = 0
                trade_count += 1
                print(f"[{date}] 🔴 손절 완료. 수익률: {profit_rate*100:.2f}% (매도가: {current_price:,.0f}원)")
                
        # [진입 로직] 보유 종목이 없고, 매수 시그널 발생 시 (5일선이 20일선 돌파)
        elif holdings == 0:
            prev_ma5 = df['MA_5'].iloc[i-1]
            prev_ma20 = df['MA_20'].iloc[i-1]
            curr_ma5 = df['MA_5'].iloc[i]
            curr_ma20 = df['MA_20'].iloc[i]
            
            if prev_ma5 < prev_ma20 and curr_ma5 > curr_ma20:
                # 50% 비율로 매수 수량 계산
                invest_amount = cash * INVEST_RATIO
                holdings = int(invest_amount / current_price)
                cash -= holdings * current_price
                buy_price = current_price
                print(f"[{date}] 🔵 매수 진입 (매수가: {buy_price:,.0f}원 / 수량: {holdings}주)")

    # 3. 최종 결과 결산
    final_price = df['Close'].iloc[-1]
    final_capital = cash + (holdings * final_price) # 보유 주식을 마지막 날 종가로 환산
    total_return = ((final_capital - INITIAL_CAPITAL) / INITIAL_CAPITAL) * 100
    win_rate = (win_count / trade_count * 100) if trade_count > 0 else 0

    print("\n==================================")
    print("      📊 백테스트 최종 결과      ")
    print("==================================")
    print(f"초기 자본금: {INITIAL_CAPITAL:,.0f} 원")
    print(f"최종 자산금: {final_capital:,.0f} 원")
    print(f"총 누적 수익률: {total_return:.2f} %")
    print(f"총 매매 횟수: {trade_count} 회")
    print(f"승률(익절 비율): {win_rate:.1f} %")
    print("==================================")

if __name__ == "__main__":
    # 2023년 1년 동안의 KODEX 200 데이터를 바탕으로 테스트 실행
    run_backtest(target_code="069500", start_date="2023-01-01", end_date="2023-12-31")