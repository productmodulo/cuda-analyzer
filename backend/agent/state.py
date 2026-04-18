from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field
from agent.schemas import KernelMetrics, KernelOptimization, VizData

class AgentStatus(str, Enum):
    START = "start"
    INIT_COPY = "init_copy"
    INIT_BENCHMARK = "init_benchmark"
    INIT_PROFILE = "init_profile"
    ARCHITECTING = "architecting"
    PROFILING = "profiling"
    CRITIQUING = "critiquing"
    REPORTING = "reporting"
    VISUALIZING = "visualizing"
    COMPLETED = "completed"
    FAILED = "failed"

class AgentState(BaseModel):
    # 0. Inputs
    raw_cuda_code: str
    user_query: str
    
    # 1. Base Artifacts
    original_kernel: Optional[str] = None
    original_metrics: Optional[KernelMetrics] = None
    benchmark_code: Optional[str] = None
    
    # 2. Optimization Tracking (Gold Standard)
    best_kernel: Optional[str] = None
    best_metrics: Optional[KernelMetrics] = None
    
    # 3. Evaluation Cycle
    current_kernel: Optional[str] = None
    current_metrics: Optional[KernelMetrics] = None
    
    # 4. History & Control
    optimization_log: List[Dict[str, Any]] = Field(default_factory=list)
    iteration: int = 0
    max_iterations: int = 3
    status: AgentStatus = AgentStatus.START
    
    # 5. Final Outputs
    final_report: Optional[str] = None
    viz_data: Optional[VizData] = None
    error_message: Optional[str] = None
