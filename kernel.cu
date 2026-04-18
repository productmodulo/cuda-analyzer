
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
