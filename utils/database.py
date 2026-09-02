import sqlite3
import os
from datetime import datetime

# 프로젝트 루트 경로 내 data 폴더 안에 db 생성
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "trading_bot.db")

def init_db():
    """데이터베이스 및 테이블 초기화 (최초 실행 시 자동 생성)"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. 매매 체결 내역 테이블
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            symbol TEXT,
            action TEXT,
            price REAL,
            quantity INTEGER,
            reason TEXT
        )
    ''')
    
    # 2. 고래 포착 로그 테이블
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS whale_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            symbol TEXT,
            price REAL,
            volume INTEGER
        )
    ''')
    conn.commit()
    conn.close()

def log_trade(symbol, action, price, quantity, reason):
    """매매 체결 내역(매수/매도)을 DB에 기록"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO trades (timestamp, symbol, action, price, quantity, reason)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), symbol, action, price, quantity, reason))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"DB 체결 기록 에러: {e}")

def log_whale(symbol, price, volume):
    """실시간 고래(대량 거래량) 포착 내역을 DB에 기록"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO whale_logs (timestamp, symbol, price, volume)
            VALUES (?, ?, ?, ?)
        ''', (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), symbol, price, volume))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"DB 고래 로그 기록 에러: {e}")