# 🚀 CUDA-Analyzer: Agentic Optimization Workflow

**Autonomous CUDA Performance Engineering via NVIDIA Nemotron & Nsight Integration**

CUDA-Analyzer is not just a diagnostic tool; it is an **Agentic Workflow** designed to autonomously profile, analyze, and optimize CUDA kernels. By orchestrating **NVIDIA Nsight CLI** and the reasoning power of **Nemotron-4**, it creates a closed-loop optimization cycle that bridges the gap between raw hardware metrics and high-level algorithmic refactoring.

---

## 💡 Key Features
- **Nsight-Driven Multi-Agent Workflow:** Automatically executes `ncu` (Nsight Compute) and `nsys` (Nsight Systems) to extract hardware-level metrics (e.g., SOL, Stall reasons, Bank conflicts).
- **Autonomous Bottleneck Diagnosis:** Agentic reasoning over Nsight reports to pinpoint exact performance inhibitors in the memory hierarchy or warp scheduling.
- **Closed-Loop Refactoring:** LLM-generated optimization based on real-time profiling data, utilizing NVIDIA best practices (CUB, Cutlass, and Tensor Cores).
- **Interactive Memory Sandbox:** Visualizes real-time memory access traces and kernel execution grids in a 3D sandbox (React + Three.js).

## ⚙️ Agentic Workflow
1. **The Profiler (Tool User):** Triggers Nsight CLI to generate detailed performance reports.
2. **The Analyst (Reasoning):** Parses Nsight data to identify stalls and suboptimal memory patterns.
3. **The Architect (Optimization):** Refactors CUDA code and validates performance gains through iterative profiling.

## 🛠 Tech Stack
- **AI/LLM:** NVIDIA NIM (Nemotron-4 340B, Llama-3-70B-Nemotron)
- **Profiling:** NVIDIA Nsight Systems (nsys), NVIDIA Nsight Compute (ncu) CLI
- **Acceleration:** TensorRT-LLM, CUDA Toolkit
- **Frontend:** React, Three.js (3D Memory Visualization)
- **Backend:** FastAPI, Python (Subprocess Orchestration)

---

## 🚧 Project Status: Work in Progress
Active development for **NVIDIA Nemotron Developer Days Seoul 2026**.
- [x] Agentic Architecture Design
- [ ] Nsight CLI Orchestration Module
- [ ] Nemotron Reasoning Pipeline
- [ ] Three.js 3D Memory Mapping
