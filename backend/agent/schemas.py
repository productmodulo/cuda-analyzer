from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class KernelMetrics(BaseModel):
    nsys_report: Optional[str] = Field(None, description="nsys profiling summary")
    ncu_report: Optional[str] = Field(None, description="ncu profiling summary")
    execution_time_ms: float = Field(0.0, description="Measured execution time in ms")
    is_accurate: bool = Field(False, description="Whether the computation result is correct")
    error_log: Optional[str] = Field(None, description="Compilation or runtime error log")

class KernelOptimization(BaseModel):
    iteration: int
    technique: str = Field(description="Optimization technique used")
    improvement: str = Field(description="Performance improvement summary")
    status: str = Field(description="Success or Failure of this attempt")

class CodeAnalysisResult(BaseModel):
    summary: str
    optimizations: List[KernelOptimization]
    final_execution_time_ms: Optional[float]
    total_speedup: Optional[str]

class VizData(BaseModel):
    title: str
    original_code: str
    best_code: str
    original_metrics: Dict[str, Any]
    best_metrics: Dict[str, Any]
    optimization_log: List[Dict[str, Any]]
    final_report: str
    component_code: Optional[str] = None

class OriginalKernelOutput(BaseModel):
    explanation: str = Field(description="Explanation of the cleaned code in Korean")
    original_kernel: str = Field(description="The cleaned standalone CUDA source code")

class FinalReportOutput(BaseModel):
    report: str = Field(description="The final Markdown report in Korean")

class BenchmarkCodeOutput(BaseModel):
    explanation: str = Field(description="Explanation of the benchmark script in Korean")
    benchmark_code: str = Field(description="The full Python benchmark script (benchmark.py) using PyTorch/CuPy")

class KernelCodeOutput(BaseModel):
    explanation: str = Field(description="Explanation of the CUDA kernel code and its structure in Korean")
    kernel_code: str = Field(description="The full CUDA source code (kernel.cu)")
