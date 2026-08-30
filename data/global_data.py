import yfinance as yf

def get_nasdaq_futures():
    """나스닥 100 선물 (NQ=F)"""
    try:
        nq = yf.Ticker("NQ=F")
        return round(nq.history(period="1d")['Close'].iloc[-1], 2)
    except Exception:
        return None

def get_vix():
    """VIX 변동성 지수 (^VIX)"""
    try:
        vix = yf.Ticker("^VIX")
        return round(vix.history(period="1d")['Close'].iloc[-1], 2)
    except Exception:
        return None

def get_usdkrw():
    """원/달러 환율 (KRW=X)"""
    try:
        krw = yf.Ticker("KRW=X")
        return round(krw.history(period="1d")['Close'].iloc[-1], 2)
    except Exception:
        return None
import yfinance as yf

def get_sox():
    """필라델피아 반도체 지수 조회"""
    try:
        ticker = yf.Ticker("^SOX")
        return round(ticker.history(period="1d")['Close'].iloc[-1], 2)
    except Exception:
        return None

def get_us_10y_yield():
    """미국 10년물 국채 금리 조회"""
    try:
        ticker = yf.Ticker("^TNX")
        return round(ticker.history(period="1d")['Close'].iloc[-1], 3)
    except Exception:
        return None

def get_bitcoin():
    """비트코인 달러 가격 조회"""
    try:
        ticker = yf.Ticker("BTC-USD")
        return round(ticker.history(period="1d")['Close'].iloc[-1], 2)
    except Exception:
        return None    