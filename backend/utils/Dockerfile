FROM nvidia/cuda:12.2.0-devel-ubuntu22.04

# 1. 환경 변수 설정 (인터랙션 방지 및 한글 깨짐 방지)
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONIOENCODING=utf-8

# 2. 필수 도구 및 Nsight 패키지 설치
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-dev \
    git \
    && apt-get install -y \
    cuda-nsight-systems-12-2 \
    cuda-nsight-compute-12-2 \
    && rm -rf /var/lib/apt/lists/*

# 3. Path 설정 (NVIDIA 도구들을 어디서든 실행할 수 있게)
ENV PATH="/usr/local/cuda/bin:/opt/nvidia/nsight-systems/bin:${PATH}"

# 4. PyTorch 설치 (CUDA 12.1/12.2 호환 버전으로 명시)
RUN pip3 install --no-cache-dir --upgrade pip && \
    pip3 install --no-cache-dir torch numpy --index-url https://download.pytorch.org/whl/cu121

WORKDIR /workspace

# 컨테이너 실행 시 바로 bash로 진입
CMD ["bash"]
