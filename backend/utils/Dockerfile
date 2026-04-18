# Optimized CUDA Development Environment for RTX 50 Series
FROM nvidia/cuda:13.0.0-devel-ubuntu22.04

# Set environment variables for non-interactive installs and encoding
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONIOENCODING=utf-8

# 1. Install essential build tools and Ninja for parallel compilation
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-dev \
    git \
    ninja-build \
    && apt-get install -y \
    cuda-nsight-systems-13-0 \
    cuda-nsight-compute-13-0 \
    && rm -rf /var/lib/apt/lists/*

# 2. Configure environment paths for NVIDIA tools
ENV PATH="/usr/local/cuda/bin:/opt/nvidia/nsight-systems/bin:${PATH}"

# 3. Install PyTorch with CUDA 13.0 support for sm_120 compatibility
RUN pip3 install --no-cache-dir --upgrade pip && \
    pip3 install --no-cache-dir torch numpy --index-url https://download.pytorch.org/whl/cu130

WORKDIR /workspace

# 컨테이너 실행 시 바로 bash로 진입
CMD ["bash"]
