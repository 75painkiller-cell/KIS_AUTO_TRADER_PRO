from account import get_balance, get_cash
from config import INVEST_RATIO, MAX_ORDER_AMOUNT
from logger import error, info, warning
from market import get_current_price

def get_my_stocks():
    """
    현재 계좌에 보유 중인 주식 포트폴리오(잔고) 목록을 가져옵니다.
    """
    try:
        data = get_balance()
        if not data:
            return []

        stocks = []
        output = data.get("output1", [])
        
        if not isinstance(output, list):
            return stocks

        for item in output:
            try:
                # 보유 수량이 0인 종목은 제외
                qty = int(item.get("hldg_qty", 0))
                if qty <= 0:
                    continue

                code = item.get("pdno", "")
                name = item.get("prdt_name", "")
                
                # 매입 금액 및 매입 단가 안전한 형변환 (None 방어)
                buy_amount = float(item.get("pchs_amt") or 0)
                buy_price = float(item.get("pchs_avg_pric") or 0)
                
                # 매입 단가가 0으로 넘어올 경우 직접 계산
                if buy_price == 0 and qty > 0:
                    buy_price = buy_amount / qty

                # 현재가 조회 (결측치일 경우 시장가 별도 조회)
                current_price = float(item.get("prpr") or 0)
                if current_price <= 0 and code:
                    current_price = float(get_current_price(code))

                profit_rate = float(item.get("evlu_pfls_rt") or 0)
                profit = float(item.get("evlu_pfls_amt") or 0)
                eval_amount = float(item.get("evlu_amt") or 0)

                stocks.append({
                    "code": code,
                    "name": name,
                    "qty": qty,
                    "buy_price": buy_price,
                    "current_price": current_price,
                    "profit_rate": profit_rate,
                    "profit": profit,
                    "eval_amount": eval_amount,
                    "buy_amount": buy_amount,
                })
            except Exception as e:
                # 개별 종목 파싱 중 에러가 나도 다른 종목은 정상적으로 불러오도록 방어
                error(f"[포트폴리오] {item.get('prdt_name', '알수없는종목')} 데이터 파싱 오류: {e}", exc_info=True)

        return stocks
        
    except Exception as e:
        error(f"[포트폴리오] 잔고 조회 실패: {e}", exc_info=True)
        return []


def get_buy_quantity(code: str) -> int:
    """
    투자 비중(INVEST_RATIO)과 최대 주문 금액(MAX_ORDER_AMOUNT)을 
    고려하여 특정 종목의 매수 가능 수량을 산출합니다.
    """
    try:
        cash = get_cash()
        if cash <= 0:
            warning("[매수수량] 주문 가능한 예수금이 없습니다.")
            return 0

        # 투자 가능 금액 산출 (전체 예수금 * 투자비율과 최대 투자금액 중 작은 값 선택)
        invest_money = min(int(cash * INVEST_RATIO), MAX_ORDER_AMOUNT)
        
        price = get_current_price(code)
        if price <= 0:
            warning(f"[매수수량] {code} 현재가 조회 실패로 수량 산출 불가")
            return 0

        qty = invest_money // price
        
        if qty < 1:
            warning(f"[매수수량] 투자금 부족 (할당금액: {invest_money:,.0f}원 / {code} 현재가: {price:,.0f}원)")
            return 0

        info(f"[매수수량] 산출 완료: {code} -> {qty}주 (예상 매수금액: {qty * price:,.0f}원)")
        return int(qty)
        
    except Exception as e:
        error(f"[매수수량] 계산 중 오류 발생: {e}", exc_info=True)
        return 0