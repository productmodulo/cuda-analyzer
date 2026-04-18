import time
import functools
import json
import os
from typing import Any, Dict, Callable
from loguru import logger

# 프로젝트 루트 기준 logs 폴더 생성
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# loguru 설정: 콘솔 출력 및 파일 저장 (날짜별 순환 및 압축)
LOG_FILE = os.path.join(LOG_DIR, "agent_execution.log")
logger.add(
    LOG_FILE, 
    rotation="10 MB", 
    retention="10 days", 
    compression="zip", 
    encoding="utf-8",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
)

def log_node_execution(func: Callable):
    """
    LangGraph 노드 실행을 loguru로 로깅하는 데코레이터.
    raw input, raw output, 실행 시간을 logs/ 폴더에 기록합니다.
    """
    @functools.wraps(func)
    async def wrapper(state: Dict[str, Any], config: Any = None, *args, **kwargs):
        node_name = func.__name__
        start_time = time.perf_counter()
        
        # 입력 로깅
        logger.info(f"--- Node Start: {node_name} ---")
        logger.info(f"Node Input [{node_name}]: {json.dumps(state, default=str, ensure_ascii=False)}")
        
        try:
            # 노드 실행
            result = await func(state, config, *args, **kwargs)
            
            end_time = time.perf_counter()
            duration = end_time - start_time
            
            # 출력 로깅
            logger.info(f"Node Output [{node_name}]: {json.dumps(result, default=str, ensure_ascii=False)}")
            logger.info(f"Node Duration [{node_name}]: {duration:.4f} seconds")
            logger.info(f"--- Node End: {node_name} ---")
            
            return result
        except Exception as e:
            end_time = time.perf_counter()
            duration = end_time - start_time
            logger.error(f"Node Error [{node_name}]: {str(e)}")
            logger.error(f"Node Duration [{node_name}]: {duration:.4f} seconds (Failed)")
            raise e
            
    return wrapper
