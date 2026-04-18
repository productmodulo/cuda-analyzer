from typing import Optional
from enum import Enum
from pydantic import BaseModel
from agent.schemas import CodeAnalysisResult

class AgentStatus(str, Enum):
    START = "start"
    ARCHITECTING = "architecting"
    BENCHMARKING = "benchmarking"
    PROFILING = "profiling"
    CRITIQUING = "critiquing"
    COMPLETED = "completed"
    FAILED = "failed"

class AgentState(BaseModel):
    # Inputs
    original_code: str
    user_question: str
    
    # Current Working Artifacts
    kernel_code: Optional[str] = None
    benchmark_code: Optional[str] = None
    
    # Last Profiling Results
    nsys_report: Optional[str] = None
    ncu_report: Optional[str] = None
    is_accurate: Optional[bool] = None
    execution_time_ms: Optional[float] = None
    
    # Baseline for Comparison (Optimization Tracking)
    baseline_time_ms: Optional[float] = None
    improvement_rate: Optional[float] = None
    
    # Control
    iteration_count: int = 0
    max_iterations: int = 3
    status: AgentStatus = AgentStatus.START
    
    # Final Result
    analysis_result: Optional[CodeAnalysisResult] = None
    error_message: Optional[str] = None
