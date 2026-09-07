import yfinance as yf

def get_nasdaq_futures():
    try: return round(yf.Ticker("NQ=F").history(period="1d")["Close"].iloc[-1], 2)
    except: return None

def get_vix():
    try: return round(yf.Ticker("^VIX").history(period="1d")["Close"].iloc[-1], 2)
    except: return None

def get_usdkrw():
    try: return round(yf.Ticker("KRW=X").history(period="1d")["Close"].iloc[-1], 2)
    except: return None

def get_sox():
    try: return round(yf.Ticker("^SOX").history(period="1d")["Close"].iloc[-1], 2)
    except: return None

def get_us_10y_yield():
    try: return round(yf.Ticker("^TNX").history(period="1d")["Close"].iloc[-1], 3)
    except: return None

def get_bitcoin():
    try: return round(yf.Ticker("BTC-USD").history(period="1d")["Close"].iloc[-1], 2)
    except: return None

def get_kospi_trend():
    try:
        df = yf.Ticker("^KS11").history(period="30d")
        if df.empty: return None, None
        return round(df["Close"].iloc[-1], 2), round(df["Close"].rolling(window=20).mean().iloc[-1], 2)
    except: return None, None
