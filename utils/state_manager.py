import sqlite3
import os
from datetime import datetime
from utils.logger import error, info

class StateManager:
    """
    자동매매 봇의 거래 기록과 일일 손익 상태를 관리하는 SQLite DB 매니저
    """
    def __init__(self, db_name: str = "trade_state.db"):
        # DB 파일이 저장될 경로 설정 (프로젝트 최상단, 리눅스 서버 백그라운드 구동 대비)
        self.db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), db_name)
        
        # 스레드 충돌 방지 및 DB 락(Lock) 대기 시간(timeout) 10초 설정 추가
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False, timeout=10.0)
        self.cursor = self.conn.cursor()
        self.init_db()

    def init_db(self):
        """초기 테이블 생성 (파일이 없으면 자동 생성됨)"""
        try:
            # 1. 매매 기록을 저장하는 테이블
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    ticker TEXT,
                    price INTEGER,
                    quantity INTEGER,
                    trade_type TEXT -- 'BUY' 또는 'SELL'
                )
            ''')
            
            # 2. 일일 손익 및 매매 횟수 상태를 관리하는 테이블
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS daily_state (
                    date TEXT PRIMARY KEY,
                    daily_loss INTEGER DEFAULT 0,
                    trade_count INTEGER DEFAULT 0
                )
            ''')
            self.conn.commit()
        except sqlite3.Error as e:
            error(f"[DB] 초기 테이블 생성 중 오류 발생: {e}", exc_info=True)

    def save_trade(self, ticker: str, price: int, quantity: int, trade_type: str):
        """매수/매도 체결 시 기록 저장"""
        try:
            self.cursor.execute('''
                INSERT INTO trades (ticker, price, quantity, trade_type)
                VALUES (?, ?, ?, ?)
            ''', (ticker, price, quantity, trade_type))
            self.conn.commit()
            
            # 거래 기록 성공 시 로그 출력
            info(f"[DB] 기록 완료: [{trade_type}] {ticker} (단가: {price:,}원, 수량: {quantity}주)")
        except sqlite3.Error as e:
            error(f"[DB] 매매 기록 저장 실패 ({ticker}): {e}", exc_info=True)

    def update_daily_loss(self, loss_amount: int):
        """일일 손실 금액 업데이트"""
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            
            # 오늘 날짜의 레코드가 없으면 생성
            self.cursor.execute('INSERT OR IGNORE INTO daily_state (date) VALUES (?)', (today,))
            
            # 손실액 누적
            self.cursor.execute('''
                UPDATE daily_state 
                SET daily_loss = daily_loss + ? 
                WHERE date = ?
            ''', (loss_amount, today))
            self.conn.commit()
        except sqlite3.Error as e:
            error(f"[DB] 일일 손실 업데이트 실패: {e}", exc_info=True)

    def get_daily_loss(self) -> int:
        """오늘의 누적 손실액 조회"""
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            self.cursor.execute('SELECT daily_loss FROM daily_state WHERE date = ?', (today,))
            result = self.cursor.fetchone()
            return int(result[0]) if result else 0
        except sqlite3.Error as e:
            error(f"[DB] 손실액 조회 실패: {e}", exc_info=True)
            return 0

    def close(self):
        """DB 연결 종료 (프로그램 종료 시 호출)"""
        try:
            self.conn.close()
        except sqlite3.Error as e:
            error(f"[DB] 연결 종료 실패: {e}")

# ==========================================
# 테스트용 코드
# ==========================================
if __name__ == "__main__":
    manager = StateManager()
    manager.save_trade("069500", 35000, 10, "BUY")
    print(f"현재 누적 손실: {manager.get_daily_loss():,}원")
    print("✅ DB 세팅 및 테스트 완료!")