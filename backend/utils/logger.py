import time
import functools
import json
import os
from typing import Any, Dict, Callable
from datetime import datetime

# 프로젝트 루트 기준 logs 폴더 설정
CWD = os.getcwd()
LOG_DIR = os.path.join(CWD, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# JSONL 로그 파일 경로
JSONL_LOG_FILE = os.path.join(LOG_DIR, "agent_execution.jsonl")

def append_jsonl_log(data: Dict[str, Any]):
    """JSONL 파일에 로그 엔트리를 조용히 추가합니다."""
    try:
        line = json.dumps(data, ensure_ascii=False, default=str)
        with open(JSONL_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass # Minimal logging should not crash the main flow

def log_node_execution(func: Callable):
    """
    LangGraph 노드 실행을 JSONL 파일로 로깅하는 데코레이터 (Minimal).
    """
    @functools.wraps(func)
    async def wrapper(state: Any, config: Any = None, *args, **kwargs):
        state_dict = state.dict() if hasattr(state, "dict") else state
        node_name = func.__name__
        start_time = time.perf_counter()
        timestamp = datetime.now().isoformat()
        
        try:
            result = await func(state, config, *args, **kwargs)
            duration = time.perf_counter() - start_time
            
            result_dict = result if isinstance(result, dict) else (result.dict() if hasattr(result, "dict") else str(result))
            
            append_jsonl_log({
                "timestamp": timestamp,
                "node": node_name,
                "status": "success",
                "duration_sec": round(duration, 4),
                "input": state_dict,
                "output": result_dict
            })
            return result
            
        except Exception as e:
            duration = time.perf_counter() - start_time
            append_jsonl_log({
                "timestamp": timestamp,
                "node": node_name,
                "status": "failed",
                "duration_sec": round(duration, 4),
                "input": state_dict,
                "error": str(e)
            })
            raise e
            
    return wrapper
