import torch
import json
import numpy as np
from torch.utils.cpp_extension import load
import sys

# CUDA 커널 소스 코드 (Vectorized memory access 및 Loop unrolling 적용)
cuda_source = """
#include <cuda_runtime.h>
#include <torch/extension.h>

__device__ __forceinline__ float warpReduceSum(float val) {
    #pragma unroll
    for (int offset = 16; offset > 0; offset >>= 1)
        val += __shfl_down_sync(0xffffffff, val, offset);
    return val;
}

__device__ __forceinline__ float blockReduceSum(float val) {
    static __shared__ float shared[32]; 
    int lane = threadIdx.x % 32;
    int wid = threadIdx.x / 32;

    val = warpReduceSum(val);

    if (lane == 0) shared[wid] = val;
    __syncthreads();

    val = (threadIdx.x < (blockDim.x / 32)) ? shared[lane] : 0.0f;
    if (wid == 0) val = warpReduceSum(val);

    return val;
}

__global__ void reduction_kernel_opt(const float* __restrict__ input, float* __restrict__ output, int N) {
    float sum = 0.0f;
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    int stride = blockDim.x * gridDim.x;

    // float4를 이용한 Vectorized Load로 메모리 대역폭 최적화
    const float4* input4 = reinterpret_cast<const float4*>(input);
    int N4 = N / 4;
    
    for (int i = idx; i < N4; i += stride) {
        float4 val = input4[i];
        sum += val.x + val.y + val.z + val.w;
    }

    // 남은 요소 처리
    for (int i = N4 * 4 + idx; i < N; i += stride) {
        sum += input[i];
    }

    sum = blockReduceSum(sum);

    if (threadIdx.x == 0) {
        atomicAdd(output, sum);
    }
}

void solve(torch::Tensor input, torch::Tensor output) {
    const int N = input.size(0);
    const int threads = 256;
    // GPU의 SM 개수를 고려하여 충분한 블록 할당
    const int blocks = std::min((N + threads - 1) / threads, 1024);

    const float* input_ptr = input.data_ptr<float>();
    float* output_ptr = output.data_ptr<float>();

    reduction_kernel_opt<<<blocks, threads>>>(input_ptr, output_ptr, N);
}

PYBIND11_MODULE(TORCH_EXTENSION_NAME, m) {
    m.def("solve", &solve, "Optimized reduction kernel launch");
}
"""

# 커널 파일 저장
with open("kernel.cu", "w") as f:
    f.write(cuda_source)

# 커널 컴파일 및 로드
module = load(
    name="cuda_kernel",
    sources=["kernel.cu"],
    extra_cuda_cflags=["-arch=sm_80"] # 환경에 따라 변경 가능하나 프롬프트 예시 준수 시 -arch=sm_120
)

def run_benchmark():
    # 데이터 설정
    N = 2**26  # 약 6700만 요소
    input_tensor = torch.randn(N, device='cuda', dtype=torch.float32)
    output_tensor = torch.zeros(1, device='cuda', dtype=torch.float32)
    
    # 정확도 검증용 참조값
    expected_sum = torch.sum(input_tensor)
    
    # Warmup
    module.solve(input_tensor, output_tensor)
    torch.cuda.synchronize()
    
    # 시간 측정
    start_event = torch.cuda.Event(enable_timing=True)
    end_event = torch.cuda.Event(enable_timing=True)
    
    output_tensor.zero_()
    
    start_event.record()
    for _ in range(10): # 평균 시간 측정을 위해 반복
        module.solve(input_tensor, output_tensor)
        # atomicAdd를 사용하므로 매번 초기화 필요하나, 
        # 성능 측정을 위해 초기화 없이 누적하거나 루프 외부에서 초기화
    end_event.record()
    
    torch.cuda.synchronize()
    avg_time_ms = start_event.elapsed_time(end_event) / 10.0
    
    # 최종 결과 재계산 (정확도 체크용)
    check_output = torch.zeros(1, device='cuda', dtype=torch.float32)
    module.solve(input_tensor, check_output)
    
    is_accurate = torch.allclose(check_output, expected_sum, rtol=1e-03, atol=1e-03)
    
    # 결과 출력
    result = {
        "is_accurate": bool(is_accurate),
        "execution_time_ms": float(avg_time_ms)
    }
    print(json.dumps(result))

if __name__ == "__main__":
    run_benchmark()