import yfinance as yf
import pandas as pd
import numpy as np
from .api_kis import ETF_FEE_RATE

def run_backtest(ticker="069500.KS", period="1y", k_ratio=0.5):
    """
    변동성 돌파 및 복합 필터 백테스팅 시뮬레이터
    """
    # 1. 야후 파이낸스 데이터 로드 (한국 종목은 .KS 부착)
    df = yf.download(ticker, period=period, progress=False)
    if df.empty:
        print(f"⚠️ [{ticker}] 백테스트용 데이터가 없습니다.")
        return

    # 다중 인덱스 컬럼 대응
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # 2. 기술적 지표 계산
    df['MA5'] = df['Close'].rolling(window=5).mean()
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['Disparity'] = (df['Close'] / df['MA20']) * 100
    
    # 변동성 돌파 타겟가 (전일 기준)
    df['Range'] = df['High'].shift(1) - df['Low'].shift(1)
    df['Target'] = df['Open'] + df['Range'] * k_ratio

    # 3. 매매 시그널 및 수익률 계산
    df['Signal'] = np.where(
        (df['Close'] > df['Target']) & 
        (df['MA5'] > df['MA20']) & 
        (df['Disparity'] >= 100) & 
        (df['Disparity'] <= 105), 
        1, 0
    )

    # 당일 시가 매수 -> 종가 매도 혹은 익일 청산 시뮬레이션
    df['Market_Ret'] = df['Close'].pct_change()
    df['Strategy_Ret'] = df['Signal'].shift(1) * df['Market_Ret'] - (ETF_FEE_RATE / 100)

    # 4. 성과 지표 산출
    cum_ret = (1 + df['Strategy_Ret'].fillna(0)).cumprod() - 1
    total_return = cum_ret.iloc[-1] * 100
    win_trades = df[df['Strategy_Ret'] > 0]
    total_trades = df[df['Signal'] == 1]
    win_rate = (len(win_trades) / len(total_trades) * 100) if len(total_trades) > 0 else 0

    # MDD 계산
    peak = cum_ret.cummax()
    mdd = ((cum_ret - peak) / (1 + peak)).min() * 100

    print(f"==================================================")
    print(f"📊 [{ticker}] 백테스트 결과 (기간: {period}, K: {k_ratio})")
    print(f"• 누적 수익률 : {total_return:+.2f}%")
    print(f"• 승       률 : {win_rate:.1f}% (총 진입 횟수: {len(total_trades)}회)")
    print(f"• 최대 낙폭(MDD): {mdd:.2f}%")
    print(f"==================================================")
    
    return total_return, win_rate, mdd

if __name__ == "__main__":
    run_backtest("069500.KS", "1y", 0.5)