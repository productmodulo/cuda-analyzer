import subprocess
import os
import tempfile
import json
import shutil
import re
from typing import Dict, Any, Optional, List

class DockerExecutor:
    def __init__(self, image: str = "cuda-analyzer-runner"):
        self.image = image

    def extract_kernel_names(self, cuda_code: str) -> List[str]:
        """
        Extracts names of all __global__ kernels from the CUDA source code.
        """
        # Matches __global__ void [name](
        pattern = r"__global__\s+void\s+(\w+)\s*\("
        return re.findall(pattern, cuda_code)

    def run_profiling(self, kernel_code: str, benchmark_code: str) -> Dict[str, Any]:
        """
        Runs the kernel and benchmark in a temporary Docker container and returns the results.
        Uses optimized nsys/ncu options with dynamic kernel detection.
        """
        # Detect kernel names to focus NCU profiling
        kernel_names = self.extract_kernel_names(kernel_code)
        ncu_kernel_filter = ""
        if kernel_names:
            # Join multiple kernels with regex OR for NCU: "kernel1|kernel2"
            ncu_kernel_filter = f"--kernel-name \"regex:{'|'.join(kernel_names)}\""

        with tempfile.TemporaryDirectory() as tmpdir:
            kernel_path = os.path.join(tmpdir, "kernel.cu")
            benchmark_path = os.path.join(tmpdir, "benchmark.py")
            
            with open(kernel_path, "w") as f:
                f.write(kernel_code)
            with open(benchmark_path, "w") as f:
                f.write(benchmark_code)

            # Build Docker command with dynamic kernel filtering
            # nsys: Use standard --stats=true for broad compatibility
            # ncu: Only profile the detected global kernels with core sections
            docker_cmd = [
                "docker", "run", "--rm",
                "--gpus", "all",
                "-v", f"{tmpdir}:/workspace",
                "-w", "/workspace",
                self.image,
                "bash", "-c",
                f"nsys profile --stats=true --force-overwrite=true --output=report_%p python3 benchmark.py && "
                f"ncu {ncu_kernel_filter} --section SpeedOfLight,MemoryWorkload --summary python3 benchmark.py"
            ]

            try:
                result = subprocess.run(
                    docker_cmd,
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                stdout = result.stdout
                stderr = result.stderr
                combined_output = stdout + "\n" + stderr
                
                lines = stdout.splitlines()
                benchmark_result = {"is_accurate": False, "execution_time_ms": 0.0}
                for line in reversed(lines):
                    try:
                        data = json.loads(line)
                        if isinstance(data, dict) and "is_accurate" in data:
                            benchmark_result = data
                            break
                    except:
                        continue
                
                return {
                    "success": True,
                    "stdout": stdout,
                    "stderr": stderr,
                    "nsys_report": self._extract_nsys_summary(combined_output),
                    "ncu_report": self._extract_ncu_summary(combined_output),
                    "is_accurate": benchmark_result.get("is_accurate", False),
                    "execution_time_ms": benchmark_result.get("execution_time_ms", 0.0)
                }

            except subprocess.CalledProcessError as e:
                return {
                    "success": False,
                    "error": e.stderr or str(e),
                    "stdout": e.stdout
                }

    def _extract_nsys_summary(self, output: str) -> str:
        marker = "CUDA Kernel Statistics"
        if marker in output:
            start = output.find(marker)
            return output[start:start+2000].strip()
        return "nsys summary not found."

    def _extract_ncu_summary(self, output: str) -> str:
        # Try to find SOL section
        marker = "Section: GPU Speed Of Light Throughput"
        if marker in output:
            start = output.find(marker)
            return output[start:start+2000].strip()
            
        if "Profiling result:" in output:
            start = output.find("Profiling result:")
            return output[start:start+2000].strip()
            
        return "ncu summary not found."
