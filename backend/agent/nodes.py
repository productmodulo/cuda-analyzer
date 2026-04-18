import json
from typing import Dict, Any, List
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig
from agent.state import AgentState, AgentStatus
from agent.schemas import (
    KernelMetrics,
    VizData
)
from utils.prompts_manager import load_prompt
from utils.logger import log_node_execution
from utils.docker_executor import DockerExecutor
from utils.parser import extract_code_block

MODEL_NANO = "nvidia/nemotron-3-nano-30b-a3b"
MODEL_SUPER = "nvidia/nemotron-3-super-120b-a12b"
DEFAULT_MODEL = MODEL_NANO

def get_llm(model=DEFAULT_MODEL):
    return ChatNVIDIA(
        model=model,
        max_tokens=16384,
        temperature=1.0,
        top_p=0.95,
    )

# --- Initial Phase Nodes ---

@log_node_execution
async def init_copy_node(state: AgentState, config: RunnableConfig) -> Dict[str, Any]:
    llm = get_llm()
    system_prompt = await load_prompt("init_copy_system.md")
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", "Raw Code:\n{raw_cuda_code}\n\nUser Query: {user_query}")
    ])
    
    chain = prompt | llm
    # Use explicit dict for safe template rendering
    response = await chain.ainvoke({
        "raw_cuda_code": state.raw_cuda_code,
        "user_query": state.user_query
    }, config)
    
    original_kernel = extract_code_block(response.content, "cpp")
    if not original_kernel:
        original_kernel = extract_code_block(response.content)
        
    return {
        "original_kernel": original_kernel,
        "status": AgentStatus.INIT_BENCHMARK
    }

@log_node_execution
async def init_benchmark_node(state: AgentState, config: RunnableConfig) -> Dict[str, Any]:
    llm = get_llm()
    system_prompt = await load_prompt("engineer_system.md")
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", "Original Kernel:\n{original_kernel}\n\nUser Query: {user_query}")
    ])
    
    chain = prompt | llm
    response = await chain.ainvoke({
        "original_kernel": state.original_kernel,
        "user_query": state.user_query
    }, config)
    
    benchmark_code = extract_code_block(response.content, "python")
    if not benchmark_code:
        benchmark_code = extract_code_block(response.content)
        
    return {
        "benchmark_code": benchmark_code,
        "status": AgentStatus.INIT_PROFILE
    }

@log_node_execution
async def init_profile_node(state: AgentState, config: RunnableConfig) -> Dict[str, Any]:
    executor = DockerExecutor()
    result = executor.run_profiling(state.original_kernel, state.benchmark_code)
    
    metrics = KernelMetrics(
        nsys_report=result.get("nsys_report"),
        ncu_report=result.get("ncu_report"),
        execution_time_ms=result.get("execution_time_ms", 0.0),
        is_accurate=result.get("is_accurate", False),
        error_log=result.get("error") if not result["success"] else None
    )
    
    return {
        "original_metrics": metrics,
        "best_kernel": state.original_kernel,
        "best_metrics": metrics,
        "status": AgentStatus.ARCHITECTING
    }

# --- Optimization Phase Nodes ---

@log_node_execution
async def architect_node(state: AgentState, config: RunnableConfig) -> Dict[str, Any]:
    llm = get_llm(DEFAULT_MODEL)
    system_prompt = await load_prompt("architect_system.md")
    
    log_str = "\n".join([f"- {l.get('summary', 'N/A')}" for l in state.optimization_log])
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", "User Query: {user_query}\n\nBest Kernel So Far:\n{best_kernel}\n\nBest Metrics:\nnsys: {nsys}\nncu: {ncu}\nTime: {time}ms\n\nOptimization History:\n{history}")
    ])
    
    chain = prompt | llm
    response = await chain.ainvoke({
        "user_query": state.user_query,
        "best_kernel": state.best_kernel,
        "nsys": state.best_metrics.nsys_report if state.best_metrics else "N/A",
        "ncu": state.best_metrics.ncu_report if state.best_metrics else "N/A",
        "time": state.best_metrics.execution_time_ms if state.best_metrics else 0.0,
        "history": log_str if log_str else "No history yet."
    }, config)
    
    current_kernel = extract_code_block(response.content, "cpp")
    if not current_kernel:
        current_kernel = extract_code_block(response.content)
        
    return {
        "current_kernel": current_kernel,
        "status": AgentStatus.PROFILING,
        "iteration": state.iteration + 1
    }

