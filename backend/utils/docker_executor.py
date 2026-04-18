import subprocess
import os
import tempfile
import json
import shutil
from typing import Dict, Any, Optional

class DockerExecutor:
    def __init__(self, image: str = "nvidia/cuda:12.2.0-devel-ubuntu22.04"):
        self.image = image

    def run_profiling(self, kernel_code: str, benchmark_code: str) -> Dict[str, Any]:
        """
        Runs the kernel and benchmark in a temporary Docker container and returns the results.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Save files to temp directory
            kernel_path = os.path.join(tmpdir, "kernel.cu")
            benchmark_path = os.path.join(tmpdir, "benchmark.py")
            
            with open(kernel_path, "w") as f:
                f.write(kernel_code)
            with open(benchmark_path, "w") as f:
                f.write(benchmark_code)

            # Define Docker command
            # We mount the tmpdir to /workspace in the container
            docker_cmd = [
                "docker", "run", "--rm",
                "--gpus", "all",
                "-v", f"{tmpdir}:/workspace",
                "-w", "/workspace",
                self.image,
                "bash", "-c",
                "apt-get update && apt-get install -y python3-pip && "
                "pip3 install torch numpy && "
                "nsys profile --stats=true --output=report python3 benchmark.py && "
                "ncu --target-processes all --summary python3 benchmark.py"
            ]

            try:
                result = subprocess.run(
                    docker_cmd,
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                # Parse output
                # In a real scenario, we would parse the nsys/ncu output files or stdout
                stdout = result.stdout
                
                # Try to extract JSON from benchmark.py output
                lines = stdout.splitlines()
                benchmark_result = {"is_accurate": False, "execution_time_ms": 0.0}
                for line in reversed(lines):
                    try:
                        benchmark_result = json.loads(line)
                        if "is_accurate" in benchmark_result:
                            break
                    except:
                        continue
                
                return {
                    "success": True,
                    "stdout": stdout,
                    "nsys_report": self._extract_nsys_summary(stdout),
                    "ncu_report": self._extract_ncu_summary(stdout),
                    "is_accurate": benchmark_result.get("is_accurate", False),
                    "execution_time_ms": benchmark_result.get("execution_time_ms", 0.0)
                }

            except subprocess.CalledProcessError as e:
                return {
                    "success": False,
                    "error": e.stderr,
                    "stdout": e.stdout
                }

    def _extract_nsys_summary(self, stdout: str) -> str:
        # Simple extraction logic for demonstration
        if "CUDA Kernel Statistics" in stdout:
            start = stdout.find("CUDA Kernel Statistics")
            return stdout[start:start+1000] # Get first 1000 chars of stats
        return "nsys summary not found."

    def _extract_ncu_summary(self, stdout: str) -> str:
        if "Section: GPU Speed Of Light Throughput" in stdout:
            start = stdout.find("Section: GPU Speed Of Light Throughput")
            return stdout[start:start+1000]
        return "ncu summary not found."
