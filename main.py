import asyncio
from core.config import load_config
from core.engine import run_trading_system
from utils.my_logger import logger

def main():
    logger.info("=== KIS_AUTO_TRADER_PRO 통합 시스템 시작 ===")
    
    bot_config = load_config("config.yaml")
    if not bot_config: 
        return
    
    try:
        asyncio.run(run_trading_system(bot_config))
    except KeyboardInterrupt:
        logger.info("\n시스템을 안전하게 종료합니다.")

if __name__ == "__main__":
    main()