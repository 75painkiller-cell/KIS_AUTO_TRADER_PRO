import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../data/trade_history.db")

def init_db():
    """매매 일지 저장을 위한 SQLite 테이블 생성"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            symbol TEXT,
            name TEXT,
            side TEXT,
            price REAL,
            qty INTEGER,
            net_profit REAL,
            reason TEXT
        )
    """)
    conn.commit()
    conn.close()

def log_trade(timestamp, symbol, name, side, price, qty, net_profit=0.0, reason=""):
    """거래 내역을 데이터베이스에 기록"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO trades (timestamp, symbol, name, side, price, qty, net_profit, reason)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (timestamp, symbol, name, side, price, qty, net_profit, reason))
    conn.commit()
    conn.close()

def get_performance_stats():
    """누적 승률 및 손익 통계 계산"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*), SUM(net_profit) FROM trades WHERE side='SELL'")
    total_sells, total_profit = cursor.fetchone()
    
    cursor.execute("SELECT COUNT(*) FROM trades WHERE side='SELL' AND net_profit > 0")
    wins = cursor.fetchone()[0]
    
    conn.close()
    
    total_sells = total_sells or 0
    total_profit = total_profit or 0.0
    win_rate = (wins / total_sells * 100) if total_sells > 0 else 0.0
    
    return total_sells, wins, win_rate, total_profit