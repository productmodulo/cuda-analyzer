from langgraph.graph import StateGraph, END
from agent.state import AgentState, AgentStatus
from agent.nodes import (
    architect_node,
    engineer_node,
    profiling_node,
    critic_node
)

def should_continue(state: AgentState):
    if state.status == AgentStatus.ARCHITECTING:
        return "code_architect"
    else:
        return END

def create_agent_graph():
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("code_architect", architect_node)
    workflow.add_node("benchmark_engineer", engineer_node)
    workflow.add_node("profiling_executor", profiling_node)
    workflow.add_node("optimization_critic", critic_node)

    # Set entry point
    workflow.set_entry_point("code_architect")

    # Linear flow
    workflow.add_edge("code_architect", "benchmark_engineer")
    workflow.add_edge("benchmark_engineer", "profiling_executor")
    workflow.add_edge("profiling_executor", "optimization_critic")
    
    # Conditional loop from critic
    workflow.add_conditional_edges(
        "optimization_critic",
        should_continue,
        {
            "code_architect": "code_architect",
            END: END
        }
    )

    # Compile the graph
    app = workflow.compile()
    
    return app
