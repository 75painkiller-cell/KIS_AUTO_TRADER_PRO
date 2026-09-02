class RiskManager:
    def __init__(self, stop_loss_pct=-2.0, take_profit_pct=3.0, trailing_stop_drop=1.5):
        self.stop_loss_pct = stop_loss_pct          # 손절 기준 (-2%)
        self.take_profit_pct = take_profit_pct      # 1차 익절 기준 (+3%)
        self.trailing_stop_drop = trailing_stop_drop# 고점 대비 하락 익절 기준 (-1.5%)
        self.entry_prices = {}                      # {종목코드: 평균진입가}
        self.highest_prices = {}                    # {종목코드: 보유 중 최고가}

    def register_position(self, symbol, entry_price):
        """포지션 진입 시 초기화"""
        self.entry_prices[symbol] = entry_price
        self.highest_prices[symbol] = entry_price

    def check_exit_keyword(self, symbol, current_price):
        """현재가를 받아 매도(손절/익절) 여부 판단"""
        if symbol not in self.entry_prices:
            return None, "NO_POSITION"

        entry_price = self.entry_prices[symbol]
        highest_price = self.highest_prices[symbol]

        if current_price > highest_price:
            self.highest_prices[symbol] = current_price
            highest_price = current_price

        pnl_pct = ((current_price - entry_price) / entry_price) * 100
        drop_from_high = ((highest_price - current_price) / highest_price) * 100

        # 손절 조건 (-2% 이탈)
        if pnl_pct <= self.stop_loss_pct:
            return "SELL_STOP_LOSS", f"손절 이탈 ({pnl_pct:.2f}%)"

        # 트레일링 스탑 조건
        if pnl_pct >= 2.0 and drop_from_high >= self.trailing_stop_drop:
            return "SELL_TRAILING_STOP", f"트레일링 스탑 익절 (고점 대비 -{drop_from_high:.2f}%)"

        # 목표 수익 익절 조건
        if pnl_pct >= self.take_profit_pct:
            return "SELL_TAKE_PROFIT", f"목표 수익 익절 ({pnl_pct:.2f}%)"

        return None, "HOLD"