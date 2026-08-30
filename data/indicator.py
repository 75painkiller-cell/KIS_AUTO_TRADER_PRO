import yfinance as yf
import pandas as pd
from my_logger import logger

def calculate_indicators(code):
    try:
        ticker = f"{code}.KS"
        df = yf.download(ticker, period="3mo", interval="1d", progress=False)
        
        if df.empty or len(df) < 26:
            return 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
            
        close = df['Close'].squeeze()
        open_price = float(df['Open'].squeeze().iloc[-1])   # 당일 시가
        high_p = float(df['High'].squeeze().iloc[-2])       # 전일 고가
        low_p = float(df['Low'].squeeze().iloc[-2])         # 전일 저가
        
        vol = int(df['Volume'].squeeze().iloc[-1])
        prev_close = float(close.iloc[-2])
        
        ma5 = float(close.rolling(window=5).mean().iloc[-1])
        ma20 = float(close.rolling(window=20).mean().iloc[-1])
        
        delta = close.diff()
        gain = delta.where(delta > 0, 0).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = float(100 - (100 / (1 + rs)).iloc[-1])
        
        std = close.rolling(window=20).std()
        bb_upper = float((ma20 + (std * 2)).iloc[-1])
        bb_lower = float((ma20 - (std * 2)).iloc[-1])
        
        exp1 = close.ewm(span=12, adjust=False).mean()
        exp2 = close.ewm(span=26, adjust=False).mean()
        macd = float((exp1 - exp2).iloc[-1])
        
        return ma5, ma20, rsi, vol, prev_close, bb_upper, bb_lower, macd, open_price, high_p, low_p
        
    except Exception as e:
        logger.error(f"지표 계산 오류 ({code}): {e}")
        return 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0

def get_nasdaq_trend():
    try:
        nasdaq = yf.Ticker("NQ=F")
        hist = nasdaq.history(period="2d")
        if len(hist) >= 2:
            prev_close = hist["Close"].iloc[0]
            current_price = hist["Close"].iloc[1]
            return current_price > prev_close
    except Exception as e:
        logger.info(f"⚠️ 야후파이낸스 조회 오류: {e}")
    return False