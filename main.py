import yaml
import asyncio
import datetime
import requests
import api_client

# 본인의 한투 HTS 접속 아이디 입력
HTS_USER_ID = "본인HTS아이디" 

def load_config(filepath="config.yaml"):
    """YAML 전략 설정 파일 로드"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"오류: {filepath} 파일을 찾을 수 없습니다.")
        return None

async def fetch_condition_stocks(access_token, seq_number, name):
    """실제 KIS HTS 조건검색식 결과 조회 API (t8427 역할)"""
    url = f"{api_client.URL_BASE}/uapi/domestic-stock/v1/quotations/psearch-result"
    headers = {
        "content-type": "application/json; charset=utf-8",
        "authorization": f"Bearer {access_token}",
        "appkey": api_client.APP_KEY,
        "appsecret": api_client.APP_SECRET,
        "tr_id": "HHKST03900400",
        "custtype": "P"
    }
    params = {
        "user_id": HTS_USER_ID,
        "seq": seq_number
    }

    # requests의 동기적 딜레이로 인한 병목을 막기 위해 비동기 백그라운드 실행
    loop = asyncio.get_event_loop()
    res = await loop.run_in_executor(None, lambda: requests.get(url, headers=headers, params=params))

    if res.status_code == 200:
        data = res.json()
        # 검색된 종목코드(code)만 추출
        return [item['code'] for item in data.get('output2', [])]
    else:
        print(f"[{name}] 조건검색 호출 실패: {res.text}")
        return []

async def monitor_strategy(strategy, access_token):
    """개별 전략의 종목 감시 루프"""
    name = strategy['name']
    cond_id = strategy['condition_id']
    interval = strategy['poll_interval_sec']
    
    print(f"▶ [{name}] 감시 시작 (조건식 번호: {cond_id} / 갱신주기: {interval}초)")
    
    while True:
        now = datetime.datetime.now().strftime("%H:%M:%S")
        
        # 1. KIS API로 실시간 조건검색 종목 리스트 확보
        target_stocks = await fetch_condition_stocks(access_token, cond_id, name)
        print(f"[{now}] [{name}] 포착 종목: {target_stocks}")
        
        # 2. 향후 여기에 웹소켓 실시간 현재가와 target_stocks를 비교하는 로직 추가
        
        # 3. KIS API 호출 제한(Rate Limit) 방지를 위한 대기
        await asyncio.sleep(interval)

async def main():
    print("=== KIS_AUTO_TRADER_PRO 통합 시스템 시작 ===")
    
    # 1. 환경 설정 로드
    bot_config = load_config("config.yaml")
    if not bot_config: return
    
    # 2. 한투 API 통신용 토큰 및 키 발급
    print("API 인증 토큰을 발급받습니다...")
    rest_token = api_client.get_access_token()
    ws_key = api_client.get_ws_approval_key()
    
    print(f"총 {len(bot_config['strategies'])}개의 전략 엔진을 가동합니다.\n" + "="*50)
    
    # 3. YAML에 등록된 개수만큼 비동기 감시 태스크 생성
    tasks = []
    for strat in bot_config['strategies']:
        tasks.append(monitor_strategy(strat, rest_token))
        
    # 4. 모든 전략 동시 실행 (병렬 처리)
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n시스템을 안전하게 종료합니다.")