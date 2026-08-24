from collections import deque
import time
from typing import Tuple

class OpenInterestTracker:
    """
    일정 시간(window_seconds) 동안의 미결제약정(Open Interest) 변화량을 추적하는 클래스입니다.
    기본값은 180초(3분)입니다.
    """
    def __init__(self, window_seconds: int = 180):
        self.window_seconds = window_seconds
        self.history = deque()

    def update(self, current_oi: int) -> Tuple[int, int]:
        now = time.time()
        
        # [방어막 추가] API 통신 중 current_oi가 문자열('1500')로 들어와도 에러가 나지 않도록 정수 변환
        try:
            current_oi = int(current_oi)
        except (ValueError, TypeError):
            # 비정상적인 값이 들어오면 변화량 0으로 처리
            return 0, 0
            
        self.history.append((now, current_oi))

        # 설정한 시간(window_seconds)이 지난 과거 데이터는 제거 (슬라이딩 윈도우 갱신)
        while self.history and (now - self.history[0][0] > self.window_seconds):
            self.history.popleft()

        # 비교할 데이터가 부족한 초기 상태에서는 0 반환
        if len(self.history) < 2:
            return 0, 0

        oldest_time, oldest_oi = self.history[0]
        
        accum_change = current_oi - oldest_oi
        actual_secs = int(now - oldest_time)
        
        return accum_change, actual_secs