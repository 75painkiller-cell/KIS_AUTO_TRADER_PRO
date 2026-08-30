import logging
import os
from logging.handlers import RotatingFileHandler

# 프로젝트 루트 기준 절대 경로 설정 (서버 백그라운드 실행 시 경로 꼬임 완벽 방지)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")

os.makedirs(LOG_DIR, exist_ok=True)

# 로거 생성 및 기본 레벨 설정
logger = logging.getLogger("AutoTrader")
logger.setLevel(logging.INFO)

# 이미 핸들러가 등록되어 있다면 중복 추가 방지 (로그 2번씩 찍히는 현상 방지)
if not logger.handlers:
    formatter = logging.Formatter("%(asctime)s | %(levelname)-7s | %(message)s")

    # 1. 파일 핸들러 (최대 10MB, 최대 5개 파일 보관 후 오래된 것부터 자동 삭제)
    file_handler = RotatingFileHandler(
        os.path.join(LOG_DIR, "autotrader.log"),
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    # 2. 콘솔 출력 핸들러 (터미널 출력용)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)


def debug(message):
    """
    개발 및 테스트용 상세 로그 (현재는 INFO 레벨이라 출력되지 않으나, 
    logger.setLevel(logging.DEBUG)로 낮추면 보입니다)
    """
    logger.debug(message)


def info(message):
    """일반적인 실행 흐름 로그 (매수/매도 완료 등)"""
    logger.info(message)


def warning(message):
    """주의가 필요한 상황 (잔고 부족, 지연 발생 등)"""
    logger.warning(message)


def error(message, exc_info=False):
    """
    치명적인 에러 발생 시 사용
    error("에러 메시지", exc_info=True)로 호출하면
    상세 에러 트레이스백(몇 번째 줄에서 에러 났는지)까지 함께 로그에 남깁니다.
    """
    logger.error(message, exc_info=exc_info)


if __name__ == "__main__":
    info("🚀 프로그램 시작")
    warning("⚠️ 테스트 경고")
    error("🚨 테스트 오류", exc_info=True) # exc_info=True 테스트