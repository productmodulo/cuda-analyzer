from langgraph.graph import StateGraph, END
from agent.state import AgentState, AgentStatus
from agent.nodes import (
    init_copy_node,
    init_benchmark_node,
    init_profile_node,
    architect_node,
    profile_node,
    critic_node,
    report_node,
    visualization_node
)

def should_continue(state: AgentState):
    if state.status == AgentStatus.ARCHITECTING:
        return "architect"
    elif state.status == AgentStatus.REPORTING:
        return "report"
    else:
        return "report"

def create_agent_graph():
    workflow = StateGraph(AgentState)

    # 1. Add all nodes
    workflow.add_node("init_copy", init_copy_node)
    workflow.add_node("init_benchmark", init_benchmark_node)
    workflow.add_node("init_profile", init_profile_node)
    
    workflow.add_node("architect", architect_node)
    workflow.add_node("profile", profile_node)
    workflow.add_node("critic", critic_node)
    
    workflow.add_node("report", report_node)
    workflow.add_node("visualize", visualization_node)

    # 2. Define standard edges
    workflow.set_entry_point("init_copy")
    
    workflow.add_edge("init_copy", "init_benchmark")
    workflow.add_edge("init_benchmark", "init_profile")
    workflow.add_edge("init_profile", "architect")
    
    workflow.add_edge("architect", "profile")
    workflow.add_edge("profile", "critic")
    
    # 3. Define conditional routing from critic
    workflow.add_conditional_edges(
        "critic",
        should_continue,
        {
            "architect": "architect",
            "report": "report",
        }
    )
    
    workflow.add_edge("report", "visualize")
    workflow.add_edge("visualize", END)

    # 4. Compile the graph
    app = workflow.compile()
    
    return app
