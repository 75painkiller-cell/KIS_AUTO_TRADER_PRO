import requests
from core.auth import get_access_token
from utils.config import ACNT_PRDT_CD, APP_KEY, APP_SECRET, CANO, IS_PAPER, URL_BASE
from utils.logger import error

def get_balance():
    token = get_access_token()
    if not token:
        return None

    url = f"{URL_BASE.rstrip('/')}/uapi/domestic-stock/v1/trading/inquire-balance"
    headers = {
        "content-type": "application/json; charset=utf-8",
        "authorization": f"Bearer {token}",
        "appkey": APP_KEY,
        "appsecret": APP_SECRET,
        "tr_id": "VTTC8434R" if IS_PAPER else "TTTC8434R",
    }
    params = {
        "CANO": CANO,
        "ACNT_PRDT_CD": ACNT_PRDT_CD,
        "AFHR_FLPR_YN": "N",
        "OFLD_DVSN": "00",
        "INQR_DVSN": "02",
        "UNPR_DVSN": "01",
        "FUND_STTL_ICLD_YN": "N",
        "FNCG_AMT_AUTO_RDPT_YN": "N",
        "PRCS_DVSN": "00",
        "CTX_AREA_FK100": "",
        "CTX_AREA_NK100": "",
    }

    try:
        res = requests.get(url, headers=headers, params=params, timeout=10)
        if res.status_code == 200:
            return res.json()
        else:
            # 상태 코드가 200(성공)이 아닐 때 에러 내용 로깅 (추가된 부분)
            error(f"[계좌] API 호출 실패 (상태코드: {res.status_code}) - {res.text}")
    except Exception as e:
        error(f"[계좌] 잔고 조회 예외 발생: {e}")
    return None


def get_cash():
    data = get_balance()
    if data and data.get("rt_cd") == "0":
        output2 = data.get("output2", [])
        if output2:
            return int(output2[0].get("dnca_tot_amt", 0))
    return 0