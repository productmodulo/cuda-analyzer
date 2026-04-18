from pydantic import BaseModel, Field
from typing import List, Optional

class KernelCodeOutput(BaseModel):
    explanation: str = Field(description="Explanation of the CUDA kernel code and its structure in Korean")
    kernel_code: str = Field(description="The full CUDA source code (kernel.cu)")

class BenchmarkCodeOutput(BaseModel):
    explanation: str = Field(description="Explanation of the benchmark script in Korean")
    benchmark_code: str = Field(description="The full Python benchmark script (benchmark.py) using PyTorch/CuPy")

class OptimizationCriticOutput(BaseModel):
    analysis: str = Field(description="Detailed analysis of profiling results and current performance in Korean")
    should_refine: bool = Field(description="Whether to continue optimization (True) or finish (False)")
    suggestion: Optional[str] = Field(None, description="Specific suggestion for the next optimization step if should_refine is True")

class KernelOptimization(BaseModel):
    kernel_name: str = Field(description="Name of the CUDA kernel")
    bottleneck_analysis: str = Field(description="Analysis of the current bottleneck for this kernel")
    optimization_suggestion: str = Field(description="Suggested code modifications to improve performance")
    optimized_code: str = Field(description="The improved CUDA code snippet implementing the suggestions")

class CodeAnalysisResult(BaseModel):
    summary: str = Field(description="Friendly explanation and overall summary of the analysis for the user in Korean")
    optimizations: List[KernelOptimization] = Field(default_factory=list, description="List of kernel optimizations")
    final_execution_time_ms: Optional[float] = Field(None, description="Final measured execution time")
    total_speedup: Optional[str] = Field(None, description="Total speedup achieved compared to baseline")
