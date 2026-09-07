import re

log_path = '/home/ubuntu/KIS_AUTO_TRADER_PRO/trade.log'
try:
    with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
except Exception as e:
    print('로그 파일을 읽을 수 없습니다:', e)
    exit()

buys = {}
trades = []

last_buy_code = None
last_buy_price = None

last_sell_code = None
last_sell_price = None

for line in lines:
    # 1. 매수 조건 포착 및 진입 처리
    m_buy = re.search(r'\[매수 조건 포착\]\s*([0-9A-Za-z]+).*?현재가:\s*([\d\.]+)', line)
    if m_buy:
        last_buy_code = m_buy.group(1)
        last_buy_price = float(m_buy.group(2))

    if '가상 매수 완료' in line:
        m_code = re.search(r'가상 매수 완료\]\s*([0-9A-Za-z]+)', line)
        if m_code and last_buy_price:
            c = m_code.group(1)
            buys[c] = last_buy_price

    # 2. 매도 신호 및 청산 처리
    m_sell = re.search(r'\[매도 신호\]\s*([0-9A-Za-z]+).*?현재가:\s*([\d\.]+)', line)
    if m_sell:
        last_sell_code = m_sell.group(1)
        last_sell_price = float(m_sell.group(2))

    if '가상 매도 완료' in line:
        m_code = re.search(r'가상 매도 완료\]\s*([0-9A-Za-z]+)', line)
        if m_code:
            c = m_code.group(1)
            sell_p = last_sell_price
            if c in buys and sell_p:
                buy_p = buys.pop(c)
                diff = sell_p - buy_p
                rate = (diff / buy_p) * 100
                trades.append((c, buy_p, sell_p, diff, rate))

print('='*55)
print('          📊 실시간 가상매매 정산 리포트')
print('='*55)
total_profit = 0
win_count = 0

for code, bp, sp, diff, rate in trades:
    total_profit += diff
    icon = '🔴' if diff > 0 else '🔵'
    if diff > 0:
        win_count += 1
    print(f'{icon} [{code}] 매수: {bp:,.0f} | 매도: {sp:,.0f} | 손익: {diff:+,.0f}원 ({rate:+.2f}%)')

print('-'*55)
total_count = len(trades)
win_rate = (win_count / total_count * 100) if total_count > 0 else 0
print(f'총 청산 종목: {total_count}건 (승리: {win_count}건 / 패배: {total_count - win_count}건)')
print(f'현재 승률    : {win_rate:.1f}%')
print(f'누적 확정손익: {total_profit:+,.0f}원 (1주 기준)')
print(f'현재 보유 중 : {len(buys)}개 종목 감시 진행 중')
print('='*55)
