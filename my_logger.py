import logging
import os
from datetime import datetime

# 1. logs 폴더가 없으면 자동으로 생성
if not os.path.exists("logs"):
    os.makedirs("logs")

# 2. 로거(Logger) 이름 설정 (프로젝트명)
logger = logging.getLogger("KIS_AUTO_TRADER_PRO")
logger.setLevel(logging.INFO)

# 3. 출력 포맷 설정 (시간이 자동으로 찍히게 설정)
# 예: [2026-08-29 14:30:00] 🚀 메인 모니터링 시작
formatter = logging.Formatter('[%(asctime)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

# 핸들러가 중복으로 추가되는 것을 방지
if not logger.handlers:
    # 4. 터미널(화면)에 출력하는 핸들러
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    
    # 5. 텍스트 파일로 저장하는 핸들러 (매일 새로운 파일 생성)
    today = datetime.now().strftime("%Y%m%d")
    file_handler = logging.FileHandler(f"logs/trader_{today}.log", encoding='utf-8')
    file_handler.setFormatter(formatter)
    
    logger.addHandler(stream_handler)
    logger.addHandler(file_handler)