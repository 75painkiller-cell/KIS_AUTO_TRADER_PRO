import time
import requests
from typing import Tuple, Dict, Any, Optional
from auth import get_access_token
from config import ACNT_PRDT_CD, APP_KEY, APP_SECRET, CANO, IS_PAPER, URL_BASE, USE_STOP_LOSS, USE_TAKE_PROFIT
from logger import error, info, warning
from risk import check_exit
from state_manager import StateManager  # 파일명이 다르면 db_manager를 해당 파일명으로 수정하세요

# 전역(Global)으로 DB 매니저 객체 생성
db = StateManager()

def _request_order(headers: Dict[str, str], body: Dict[str, str]) -> Tuple[int, Dict[str, Any]]:
    """한국투자증권 API로 매수/매도 주문 요청을 보내는 공통 함수"""
    url = f"{URL_BASE.rstrip('/')}/uapi/domestic-stock/v1/trading/order-cash"
    
    for attempt in range(1, 4):
        try:
            res = requests.post(url=url, headers=headers, json=body, timeout=5)
            data = res.json()
            
            if res.status_code == 200:
                # API 자체 에러 메시지 처리 방어막 추가
                if data.get("rt_cd") != "0":
                    error(f"[주문] API 응답 에러: {data.get('msg1', '알 수 없는 오류')}")
                return res.status_code, data
                
            time.sleep(1)
        except requests.exceptions.RequestException as e:
            error(f"[주문] 네트워크 통신 시도 {attempt}/3 실패: {e}")
            time.sleep(0.5)
            
    return 500, {"rt_cd": "-1", "msg1": "서버 통신 실패로 주문을 넣지 못했습니다."}

def buy_stock(code: str, qty: int, price: int = 0) -> Dict[str, Any]:
    """시장가 매수 주문 실행 및 DB 기록"""
    if qty <= 0:
        warning("[주문] 매수 수량이 0 이하이므로 주문을 생략합니다.")
        return {}
        
    token = get_access_token()
    if not token:
        error("[주문] 유효한 접근 토큰이 없어 매수 주문을 취소합니다.")
        return {}

    headers = {
        "Content-Type": "application/json",
        "authorization": f"Bearer {token}",
        "appkey": APP_KEY,
        "appsecret": APP_SECRET,
        "tr_id": "VTTC0802U" if IS_PAPER else "TTTC0802U",
        "custtype": "P",
    }
    
    body = {
        "CANO": CANO,
        "ACNT_PRDT_CD": ACNT_PRDT_CD,
        "PDNO": code,
        "ORD_DVSN": "01", # 시장가 주문
        "ORD_QTY": str(qty),
        "ORD_UNPR": "0",  # 시장가일 경우 단가는 0으로 세팅
    }
    
    _, data = _request_order(headers, body)
    
    # 매수 주문이 성공했다면 DB에 기록 저장
    if data.get("rt_cd") == "0":
        db.save_trade(code, price, qty, "BUY")
        info(f"[{code}] {qty}주 매수 주문 체결 완료 및 DB 저장 (시장가)")
        
    return data

def sell_stock(code: str, qty: int, price: int = 0) -> Dict[str, Any]:
    """시장가 매도 주문 실행 및 DB 기록"""
    if qty <= 0:
        return {}
        
    token = get_access_token()
    if not token:
        error("[주문] 유효한 접근 토큰이 없어 매도 주문을 취소합니다.")
        return {}

    headers = {
        "Content-Type": "application/json",
        "authorization": f"Bearer {token}",
        "appkey": APP_KEY,
        "appsecret": APP_SECRET,
        "tr_id": "VTTC0801U" if IS_PAPER else "TTTC0801U",
        "custtype": "P",
    }
    
    body = {
        "CANO": CANO,
        "ACNT_PRDT_CD": ACNT_PRDT_CD,
        "PDNO": code,
        "ORD_DVSN": "01", # 시장가 주문
        "ORD_QTY": str(qty),
        "ORD_UNPR": "0",
    }
    
    _, data = _request_order(headers, body)
    
    # 매도 주문이 성공했다면 DB에 기록 저장
    if data.get("rt_cd") == "0":
        db.save_trade(code, price, qty, "SELL")
        info(f"[{code}] {qty}주 매도 주문 체결 완료 및 DB 저장 (시장가)")
        
    return data

def auto_sell(code: str, qty: int, buy_price: int, current_price: int) -> Optional[Dict[str, Any]]:
    """익절/손절 조건 확인 후 청산 주문 및 일일 누적 손익(DB) 업데이트"""
    result = check_exit(buy_price, current_price)
    
    # pnl_amount가 양수면 수익, 음수면 손실
    pnl_amount = (current_price - buy_price) * qty

    # 1. 익절 달성 시
    if result == "SELL_PROFIT" and USE_TAKE_PROFIT:
        info(f"[{code}] 📈 익절 조건 달성 -> 청산 주문 실행 (매입가: {buy_price:,}원 -> 현재가: {current_price:,}원)")
        res = sell_stock(code, qty, current_price)
        
        if res.get("rt_cd") == "0":
            # DB의 update_daily_loss는 '손실'을 더하는 함수이므로 마이너스(-)를 붙여 수익만큼 손실액을 깎음
            db.update_daily_loss(int(-pnl_amount))
            return res

    # 2. 손절 달성 시
    elif result == "SELL_LOSS" and USE_STOP_LOSS:
        warning(f"[{code}] 📉 손절 조건 달성 -> 청산 주문 실행 (매입가: {buy_price:,}원 -> 현재가: {current_price:,}원)")
        res = sell_stock(code, qty, current_price)
        
        if res.get("rt_cd") == "0":
            # 손실 났을 때는 양수로 변환하여 일일 손실 누적치 증가
            db.update_daily_loss(int(-pnl_amount))
            return res

    return None