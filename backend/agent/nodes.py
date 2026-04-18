import json
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.runnables import RunnableConfig
from agent.state import AgentState, AgentStatus
from agent.schemas import (
    KernelCodeOutput, 
    BenchmarkCodeOutput, 
    OptimizationCriticOutput,
    CodeAnalysisResult,
    KernelOptimization
)
from utils.prompts_manager import load_prompt
from utils.logger import log_node_execution
from utils.docker_executor import DockerExecutor

MODEL_NANO = "nvidia/nemotron-3-nano-30b-a3b"
MODEL_SUPER = "nvidia/nemotron-3-super-120b-a12b"

DEFAULT_MODEL = MODEL_NANO

def get_llm(model=DEFAULT_MODEL):
    return ChatNVIDIA(
        model=model,
        max_tokens=8192,
        temperature=1.0,
        top_p=0.95,
    )

@log_node_execution
async def architect_node(state: AgentState, config: RunnableConfig) -> AgentState:
    # First iteration: Just use original code to establish baseline
    if state.iteration_count == 0:
        return {
            "kernel_code": state.original_code,
            "status": AgentStatus.BENCHMARKING,
            "iteration_count": 1
        }

    llm = get_llm()
    parser = PydanticOutputParser(pydantic_object=KernelCodeOutput)
    
    system_prompt = await load_prompt("architect_system.md")
    
    # context for refinement
    critic_suggestion = ""
    if state.analysis_result and state.analysis_result.optimizations:
        last_opt = state.analysis_result.optimizations[-1]
        critic_suggestion = f"Previous Suggestion: {last_opt.optimization_suggestion}"
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", "Original Code:\n{original_code}\n\nUser Question: {user_question}\n\n{suggestion}")
    ])
    
    chain = prompt | llm | parser
    result = await chain.ainvoke({
        "original_code": state.original_code,
        "user_question": state.user_question,
        "suggestion": critic_suggestion,
        "format_instructions": parser.get_format_instructions()
    }, config)
    
    return {
        "kernel_code": result.kernel_code,
        "status": AgentStatus.BENCHMARKING,
        "iteration_count": state.iteration_count + 1
    }

@log_node_execution
async def engineer_node(state: AgentState, config: RunnableConfig) -> AgentState:
    llm = get_llm()
    parser = PydanticOutputParser(pydantic_object=BenchmarkCodeOutput)
    
    system_prompt = await load_prompt("engineer_system.md")
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", "Kernel Code:\n{kernel_code}\n\nUser Question: {user_question}")
    ])
    
    chain = prompt | llm | parser
    result = await chain.ainvoke({
        "kernel_code": state.kernel_code,
        "user_question": state.user_question,
        "format_instructions": parser.get_format_instructions()
    }, config)
    
    return {
        "benchmark_code": result.benchmark_code,
        "status": AgentStatus.PROFILING
    }

@log_node_execution
async def profiling_node(state: AgentState, config: RunnableConfig) -> AgentState:
    executor = DockerExecutor()
    result = executor.run_profiling(state.kernel_code, state.benchmark_code)
    
    if not result["success"]:
        return {
            "error_message": f"Profiling Failed: {result.get('error')}",
            "status": AgentStatus.FAILED
        }
    
    return {
        "nsys_report": result["nsys_report"],
        "ncu_report": result["ncu_report"],
        "is_accurate": result["is_accurate"],
        "execution_time_ms": result["execution_time_ms"],
        "status": AgentStatus.CRITIQUING
    }

@log_node_execution
async def critic_node(state: AgentState, config: RunnableConfig) -> AgentState:
    # If it was the first run (baseline), just save baseline and go back to architecting
    if state.iteration_count == 1 and state.baseline_time_ms is None:
        return {
            "baseline_time_ms": state.execution_time_ms,
            "status": AgentStatus.ARCHITECTING
        }

    llm = get_llm()
    parser = PydanticOutputParser(pydantic_object=OptimizationCriticOutput)
    
    system_prompt = await load_prompt("critic_system.md")
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", "Kernel Code:\n{kernel_code}\n\nnsys Report:\n{nsys_report}\n\nncu Report:\n{ncu_report}\n\nExecution Time: {execution_time_ms}ms\nAccuracy: {is_accurate}")
    ])
    
    chain = prompt | llm | parser
    result = await chain.ainvoke({
        "kernel_code": state.kernel_code,
        "nsys_report": state.nsys_report,
        "ncu_report": state.ncu_report,
        "execution_time_ms": state.execution_time_ms,
        "is_accurate": state.is_accurate,
        "format_instructions": parser.get_format_instructions()
    }, config)
    
    # Update optimizations list in state
    current_opt = KernelOptimization(
        kernel_name="optimized_kernel", # simplified
        bottleneck_analysis=result.analysis,
        optimization_suggestion=result.suggestion or "No further suggestions",
        optimized_code=state.kernel_code
    )
    
    prev_analysis = state.analysis_result
    optimizations = prev_analysis.optimizations if prev_analysis else []
    optimizations.append(current_opt)
    
    new_analysis = CodeAnalysisResult(
        summary=result.analysis if not result.should_refine else "최적화가 진행 중입니다.",
        optimizations=optimizations,
        final_execution_time_ms=state.execution_time_ms
    )
    
    # Decide next status
    next_status = AgentStatus.ARCHITECTING if result.should_refine and state.iteration_count < state.max_iterations else AgentStatus.COMPLETED
    
    return {
        "analysis_result": new_analysis,
        "status": next_status
    }