@log_node_execution
async def profile_node(state: AgentState, config: RunnableConfig) -> Dict[str, Any]:
    executor = DockerExecutor()
    result = executor.run_profiling(state.current_kernel, state.benchmark_code)
    
    metrics = KernelMetrics(
        nsys_report=result.get("nsys_report"),
        ncu_report=result.get("ncu_report"),
        execution_time_ms=result.get("execution_time_ms", 0.0),
        is_accurate=result.get("is_accurate", False),
        error_log=result.get("error") if not result["success"] else None
    )
    
    return {
        "current_metrics": metrics,
        "status": AgentStatus.CRITIQUING
    }

@log_node_execution
async def critic_node(state: AgentState, config: RunnableConfig) -> Dict[str, Any]:
    current = state.current_metrics
    best = state.best_metrics
    
    update_best = False
    status_msg = ""
    
    if current.is_accurate:
        if current.execution_time_ms < best.execution_time_ms or best.execution_time_ms == 0:
            update_best = True
            improvement = ((best.execution_time_ms - current.execution_time_ms) / best.execution_time_ms * 100) if best.execution_time_ms > 0 else 0
            status_msg = f"Success: Improved by {improvement:.2f}%"
        else:
            status_msg = f"No Improvement: {current.execution_time_ms:.2f}ms >= {best.execution_time_ms:.2f}ms"
    else:
        status_msg = f"Failed: Accuracy check failed or Error: {current.error_log[:50] if current.error_log else 'Unknown'}"
    
    new_log_entry = {
        "iteration": state.iteration,
        "summary": status_msg,
        "time": current.execution_time_ms
    }
    new_log = state.optimization_log + [new_log_entry]
    
    should_stop = state.iteration >= state.max_iterations
    next_status = AgentStatus.REPORTING if should_stop else AgentStatus.ARCHITECTING
    
    return_data = {
        "optimization_log": new_log,
        "status": next_status
    }
    
    if update_best:
        return_data["best_kernel"] = state.current_kernel
        return_data["best_metrics"] = current
        
    return return_data

# --- Final Phase Nodes ---

@log_node_execution
async def report_node(state: AgentState, config: RunnableConfig) -> Dict[str, Any]:
    llm = get_llm(DEFAULT_MODEL)
    system_prompt = await load_prompt("report_system.md")
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", "User Query: {user_query}\n\nOriginal Kernel:\n{original_kernel}\nOriginal Metrics: {orig_time}ms\n\nBest Kernel:\n{best_kernel}\nBest Metrics: {best_time}ms\n\nOptimization History:\n{history}")
    ])
    
    chain = prompt | llm
    response = await chain.ainvoke({
        "user_query": state.user_query,
        "original_kernel": state.original_kernel,
        "orig_time": state.original_metrics.execution_time_ms if state.original_metrics else 0.0,
        "best_kernel": state.best_kernel,
        "best_time": state.best_metrics.execution_time_ms if state.best_metrics else 0.0,
        "history": json.dumps(state.optimization_log)
    }, config)
    
    final_report = extract_code_block(response.content, "markdown")
    if not final_report:
        final_report = response.content
        
    return {
        "final_report": final_report,
        "status": AgentStatus.VISUALIZING
    }

@log_node_execution
async def visualization_node(state: AgentState, config: RunnableConfig) -> Dict[str, Any]:
    llm = get_llm(DEFAULT_MODEL)
    system_prompt = await load_prompt("visualize_system.md")
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", "Original Metrics: {orig}\nBest Metrics: {best}\nOptimization History: {history}")
    ])
    
    chain = prompt | llm
    response = await chain.ainvoke({
        "orig": state.original_metrics.dict() if state.original_metrics else {},
        "best": state.best_metrics.dict() if state.best_metrics else {},
        "history": json.dumps(state.optimization_log)
    }, config)
    
    component_code = extract_code_block(response.content, "jsx")
    if not component_code:
        component_code = extract_code_block(response.content)

    viz = VizData(
        title=state.user_query,
        original_code=state.original_kernel or "",
        best_code=state.best_kernel or "",
        original_metrics=state.original_metrics.dict() if state.original_metrics else {},
        best_metrics=state.best_metrics.dict() if state.best_metrics else {},
        optimization_log=state.optimization_log,
        final_report=state.final_report or "",
        component_code=component_code
    )
    
    return {
        "viz_data": viz.dict(),
        "status": AgentStatus.COMPLETED
    }
